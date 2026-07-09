"""FAISS vector store backend — in-memory with optional persistence.

All FAISS and numpy calls run in thread pool to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from knowledge_base.exceptions import VectorStoreError
from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
from knowledge_base.vector.base import BaseVectorStore


async def _run(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


class FAISSVectorStore(BaseVectorStore):
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./vector_store",
        distance: str = "cosine",
    ):
        self._name = collection_name
        self._distance = distance
        self._persist = Path(persist_directory)
        self._persist.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._id_to_doc: dict[str, dict[str, Any]] = {}
        self._id_to_embedding: dict[str, list[float]] = {}
        self._dimensions = 0

    async def _ensure(self):
        if self._index is not None:
            return
        import faiss

        index_path = self._persist / f"{self._name}.faiss"
        meta_path = self._persist / f"{self._name}.json"

        if index_path.exists():
            self._index = await _run(faiss.read_index, str(index_path))
            self._dimensions = self._index.d
            if meta_path.exists():
                self._id_to_doc = json.loads(meta_path.read_text())
            return

        self._index = None

    async def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        await self._ensure()
        import faiss

        try:
            await _run(self._upsert_sync, embeddings, faiss)
        except Exception as exc:
            raise VectorStoreError(f"FAISS upsert failed: {exc}") from exc

    def _upsert_sync(self, embeddings: list[ChunkEmbedding], faiss_module) -> None:
        vectors = np.array([e.embedding for e in embeddings], dtype=np.float32)
        ids = np.array([hash(e.chunk_id) for e in embeddings], dtype=np.int64)

        if self._index is None:
            self._dimensions = vectors.shape[1]
            self._index = faiss_module.IndexFlatIP(self._dimensions)

        faiss_module.normalize_L2(vectors)
        self._index.add_with_ids(vectors, ids)

        for e in embeddings:
            self._id_to_doc[e.chunk_id] = {
                "document_id": e.document_id,
                "model": e.model,
            }
            self._id_to_embedding[e.chunk_id] = e.embedding

        self._save_sync()

    async def search(self, query: SearchQuery) -> SearchResult:
        await self._ensure()
        if self._index is None or self._index.ntotal == 0:
            return SearchResult(query=query, items=[], total_found=0)

        import faiss

        try:
            return await _run(self._search_sync, query, faiss)
        except Exception as exc:
            raise VectorStoreError(f"FAISS search failed: {exc}") from exc

    def _search_sync(self, query: SearchQuery, faiss_module) -> SearchResult:
        start = time.perf_counter()
        k = min(query.top_k, self._index.ntotal)

        if query.embedding:
            qvec = np.array([query.embedding], dtype=np.float32)
        elif query.text:
            qvec = np.array([[0.0] * self._dimensions], dtype=np.float32)
        else:
            return SearchResult(query=query, items=[], total_found=0)

        faiss_module.normalize_L2(qvec)
        distances, indices = self._index.search(qvec, k)

        elapsed = (time.perf_counter() - start) * 1000
        items: list[SearchResultItem] = []
        id_to_doc_rev = {v: k for k, v in self._id_to_embedding.items()}

        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            chunk_id = list(self._id_to_doc.keys())[idx] if idx < len(self._id_to_doc) else str(idx)
            # Find chunk_id by reverse lookup
            for cid, emb in self._id_to_embedding.items():
                if np.array_equal(emb, id_to_doc_rev.get(cid, [])):
                    chunk_id = cid
                    break

            score = float(distances[0][i])
            if score < 0:
                score = 0.0
            if score < query.score_threshold:
                continue
            md = self._id_to_doc.get(chunk_id, {})
            items.append(
                SearchResultItem(
                    chunk=Chunk(id=chunk_id, document_id=md.get("document_id", ""), text=""),
                    score=score,
                    document_metadata=md,
                )
            )

        return SearchResult(query=query, items=items, total_found=len(items), elapsed_ms=round(elapsed, 1))

    async def delete(self, document_id: str) -> None:
        await self._ensure()
        if self._index is None:
            return
        import faiss

        try:
            await _run(self._delete_sync, document_id, faiss)
        except Exception as exc:
            raise VectorStoreError(f"FAISS delete failed: {exc}") from exc

    def _delete_sync(self, document_id: str, faiss_module) -> None:
        to_remove = [
            cid for cid, md in self._id_to_doc.items()
            if md.get("document_id") == document_id
        ]
        if not to_remove:
            return

        keep = [(cid, md) for cid, md in self._id_to_doc.items()
                if cid not in to_remove]
        remaining_embeddings = [
            emb for cid, emb in self._id_to_embedding.items()
            if cid not in to_remove
        ]

        if remaining_embeddings:
            vectors = np.array(remaining_embeddings, dtype=np.float32)
            ids = np.array([hash(cid) for cid, _ in keep], dtype=np.int64)
            new_index = faiss_module.IndexFlatIP(self._dimensions)
            faiss_module.normalize_L2(vectors)
            new_index.add_with_ids(vectors, ids)
            self._index = new_index
        else:
            self._index = None

        for cid in to_remove:
            self._id_to_doc.pop(cid, None)
            self._id_to_embedding.pop(cid, None)

        self._save_sync()

    async def delete_chunk(self, chunk_id: str) -> None:
        await self._ensure()
        if self._index is None or chunk_id not in self._id_to_doc:
            return
        import faiss

        try:
            await _run(self._delete_chunk_sync, chunk_id, faiss)
        except Exception as exc:
            raise VectorStoreError(f"FAISS delete chunk failed: {exc}") from exc

    def _delete_chunk_sync(self, chunk_id: str, faiss_module) -> None:
        self._id_to_doc.pop(chunk_id, None)
        self._id_to_embedding.pop(chunk_id, None)

        remaining = list(self._id_to_embedding.items())
        if remaining:
            vectors = np.array([emb for _, emb in remaining], dtype=np.float32)
            ids = np.array([hash(cid) for cid, _ in remaining], dtype=np.int64)
            new_index = faiss_module.IndexFlatIP(self._dimensions)
            faiss_module.normalize_L2(vectors)
            new_index.add_with_ids(vectors, ids)
            self._index = new_index
        else:
            self._index = None

        self._save_sync()

    async def count(self) -> int:
        await self._ensure()
        if self._index is None:
            return 0
        return self._index.ntotal

    async def close(self) -> None:
        if self._persist:
            await _run(self._save_sync)

    def _save_sync(self):
        if self._persist:
            import faiss
            index_path = self._persist / f"{self._name}.faiss"
            meta_path = self._persist / f"{self._name}.json"
            if self._index is not None:
                faiss.write_index(self._index, str(index_path))
            meta_path.write_text(json.dumps(self._id_to_doc))
