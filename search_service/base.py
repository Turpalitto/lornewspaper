"""Abstract provider base.

``BaseProvider`` defines the uniform interface every source implements and a
single ``_fetch`` helper that wires together rate limiting, transient-only
retry, HTTP, structured logging and Pydantic validation. Concrete providers
only implement the query/mapping logic, keeping them small and focused (SRP).

``SearchService`` depends solely on this ABC (DIP) — it never imports a
concrete provider.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel

from search_service.config import ProviderConfig
from search_service.http_client import create_client
from search_service.logging_config import RequestLog, get_logger
from search_service.rate_limit import AsyncRateLimiter
from search_service.retry import TransientHTTPError, async_retry

# Type alias: a mapper turns a validated model (or raw dict) into Article(s).
Mapper = Callable[[Any], "list[Any] | Any"]


class BaseProvider(ABC):
    """Common contract and infrastructure for all literature sources."""

    name: str = "base"
    capabilities: Any = None  # set by subclasses (ProviderCapabilities)

    def __init__(
        self,
        config: ProviderConfig,
        client: httpx.AsyncClient | None = None,
        *,
        max_attempts: int = 4,
        logger: Any | None = None,
    ) -> None:
        self.config = config
        self.name = config.name
        self._client = client or create_client()
        self._limiter = AsyncRateLimiter(rate=config.rate, burst=config.burst)
        self._max_attempts = max_attempts
        self._logger = logger or get_logger()
        self._owns_client = client is None

    # ---- Abstract surface every provider must implement -------------------
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[Any]:
        ...

    @abstractmethod
    async def search_by_date(
        self,
        query: str,
        from_year: int | None = None,
        to_year: int | None = None,
        limit: int = 20,
    ) -> list[Any]:
        ...

    @abstractmethod
    async def search_by_pmid(self, pmid: str) -> Any | None:
        ...

    @abstractmethod
    async def get_metadata(self, identifier: str) -> Any | None:
        ...

    @abstractmethod
    async def get_abstract(self, identifier: str) -> str | None:
        ...

    @abstractmethod
    async def healthcheck(self) -> bool:
        ...

    # ---- Shared request pipeline -----------------------------------------
    async def _request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Single HTTP call wrapped with rate limit + transient retry."""

        url = endpoint if endpoint.startswith("http") else f"{self.config.base_url}{endpoint}"
        to = timeout if timeout is not None else self.config.timeout

        @async_retry(max_attempts=self._max_attempts)
        async def _do() -> httpx.Response:
            await self._limiter.acquire()
            try:
                resp = await self._client.request(
                    method, url, params=params, json=json, timeout=to
                )
            except httpx.HTTPError:
                # Network/timeout errors are transient and re-raised for retry.
                raise
            if resp.status_code == 429:
                retry_after = TransientHTTPError(resp, resp.request).retry_after
                self._limiter.pause(retry_after or max(to, 1.0))
                raise TransientHTTPError(resp, resp.request)
            if resp.status_code >= 500:
                raise TransientHTTPError(resp, resp.request)
            if resp.status_code >= 400:
                # Non-transient client error: surface immediately, no retry.
                resp.raise_for_status()
            return resp

        return await _do()

    async def _fetch(
        self,
        *,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        response_model: type[BaseModel] | None = None,
        map_fn: Callable[[Any], list[Any] | Any],
        query: str = "",
        timeout: float | None = None,
    ) -> list[Any] | Any:
        """Run the full pipeline and map a validated response to Article(s).

        Validates the JSON body against ``response_model`` (when given) before
        mapping, raising on malformed provider payloads. Emits one structured
        log line per call with the resulting article count.
        """
        rl = RequestLog(self.name, endpoint, query, logger=self._logger)
        rl.__enter__()
        try:
            raw = await self._request_raw(
                method, endpoint, params=params, json=json, timeout=timeout
            )
            payload = raw.json()
            if response_model is not None:
                data = response_model.model_validate(payload)
            else:
                data = payload
            result = map_fn(data)
            count = len(result) if isinstance(result, list) else (1 if result else 0)
            rl.result_count = count
        except Exception:
            rl.result_count = 0
            rl.__exit__(*sys.exc_info())
            raise
        else:
            rl.__exit__(None, None, None)
        return result

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
