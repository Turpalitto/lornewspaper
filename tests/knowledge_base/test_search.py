"""Tests for search service."""

import math

import pytest

from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
from knowledge_base.search import SearchService
from knowledge_base.storage.sqlite import SQLiteStorage
from knowledge_base.vector.base import BaseVectorStore


class DictVectorStore(BaseVectorStore):
    def __init__(self):
        self._vectors: dict[str, list[float]] = {}
        self._metadatas: dict[str, dict] = {}

    async def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        for e in embeddings:
            self._vectors[e.chunk_id] = e.embedding
            self._metadatas[e.chunk_id] = {"document_id": e.document_id, "model": e.model}

    async def search(self, query: SearchQuery) -> SearchResult:
        if not query.embedding:
            return SearchResult(query=query, items=[])
        q = query.embedding
        scores: list[tuple[str, float]] = []
        for cid, vec in self._vectors.items():
            if query.document_filter:
                md = self._metadatas.get(cid, {})
                if md.get("document_id") not in query.document_filter:
                    continue
            score = _cosine_sim(q, vec)
            if score >= query.score_threshold:
                scores.append((cid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        scores = scores[:query.top_k]
        items = [
            SearchResultItem(
                chunk=Chunk(id=cid, document_id=self._metadatas.get(cid, {}).get("document_id", ""), text=""),
                score=score,
                document_metadata=self._metadatas.get(cid, {}),
            )
            for cid, score in scores
        ]
        return SearchResult(query=query, items=items, total_found=len(items))

    async def delete(self, document_id: str) -> None:
        to_remove = [cid for cid, md in self._metadatas.items() if md.get("document_id") == document_id]
        for cid in to_remove:
            self._vectors.pop(cid, None)
            self._metadatas.pop(cid, None)

    async def delete_chunk(self, chunk_id: str) -> None:
        self._vectors.pop(chunk_id, None)
        self._metadatas.pop(chunk_id, None)

    async def count(self) -> int:
        return len(self._vectors)

    async def close(self) -> None:
        pass


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class FixedEmbedder(BaseEmbeddingProvider):
    provider_name = "fixed"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.5, 0.5] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.5, 0.5]

    @property
    def dimensions(self) -> int:
        return 2

    @property
    def model_name(self) -> str:
        return "fixed"


@pytest.fixture
def svc():
    storage = SQLiteStorage(database_path=":memory:")
    vector = DictVectorStore()
    embedder = FixedEmbedder()
    return SearchService(vector_store=vector, storage=storage, embedding_provider=embedder)


@pytest.mark.asyncio
async def test_search_by_text(svc):
    await svc._vector.upsert([
        ChunkEmbedding(chunk_id="c1", document_id="doc1", embedding=[0.5, 0.5], model="fixed", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc1", embedding=[0.1, 0.9], model="fixed", dimensions=2),
    ])
    result = await svc.search_by_text("test query", top_k=10)
    assert isinstance(result, SearchResult)
    assert len(result.items) >= 1


@pytest.mark.asyncio
async def test_search_returns_results(svc):
    await svc._vector.upsert([
        ChunkEmbedding(chunk_id="c1", document_id="doc1", embedding=[0.5, 0.5], model="fixed", dimensions=2),
    ])
    result = await svc.search(SearchQuery(text="hello", top_k=10))
    assert len(result.items) == 1
    assert result.items[0].score > 0


@pytest.mark.asyncio
async def test_search_empty(svc):
    result = await svc.search(SearchQuery(text="nothing", top_k=10))
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_search_with_document_filter(svc):
    await svc._vector.upsert([
        ChunkEmbedding(chunk_id="c1", document_id="doc_a", embedding=[0.5, 0.5], model="fixed", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc_b", embedding=[0.5, 0.5], model="fixed", dimensions=2),
    ])
    result = await svc.search_by_text("test", document_filter=["doc_a"])
    assert len(result.items) == 1
    assert result.items[0].chunk.document_id == "doc_a"


@pytest.mark.asyncio
async def test_search_elapsed_set(svc):
    result = await svc.search(SearchQuery(text="hi", top_k=10))
    assert isinstance(result.elapsed_ms, (int, float))
    assert result.elapsed_ms >= 0