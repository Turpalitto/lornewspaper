"""Simple TTL response cache for ResearchAgent."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float


class ResponseCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 512):
        self._ttl = ttl_seconds
        self._max = max_size
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        while len(self._store) >= self._max:
            self._store.popitem(last=False)
        expires_at = time.monotonic() + (ttl or self._ttl)
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)
        self._store.move_to_end(key)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        now = time.monotonic()
        return sum(1 for e in self._store.values() if e.expires_at > now)

    @property
    def size(self) -> int:
        return len(self._store)
