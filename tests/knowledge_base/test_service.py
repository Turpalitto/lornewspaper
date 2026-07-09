"""Integration tests for KnowledgeBaseService orchestrator."""

import math

import pytest

from document_processing_service.models import (
    DocumentMetadata,
    ExtractedSection,
    ExtractionStats,
    ProcessedDocument,
    ProcessingStatus,
)
from knowledge_base.config import Settings
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.models import IndexingStatus, SearchQuery
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.storage.sqlite import SQLiteStorage
from knowledge_base.vector.base import BaseVectorStore
from knowledge_base.models import Chunk, ChunkEmbedding, SearchResult, SearchResultItem


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


class MockEmbedder(BaseEmbeddingProvider):
    provider_name = "mock"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 100) / 100.0 for _ in range(4)] for t in texts]

    @property
    def dimensions(self) -> int:
        return 4

    @property
    def model_name(self) -> str:
        return "mock-v2"


def make_doc(article_id: str = "integ_test") -> ProcessedDocument:
    return ProcessedDocument(
        article_id=article_id,
        source_file="/tmp/test.pdf",
        status=ProcessingStatus.COMPLETED,
        metadata=DocumentMetadata(title="Integration Test", abstract="Abstract here.", authors=["Alice"]),
        sections=[
            ExtractedSection(heading="Intro", content="This is the introduction text with enough length for chunking.", level=1),
            ExtractedSection(heading="Results", content="These are the detailed results of the experiment.", level=1),
        ],
        stats=ExtractionStats(total_pages=3, total_characters=100),
        raw_text="Intro\nThis is the introduction text with enough length for chunking.\nResults\nThese are the detailed results of the experiment.",
    )


@pytest.fixture
def kb():
    s = Settings()
    s.storage.database_path = ":memory:"
    kb = KnowledgeBaseService(
        settings=s,
        storage=SQLiteStorage(database_path=":memory:"),
        vector_store=DictVectorStore(),
        embedding_provider=MockEmbedder(),
    )
    return kb


@pytest.mark.asyncio
async def test_index_and_retrieve(kb):
    doc = make_doc()
    result = await kb.index(doc)
    assert result.status == IndexingStatus.COMPLETED
    assert result.document_id == "integ_test"

    loaded = await kb.get_document("integ_test")
    assert loaded is not None
    assert loaded.statistics.total_chunks == 2


@pytest.mark.asyncio
async def test_search_after_index(kb):
    await kb.index(make_doc("search_test"))
    results = await kb.search_text("introduction text with enough length", top_k=10)
    assert len(results.items) >= 1
    assert results.total_found >= 1


@pytest.mark.asyncio
async def test_delete_document(kb):
    await kb.index(make_doc("to_delete"))
    assert await kb.get_document("to_delete") is not None
    deleted = await kb.delete_document("to_delete")
    assert deleted is True
    assert await kb.get_document("to_delete") is None


@pytest.mark.asyncio
async def test_list_documents(kb):
    await kb.index(make_doc("list_a"))
    await kb.index(make_doc("list_b"))
    docs = await kb.list_documents()
    assert len(docs) >= 2


@pytest.mark.asyncio
async def test_get_chunks(kb):
    await kb.index(make_doc("chunks_test"))
    chunks = await kb.get_chunks("chunks_test")
    assert len(chunks) == 2
    assert chunks[0].heading == "Intro"
    assert chunks[1].heading == "Results"


@pytest.mark.asyncio
async def test_search_with_query_object(kb):
    await kb.index(make_doc("query_obj_test"))
    query = SearchQuery(text="detailed results of the experiment", top_k=5)
    result = await kb.search(query)
    assert result.total_found >= 1


@pytest.mark.asyncio
async def test_search_no_results(kb):
    results = await kb.search_text("nonexistent garbage text")
    assert len(results.items) == 0


@pytest.mark.asyncio
async def test_async_context_manager():
    s = Settings()
    s.storage.database_path = ":memory:"
    async with KnowledgeBaseService(
        settings=s,
        storage=SQLiteStorage(database_path=":memory:"),
        vector_store=DictVectorStore(),
        embedding_provider=MockEmbedder(),
    ) as kb:
        await kb.index(make_doc("ctx_test"))
        doc = await kb.get_document("ctx_test")
    assert doc is not None


@pytest.mark.asyncio
async def test_document_metadata_preserved(kb):
    doc = make_doc("meta_test")
    await kb.index(doc)
    loaded = await kb.get_document("meta_test")
    assert loaded.metadata.get("title") == "Integration Test"
    assert loaded.metadata.get("abstract") == "Abstract here."