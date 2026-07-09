"""Embedding provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    provider_name: str

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0] if results else []

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...