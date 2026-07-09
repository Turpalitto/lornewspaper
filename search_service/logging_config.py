"""Structured logging setup via structlog.

Every provider request emits one structured log line carrying: provider,
endpoint, query, elapsed, retries, status_code, result_count. A contextvars
helper lets the retry/rate-limit layers attach the retry count transparently.
"""

from __future__ import annotations

import contextvars
import logging
import time
from typing import Any

import structlog

_retries: contextvars.ContextVar[int] = contextvars.ContextVar("retries", default=0)


def set_retries(n: int) -> None:
    _retries.set(n)


def get_retries() -> int:
    return _retries.get()


def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    """Configure structlog + stdlib root once.

    Call before any provider runs. ``json_logs`` selects JSON vs console
    rendering (JSON is preferred in production / containers).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]

    if json_logs:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    fmt = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)


def get_logger(name: str = "search_service") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class RequestLog:  # noqa: D101 - small helper, not part of public API
    """Context manager that logs one structured line per provider call."""

    def __init__(
        self,
        provider: str,
        endpoint: str,
        query: str = "",
        *,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        self._log = logger or get_logger()
        self._provider = provider
        self._endpoint = endpoint
        self._query = query
        self._start = 0.0
        self.result_count: int = 0

    def __enter__(self) -> RequestLog:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        elapsed = time.perf_counter() - self._start
        status = getattr(exc, "status_code", None) if exc else None
        result_count = getattr(self, "result_count", 0)
        self._log.info(
            "provider_request",
            provider=self._provider,
            endpoint=self._endpoint,
            query=self._query,
            elapsed_ms=round(elapsed * 1000, 2),
            retries=get_retries(),
            status_code=status,
            result_count=result_count,
            error=exc_type.__name__ if exc_type else None,
        )
        return
