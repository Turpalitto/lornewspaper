"""Transient-only async retry decorator (tenacity).

Retries exclusively on recoverable conditions:
  * network errors (``httpx.RequestError``)
  * timeouts (``httpx.TimeoutException``)
  * HTTP 429 (Too Many Requests)
  * HTTP 5xx (server errors)

Non-transient 4xx (e.g. 400, 401, 403, 404) are NOT retried. When the server
supplies ``Retry-After`` it is honoured before the exponential backoff.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import tenacity
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter


class TransientHTTPError(httpx.HTTPStatusError):
    """HTTPStatusError wrapper for retryable statuses (429 / 5xx)."""

    def __init__(self, response: httpx.Response, request: httpx.Request) -> None:
        super().__init__(
            message=f"Transient HTTP {response.status_code}",
            request=request,
            response=response,
        )
        self.retry_after: float | None = _parse_retry_after(response)


def _parse_retry_after(response: httpx.Response) -> float | None:
    """Return Retry-After as seconds, or None.

    Supports both the delta-seconds form and the HTTP-date form.
    """
    value = response.headers.get("Retry-After")
    if not value:
        return None
    value = value.strip()
    try:
        return float(value)
    except ValueError:
        pass
    # HTTP-date form
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            return None
        delta = (dt - dt.now(dt.tzinfo)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError):
        return None


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, TransientHTTPError):
        return True
    return False


def _wait_with_retry_after(retry_state: tenacity.RetryCallState) -> float:
    """Exponential jittered backoff, but immediately obey Retry-After if present."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(exc, TransientHTTPError) and exc.retry_after is not None:
        return float(exc.retry_after)
    # exponential backoff with jitter: base 0.5s, cap 15s
    return wait_exponential_jitter(initial=0.5, max=15)(retry_state)


def async_retry(
    *,
    max_attempts: int = 4,
    sleep: Callable[[float], Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator applying transient-only retry with Retry-After support.

    ``sleep`` is injectable for tests; defaults to ``asyncio.sleep``.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        retrying = AsyncRetrying(
            retry=retry_if_exception(_is_transient),
            stop=stop_after_attempt(max_attempts),
            wait=_wait_with_retry_after,
            sleep=sleep or _async_sleep,
            reraise=True,
            before_sleep=_count_retry,
        )

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retrying(fn, *args, **kwargs)

        return wrapper

    return decorator


async def _async_sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def _count_retry(retry_state: tenacity.RetryCallState) -> None:
    from search_service.logging_config import set_retries

    set_retries(retry_state.attempt_number)
