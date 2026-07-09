"""Tests for vector stores (DictVectorStore for CI, Chroma/FAISS if available)."""

import math

import pytest

from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
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


@pytest.fixture
def store():
    return DictVectorStore()


@pytest.mark.asyncio
async def test_upsert_and_search(store):
    embs = [
        ChunkEmbedding(chunk_id="c1", document_id="doc1", embedding=[1.0, 0.0], model="m", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc1", embedding=[0.0, 1.0], model="m", dimensions=2),
        ChunkEmbedding(chunk_id="c3", document_id="doc2", embedding=[1.0, 1.0], model="m", dimensions=2),
    ]
    await store.upsert(embs)
    query = SearchQuery(embedding=[1.0, 0.0], top_k=10)
    result = await store.search(query)
    assert len(result.items) >= 1
    assert result.items[0].chunk.id == "c1"
    assert result.items[0].score == pytest.approx(1.0, abs=1e-6)


@pytest.mark.asyncio
async def test_search_with_document_filter(store):
    embs = [
        ChunkEmbedding(chunk_id="c1", document_id="doc_a", embedding=[1.0, 0.0], model="m", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc_b", embedding=[1.0, 0.0], model="m", dimensions=2),
    ]
    await store.upsert(embs)
    query = SearchQuery(embedding=[1.0, 0.0], document_filter=["doc_a"])
    result = await store.search(query)
    assert len(result.items) == 1
    assert result.items[0].chunk.document_id == "doc_a"


@pytest.mark.asyncio
async def test_search_score_threshold(store):
    embs = [
        ChunkEmbedding(chunk_id="c1", document_id="doc1", embedding=[1.0, 0.0], model="m", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc1", embedding=[0.0, 1.0], model="m", dimensions=2),
    ]
    await store.upsert(embs)
    query = SearchQuery(embedding=[1.0, 0.0], score_threshold=0.99)
    result = await store.search(query)
    assert len(result.items) == 1
    assert result.items[0].chunk.id == "c1"


@pytest.mark.asyncio
async def test_delete_document(store):
    embs = [ChunkEmbedding(chunk_id="c1", document_id="del_doc", embedding=[1.0, 0.0], model="m", dimensions=2)]
    await store.upsert(embs)
    assert await store.count() == 1
    await store.delete("del_doc")
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_delete_chunk(store):
    embs = [
        ChunkEmbedding(chunk_id="c1", document_id="doc", embedding=[1.0, 0.0], model="m", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc", embedding=[0.0, 1.0], model="m", dimensions=2),
    ]
    await store.upsert(embs)
    await store.delete_chunk("c1")
    assert await store.count() == 1


@pytest.mark.asyncio
async def test_count(store):
    assert await store.count() == 0
    embs = [ChunkEmbedding(chunk_id=f"c{i}", document_id="doc", embedding=[1.0, 0.0], model="m", dimensions=2) for i in range(5)]
    await store.upsert(embs)
    assert await store.count() == 5


@pytest.mark.asyncio
async def test_search_empty(store):
    query = SearchQuery(embedding=[1.0, 0.0])
    result = await store.search(query)
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_search_no_embedding(store):
    query = SearchQuery(text="hello")
    result = await store.search(query)
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_chroma_vector_store_import():
    try:
        import chromadb  # noqa: F401
        from knowledge_base.vector.chroma import ChromaVectorStore
        vs = ChromaVectorStore(persist_directory=":memory:")
        assert vs is not None
    except ImportError:
        pytest.skip("chromadb not installed")


@pytest.mark.asyncio
async def test_faiss_vector_store_import():
    try:
        import faiss  # noqa: F401
        from knowledge_base.vector.faiss import FAISSVectorStore
        vs = FAISSVectorStore(persist_directory=":memory:")
        assert vs is not None
    except ImportError:
        pytest.skip("faiss not installed")