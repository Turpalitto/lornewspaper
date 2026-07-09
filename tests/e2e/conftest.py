"""Shared fixtures for end-to-end pipeline tests."""

from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

from document_processing_service.models import (
    DocumentMetadata,
    ExtractedSection,
    ExtractionStats,
    ProcessedDocument,
    ProcessingStatus,
)
from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from knowledge_base.config import Settings as KBSettings
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.storage.sqlite import SQLiteStorage
from knowledge_base.vector.base import BaseVectorStore
from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings as AgentSettings
from search_service.models import Article


def _make_pdf_bytes() -> bytes:
    """Generate a minimal valid PDF with 'Test Article PDF' text on page 1."""
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R"
        b" /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        b"4 0 obj\n<< /Length 70 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Test Article PDF) Tj ET\n"
        b"endstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    header = b"%PDF-1.4\n"
    body = b""
    offsets = []
    for obj in objects:
        offsets.append(len(header) + len(body))
        body += obj
    xref_offset = len(header) + len(body)
    xref = b"xref\n"
    xref += f"0 {len(objects) + 1}\n".encode()
    xref += b"0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = b"trailer\n<< /Size " + str(len(objects) + 1).encode()
    trailer += b" /Root 1 0 R >>\n"
    trailer += b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF\n"
    return header + body + xref + trailer


@pytest.fixture(scope="session")
def sample_pdf_path() -> str:
    """Create a minimal valid PDF for processing tests."""
    path = os.path.join(tempfile.gettempdir(), "lornews_e2e_test.pdf")
    Path(path).write_bytes(_make_pdf_bytes())
    return path


@pytest.fixture(scope="session")
def sample_article() -> Article:
    return Article(
        id="e2e-test-001",
        title="Test Article for E2E Pipeline",
        doi="10.1234/e2e.test.001",
        pmid="12345678",
        pmcid="PMC12345678",
        authors=["Alice Researcher", "Bob Scientist"],
        year=2024,
        journal="Journal of Integration Testing",
        abstract="This is a test article used for end-to-end pipeline validation.",
        source="pubmed",
        keywords=["e2e", "testing", "pipeline"],
        provenance=["pubmed", "europepmc"],
    )


@pytest.fixture
def mock_search_results(sample_article) -> list[Article]:
    return [sample_article]


@pytest.fixture
def download_result(sample_article, sample_pdf_path) -> DownloadResult:
    return DownloadResult(
        article_id=sample_article.id,
        source=sample_article.source,
        download_type="pdf",
        status=DownloadStatus.COMPLETED,
        file_path=sample_pdf_path,
        mime_type="application/pdf",
        size=Path(sample_pdf_path).stat().st_size,
    )


class DictVectorStore(BaseVectorStore):
    """In-memory vector store for testing — exact copy from test_service.py."""

    def __init__(self):
        self._vectors: dict[str, list[float]] = {}
        self._metadatas: dict[str, dict] = {}

    async def upsert(self, embeddings: list[ChunkEmbedding]) -> None:
        for e in embeddings:
            self._vectors[e.chunk_id] = e.embedding
            self._metadatas[e.chunk_id] = {
                "document_id": e.document_id,
                "model": e.model,
            }

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
        scores = scores[: query.top_k]
        items = [
            SearchResultItem(
                chunk=Chunk(
                    id=cid,
                    document_id=self._metadatas.get(cid, {}).get("document_id", ""),
                    text="",
                ),
                score=score,
                document_metadata=self._metadatas.get(cid, {}),
            )
            for cid, score in scores
        ]
        return SearchResult(query=query, items=items, total_found=len(items))

    async def delete(self, document_id: str) -> None:
        to_remove = [
            cid
            for cid, md in self._metadatas.items()
            if md.get("document_id") == document_id
        ]
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
    """Deterministic mock embedding provider."""

    provider_name = "mock"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 100) / 100.0 for _ in range(4)] for t in texts]

    @property
    def dimensions(self) -> int:
        return 4

    @property
    def model_name(self) -> str:
        return "e2e-mock-v1"


@pytest.fixture
def dict_vector_store() -> DictVectorStore:
    return DictVectorStore()


@pytest.fixture
def mock_embedder() -> MockEmbedder:
    return MockEmbedder()


@pytest.fixture
def kb_settings() -> KBSettings:
    s = KBSettings()
    s.storage.database_path = ":memory:"
    s.chunking.strategy = "section"
    s.chunking.min_chunk_length = 1
    return s


@pytest.fixture
def knowledge_base(
    kb_settings: KBSettings,
    dict_vector_store: DictVectorStore,
    mock_embedder: MockEmbedder,
) -> KnowledgeBaseService:
    kb = KnowledgeBaseService(
        settings=kb_settings,
        storage=SQLiteStorage(database_path=":memory:"),
        vector_store=dict_vector_store,
        embedding_provider=mock_embedder,
    )
    return kb


@pytest.fixture
def processed_document(sample_article, sample_pdf_path) -> ProcessedDocument:
    return ProcessedDocument(
        article_id=sample_article.id,
        source_file=sample_pdf_path,
        status=ProcessingStatus.COMPLETED,
        metadata=DocumentMetadata(
            title=sample_article.title,
            abstract=sample_article.abstract,
            authors=sample_article.authors,
        ),
        sections=[
            ExtractedSection(
                heading="Introduction",
                content="This is the introduction section with enough text for chunking and embedding in our e2e pipeline test.",
                level=1,
            ),
            ExtractedSection(
                heading="Methods",
                content="We conducted integration tests using the full search-download-process-index-ask pipeline.",
                level=1,
            ),
            ExtractedSection(
                heading="Results",
                content="The e2e pipeline completed successfully. All stages produced valid outputs.",
                level=1,
            ),
        ],
        stats=ExtractionStats(total_pages=1, total_characters=350),
        raw_text=(
            "Introduction\n"
            "This is the introduction section with enough text for chunking "
            "and embedding in our e2e pipeline test.\n"
            "Methods\n"
            "We conducted integration tests using the full "
            "search-download-process-index-ask pipeline.\n"
            "Results\n"
            "The e2e pipeline completed successfully. All stages "
            "produced valid outputs."
        ),
    )


@pytest.fixture
def agent_settings() -> AgentSettings:
    s = AgentSettings()
    s.llm.provider = "ollama"
    s.llm.model = "e2e-mock"
    return s


@pytest.fixture
def response_cache() -> ResponseCache:
    return ResponseCache(ttl_seconds=10, max_size=16)


@pytest.fixture
async def research_agent(
    agent_settings: AgentSettings,
    knowledge_base: KnowledgeBaseService,
    response_cache: ResponseCache,
) -> ResearchAgent:
    agent = ResearchAgent(
        settings=agent_settings,
        knowledge_base=knowledge_base,
        cache=response_cache,
    )
    yield agent
    await agent.close()
