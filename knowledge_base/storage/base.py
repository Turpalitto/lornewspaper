"""Abstract storage backend."""

from __future__ import annotations

from abc import ABC, abstractmethod

from knowledge_base.models import Chunk, ChunkEmbedding, KnowledgeDocument


class BaseStorage(ABC):
    @abstractmethod
    async def save_document(self, doc: KnowledgeDocument) -> None:
        ...

    @abstractmethod
    async def get_document(self, document_id: str) -> KnowledgeDocument | None:
        ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        ...

    @abstractmethod
    async def list_documents(self) -> list[KnowledgeDocument]:
        ...

    @abstractmethod
    async def save_chunks(self, chunks: list[Chunk]) -> None:
        ...

    @abstractmethod
    async def get_chunks(self, document_id: str) -> list[Chunk]:
        ...

    @abstractmethod
    async def save_embeddings(self, embeddings: list[ChunkEmbedding]) -> None:
        ...

    @abstractmethod
    async def get_embeddings(self, document_id: str) -> list[ChunkEmbedding]:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...