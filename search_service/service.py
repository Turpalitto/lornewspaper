"""SearchService orchestrator.

Depends only on the :class:`BaseProvider` ABC (DIP). It fans queries out to all
enabled providers concurrently (bounded by a semaphore), isolates provider
failures so one broken source never sinks the whole search, then deduplicates
and merges the combined results.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

import httpx
import structlog

from search_service.base import BaseProvider
from search_service.config import Settings, default_settings
from search_service.dedupe import deduplicate
from search_service.exceptions import UnknownProviderError
from search_service.http_client import create_client
from search_service.logging_config import get_logger
from search_service.providers import get_provider


class SearchService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        providers: Iterable[BaseProvider] | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        self.settings = settings or default_settings()
        self._client = client or create_client(self.settings)
        self._logger = logger or get_logger()
        self._sem = asyncio.Semaphore(self.settings.concurrency_limit)
        self._providers: dict[str, BaseProvider] = {}

        if providers is not None:
            # Explicit provider set given (tests / custom wiring): use only these.
            for provider in providers:
                self._providers[provider.name] = provider
        else:
            for name, cfg in self.settings.providers.items():
                if cfg.enabled:
                    self._providers[name] = get_provider(name, cfg, self._client)

    @property
    def providers(self) -> list[str]:
        return list(self._providers)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def __aenter__(self) -> SearchService:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # -- public API --------------------------------------------------------
    async def search_all(
        self,
        query: str,
        limit: int = 20,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list:
        date_scoped = from_year is not None or to_year is not None

        async def _task(p: BaseProvider):
            if date_scoped:
                if p.capabilities.supports_date:
                    return await p.search_by_date(query, from_year, to_year, limit)
                return []
            if p.capabilities.supports_search:
                return await p.search(query, limit)
            return []

        results = await self._gather(_task)
        return deduplicate(a for sub in results if sub for a in sub)

    async def search_by_provider(
        self,
        query: str,
        provider_name: str,
        limit: int = 20,
        from_year: int | None = None,
        to_year: int | None = None,
    ) -> list:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise UnknownProviderError(f"Unknown or disabled provider: {provider_name}")
        if from_year is not None or to_year is not None:
            articles = await provider.search_by_date(query, from_year, to_year, limit)
        else:
            articles = await provider.search(query, limit)
        return deduplicate(articles)

    async def search_by_date(
        self,
        query: str,
        from_year: int | None,
        to_year: int | None,
        limit: int = 20,
    ) -> list:
        return await self.search_all(query, limit, from_year, to_year)

    async def search_by_pmid(self, pmid: str) -> list:
        async def _task(p: BaseProvider):
            if p.capabilities.supports_pmid:
                return await p.search_by_pmid(pmid)
            return None

        results = await self._gather(_task)
        return deduplicate(r for r in results if r is not None)

    # -- internals ---------------------------------------------------------
    async def _gather(self, task_fn) -> list:
        """Run ``task_fn`` for every provider under the concurrency semaphore,
        isolating per-provider failures."""
        tasks = [
            self._guarded(task_fn, provider) for provider in self._providers.values()
        ]
        return await asyncio.gather(*tasks)

    async def _guarded(self, task_fn, provider: BaseProvider):
        async with self._sem:
            try:
                return await task_fn(provider)
            except Exception as exc:  # noqa: BLE001 - resilience by design
                self._logger.error(
                    "provider_failed",
                    provider=provider.name,
                    error=type(exc).__name__,
                )
                return None
