"""KnowledgeBaseService orchestrator — index, search, manage."""

from __future__ import annotations

from typing import Any

import structlog

from knowledge_base.config import Settings, default_settings
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.embedding.registry import get_embedding_provider
from knowledge_base.indexing import IndexingService
from knowledge_base.models import KnowledgeDocument, SearchQuery, SearchResult
from knowledge_base.search import SearchService
from knowledge_base.storage.base import BaseStorage
from knowledge_base.storage.sqlite import SQLiteStorage
from knowledge_base.vector.base import BaseVectorStore
from knowledge_base.vector.chroma import ChromaVectorStore
from document_processing_service.models import ProcessedDocument

_LOG = structlog.get_logger("knowledge_base")


class KnowledgeBaseService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        storage: BaseStorage | None = None,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
    ):
        self._settings = settings or default_settings()
        self._storage = storage or SQLiteStorage(database_path=self._settings.storage.database_path)
        self._vector_store = vector_store or ChromaVectorStore(
            collection_name=self._settings.vector.collection_name,
            persist_directory=self._settings.vector.persist_directory,
            distance=self._settings.vector.distance,
        )
        self._embedding = embedding_provider or get_embedding_provider(self._settings.embedding)
        self._indexing = IndexingService(
            settings=self._settings,
            storage=self._storage,
            vector_store=self._vector_store,
            embedding_provider=self._embedding,
        )
        self._search = SearchService(
            vector_store=self._vector_store,
            storage=self._storage,
            embedding_provider=self._embedding,
        )

    # ---- Indexing ----------------------------------------------------------
    async def index(self, processed_doc: ProcessedDocument) -> KnowledgeDocument:
        return await self._indexing.index(processed_doc)

    # ---- Search ------------------------------------------------------------
    async def search(self, query: SearchQuery) -> SearchResult:
        return await self._search.search(query)

    async def search_text(
        self,
        text: str,
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
        section_filter: str | None = None,
        document_filter: list[str] | None = None,
        score_threshold: float = 0.0,
    ) -> SearchResult:
        return await self._search.search_by_text(
            text=text,
            top_k=top_k,
            metadata_filter=metadata_filter,
            section_filter=section_filter,
            document_filter=document_filter,
            score_threshold=score_threshold,
        )

    # ---- Document management -----------------------------------------------
    async def get_document(self, document_id: str) -> KnowledgeDocument | None:
        return await self._storage.get_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        await self._vector_store.delete(document_id)
        return await self._storage.delete_document(document_id)

    async def list_documents(self) -> list[KnowledgeDocument]:
        return await self._storage.list_documents()

    async def get_chunks(self, document_id: str) -> list:
        from knowledge_base.models import Chunk
        return await self._storage.get_chunks(document_id)

    # ---- Lifecycle ---------------------------------------------------------
    async def close(self) -> None:
        await self._storage.close()
        await self._vector_store.close()

    async def __aenter__(self) -> KnowledgeBaseService:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()