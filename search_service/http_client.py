"""Shared httpx.AsyncClient with connection pooling, keep-alive, timeouts and a
proper User-Agent.

A single client instance is reused across all providers (one connection pool)
to honour keep-alive and bound resource usage. ``SearchService`` owns the
client lifecycle; ``create_client`` builds it from :class:`Settings`.
"""

from __future__ import annotations

import httpx

from search_service.config import Settings


def create_client(settings: Settings | None = None) -> httpx.AsyncClient:
    """Build a pooled AsyncClient from settings.

    Sets default timeout and a descriptive User-Agent required by several
    literature APIs (OpenAlex politeness, Europe PMC contact).
    """
    settings = settings or _default()
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=settings.concurrency_limit * 2,
            max_keepalive_connections=settings.concurrency_limit,
            keepalive_expiry=30.0,
        ),
    )


def _default() -> Settings:
    from search_service.config import default_settings

    return default_settings()
