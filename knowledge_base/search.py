"""Search service — hybrid retrieval across vector + metadata."""

from __future__ import annotations

import time
from typing import Any

import structlog

from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.models import SearchQuery, SearchResult
from knowledge_base.storage.base import BaseStorage
from knowledge_base.vector.base import BaseVectorStore

_LOG = structlog.get_logger("knowledge_base")


class SearchService:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        storage: BaseStorage,
        embedding_provider: BaseEmbeddingProvider,
    ):
        self._vector = vector_store
        self._storage = storage
        self._embedding = embedding_provider

    async def search(self, query: SearchQuery) -> SearchResult:
        start = time.perf_counter()

        if not query.embedding and query.text:
            query.embedding = await self._embedding.embed_query(query.text)

        result = await self._vector.search(query)

        # Enrich result items with full chunk text from storage
        for item in result.items:
            if not item.chunk.text:
                chunks = await self._storage.get_chunks(item.chunk.document_id)
                for c in chunks:
                    if c.id == item.chunk.id:
                        item.chunk = c
                        break

        result.elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return result

    async def search_by_text(
        self,
        text: str,
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
        section_filter: str | None = None,
        document_filter: list[str] | None = None,
        score_threshold: float = 0.0,
    ) -> SearchResult:
        query = SearchQuery(
            text=text,
            top_k=top_k,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter or {},
            section_filter=section_filter,
            document_filter=document_filter or [],
        )
        return await self.search(query)