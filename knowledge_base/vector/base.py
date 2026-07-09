"""Abstract vector store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from knowledge_base.models import ChunkEmbedding, SearchQuery, SearchResult


class BaseVectorStore(ABC):
    @abstractmethod
    async def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        ...

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult:
        ...

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        ...

    @abstractmethod
    async def delete_chunk(self, chunk_id: str) -> None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...