"""Tests for indexing pipeline."""

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
from knowledge_base.indexing import IndexingService
from knowledge_base.models import Chunk, ChunkEmbedding, IndexingStatus, SearchQuery, SearchResult, SearchResultItem
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


class MockEmbedder(BaseEmbeddingProvider):
    provider_name = "mock"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    @property
    def dimensions(self) -> int:
        return 3

    @property
    def model_name(self) -> str:
        return "mock-v1"


@pytest.fixture
def settings():
    s = Settings()
    s.storage.database_path = ":memory:"
    s.chunking.strategy = "section"
    return s


@pytest.fixture
def storage():
    return SQLiteStorage(database_path=":memory:")


@pytest.fixture
def vector_store():
    return DictVectorStore()


@pytest.fixture
def embedding():
    return MockEmbedder()


def make_processed(article_id: str = "test_article") -> ProcessedDocument:
    return ProcessedDocument(
        article_id=article_id,
        source_file="/tmp/test.pdf",
        status=ProcessingStatus.COMPLETED,
        metadata=DocumentMetadata(title="Test Paper", abstract="A test paper for indexing."),
        sections=[
            ExtractedSection(heading="Introduction", content="This is the introduction section of the paper with enough length.", level=1),
            ExtractedSection(heading="Methods", content="We conducted experiments with sufficient detail for chunking.", level=1),
        ],
        stats=ExtractionStats(total_pages=5, total_characters=200),
        raw_text="Introduction\nThis is the introduction section of the paper with enough length.\nMethods\nWe conducted experiments with sufficient detail for chunking.",
    )


@pytest.mark.asyncio
async def test_index_completes(settings, storage, vector_store, embedding):
    svc = IndexingService(settings, storage, vector_store, embedding)
    processed = make_processed()
    doc = await svc.index(processed)
    assert doc.status == IndexingStatus.COMPLETED
    assert doc.document_id == "test_article"
    assert len(doc.chunks) == 2
    assert doc.statistics.total_chunks == 2
    assert doc.statistics.embedding_model == "mock-v1"

    loaded = await storage.get_document("test_article")
    assert loaded is not None
    assert loaded.status == IndexingStatus.COMPLETED
    chunks = await storage.get_chunks("test_article")
    assert len(chunks) == 2
    embs = await storage.get_embeddings("test_article")
    assert len(embs) == 2
    assert await vector_store.count() == 2


@pytest.mark.asyncio
async def test_index_failed_on_exception(settings, storage, vector_store, embedding):
    svc = IndexingService(settings, storage, vector_store, embedding)
    processed = make_processed()
    original_chunk = svc._chunker.chunk
    svc._chunker.chunk = lambda *a, **kw: (_ for _ in ()).throw(ValueError("chunk failed"))
    doc = await svc.index(processed)
    assert doc.status == IndexingStatus.FAILED
    assert "error" in doc.metadata
    svc._chunker.chunk = original_chunk


@pytest.mark.asyncio
async def test_index_stores_metadata(settings, storage, vector_store, embedding):
    svc = IndexingService(settings, storage, vector_store, embedding)
    processed = make_processed()
    doc = await svc.index(processed)
    assert doc.metadata.get("title") == "Test Paper"
    assert doc.metadata.get("abstract") == "A test paper for indexing."
    assert doc.metadata.get("total_pages") == 5


@pytest.mark.asyncio
async def test_index_sentence_strategy(settings, storage, vector_store, embedding):
    settings.chunking.strategy = "sentence"
    svc = IndexingService(settings, storage, vector_store, embedding)
    processed = make_processed()
    doc = await svc.index(processed)
    assert doc.status == IndexingStatus.COMPLETED
    assert doc.statistics.chunking_strategy == "sentence"


@pytest.mark.asyncio
async def test_index_fixed_strategy(settings, storage, vector_store, embedding):
    settings.chunking.strategy = "fixed"
    settings.chunking.chunk_size = 10
    settings.chunking.chunk_overlap = 2
    settings.chunking.min_chunk_length = 1
    svc = IndexingService(settings, storage, vector_store, embedding)
    processed = make_processed()
    doc = await svc.index(processed)
    assert doc.status == IndexingStatus.COMPLETED
    assert doc.statistics.chunking_strategy == "fixed"