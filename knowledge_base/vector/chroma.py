"""ChromaDB vector store backend."""

from __future__ import annotations

import asyncio
from typing import Any

from knowledge_base.exceptions import VectorStoreError
from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
from knowledge_base.vector.base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./vector_store",
        distance: str = "cosine",
    ):
        self._collection_name = collection_name
        self._persist_dir = persist_directory
        self._distance = distance
        self._collection = None
        self._client = None

    async def _ensure(self):
        if self._collection is None:
            import chromadb
            loop = asyncio.get_running_loop()
            self._client = await loop.run_in_executor(
                None, lambda: chromadb.PersistentClient(path=self._persist_dir)
            )
            self._collection = await loop.run_in_executor(
                None,
                lambda: self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": self._distance},
                ),
            )

    async def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        await self._ensure()
        try:
            ids = [e.chunk_id for e in embeddings]
            vectors = [e.embedding for e in embeddings]
            metadatas: list[dict[str, Any]] = [
                {"document_id": e.document_id, "model": e.model, "dimensions": e.dimensions}
                for e in embeddings
            ]
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.upsert(ids=ids, embeddings=vectors, metadatas=metadatas),
            )
        except Exception as exc:
            raise VectorStoreError(f"Chroma upsert failed: {exc}") from exc

    async def search(self, query: SearchQuery) -> SearchResult:
        await self._ensure()
        import time
        start = time.perf_counter()
        try:
            where: dict | None = None
            if query.document_filter:
                where = {"document_id": {"$in": query.document_filter}}
            if query.metadata_filter:
                where = {**where, **query.metadata_filter} if where else query.metadata_filter

            loop = asyncio.get_running_loop()
            raw = await loop.run_in_executor(
                None,
                lambda: self._collection.query(
                    query_embeddings=[query.embedding] if query.embedding else None,
                    query_texts=[query.text] if query.text else None,
                    n_results=query.top_k,
                    where=where,
                ),
            )
            elapsed = (time.perf_counter() - start) * 1000
            items: list[SearchResultItem] = []
            ids = raw.get("ids", [[]])[0]
            distances = raw.get("distances", [[]])[0]
            metadatas = raw.get("metadatas", [[]])[0]

            for i, cid in enumerate(ids):
                score = 1.0 / (1.0 + distances[i]) if distances else 0.0
                if score < query.score_threshold:
                    continue
                md = metadatas[i] if metadatas else {}
                items.append(
                    SearchResultItem(
                        chunk=Chunk(id=cid, document_id=md.get("document_id", ""), text=""),
                        score=score,
                        document_metadata=md,
                    )
                )
            return SearchResult(query=query, items=items, total_found=len(items), elapsed_ms=round(elapsed, 1))
        except Exception as exc:
            raise VectorStoreError(f"Chroma search failed: {exc}") from exc

    async def delete(self, document_id: str) -> None:
        await self._ensure()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.delete(where={"document_id": document_id}),
            )
        except Exception as exc:
            raise VectorStoreError(f"Chroma delete failed: {exc}") from exc

    async def delete_chunk(self, chunk_id: str) -> None:
        await self._ensure()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.delete(ids=[chunk_id]),
            )
        except Exception as exc:
            raise VectorStoreError(f"Chroma delete chunk failed: {exc}") from exc

    async def count(self) -> int:
        await self._ensure()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._collection.count())

    async def close(self) -> None:
        pass
