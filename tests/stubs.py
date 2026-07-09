"""Shared test doubles for SearchService tests."""

import asyncio
from typing import Any

from search_service.base import BaseProvider
from search_service.config import ProviderCapabilities, ProviderConfig


class ConcurrencyCounter:
    def __init__(self) -> None:
        self.current = 0
        self.max = 0

    async def track(self, delay: float) -> None:
        self.current += 1
        self.max = max(self.max, self.current)
        if delay:
            await asyncio.sleep(delay)
        self.current -= 1


class StubProvider(BaseProvider):
    name = "stub"
    capabilities = ProviderCapabilities()

    def __init__(
        self,
        results: Any | None = None,
        *,
        fail: bool = False,
        delay: float = 0.0,
        counter: ConcurrencyCounter | None = None,
        name: str = "stub",
    ) -> None:
        cfg = ProviderConfig(name=name, rate=1000.0, burst=1000)
        super().__init__(cfg)
        self.name = name
        self._results = results if results is not None else []
        self.fail = fail
        self.delay = delay
        self.counter = counter
        self.call_count = 0

    async def _respond(self, value: Any) -> Any:
        self.call_count += 1
        if self.counter is not None:
            await self.counter.track(self.delay)
        if self.fail:
            raise RuntimeError(f"{self.name} failed")
        return value

    async def search(self, query: str, limit: int = 20) -> list:
        return await self._respond(self._results)

    async def search_by_date(self, query, from_year=None, to_year=None, limit=20) -> list:
        return await self._respond(self._results)

    async def search_by_pmid(self, pmid: str):
        return await self._respond(self._results[0] if self._results else None)

    async def get_metadata(self, identifier: str):
        return await self._respond(self._results[0] if self._results else None)

    async def get_abstract(self, identifier: str):
        art = self._results[0] if self._results else None
        return art.abstract if art else None

    async def healthcheck(self) -> bool:
        return not self.fail
