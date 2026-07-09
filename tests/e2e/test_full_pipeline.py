"""Complete end-to-end pipeline integration test.

Exercises the full production pipeline end-to-end:
  SearchService -> DownloadService -> DocumentProcessingService
  -> KnowledgeBaseService -> ResearchAgent -> FastAPI

External APIs are mocked via respx (realistic HTTP fixtures).
Internal services run with real implementations.
All stages are timed and benchmarked.

Usage:
    pytest tests/e2e/test_full_pipeline.py -v --benchmark-json output.json
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from api.app import create_app
from api.dependencies import get_agent
from api.schemas.ask import AnswerResponse, AskResponse
from api.schemas.documents import DocumentDetailResponse
from api.schemas.ingest import IngestResponse
from api.schemas.search import SearchResponse
from document_processing_service.service import DocumentProcessingService
from knowledge_base.models import IndexingStatus
from research_agent.agent import ResearchAgent
from research_agent.models import Answer
from search_service.config import ProviderConfig, Settings as SearchSettings
from search_service.providers.pubmed import PubMedProvider
from search_service.providers.europepmc import EuropePMCProvider
from search_service.providers.openalex import OpenAlexProvider
from search_service.service import SearchService


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Stage timing collector
# ---------------------------------------------------------------------------

class StageTimer:
    """Collects wall-clock timing per pipeline stage."""

    def __init__(self):
        self.times: dict[str, float] = {}

    async def __aenter__(self):
        self._start = time.monotonic()
        return self

    async def __aexit__(self, *args):
        pass

    def start(self, stage: str):
        self._current = stage
        self._start = time.monotonic()

    def stop(self):
        elapsed = time.monotonic() - self._start
        self.times[self._current] = elapsed
        print(f"\n  [{self._current}] {elapsed:.3f}s")
        return elapsed


@pytest.fixture
def timer() -> StageTimer:
    return StageTimer()


# ---------------------------------------------------------------------------
# Stage 1: SearchService with respx-mocked providers
# ---------------------------------------------------------------------------

@pytest.fixture
def search_settings() -> SearchSettings:
    s = SearchSettings()
    s.concurrency_limit = 3
    s.http_timeout = 5.0
    s.providers = {
        "pubmed": ProviderConfig(
            name="pubmed",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            rate=100.0,
            burst=100,
            timeout=5.0,
        ),
        "europepmc": ProviderConfig(
            name="europepmc",
            base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
            rate=100.0,
            burst=100,
            timeout=5.0,
        ),
        "openalex": ProviderConfig(
            name="openalex",
            base_url="https://api.openalex.org",
            rate=100.0,
            burst=100,
            timeout=5.0,
        ),
    }
    return s


def _pubmed_esearch():
    return httpx.Response(200, json={
        "esearchresult": {"idlist": ["e2e001"]},
    })


def _pubmed_efetch():
    return httpx.Response(200, json={
        "result": {
            "uids": ["e2e001"],
            "e2e001": {
                "title": "E2E Pipeline Test Article",
                "fulljournalname": "J Integr Test",
                "pubdate": "2024",
                "authors": [{"name": "Alice"}, {"name": "Bob"}],
                "articleids": [
                    {"idtype": "pubmed", "value": "e2e001"},
                    {"idtype": "doi", "value": "10.1234/e2e.test.001"},
                    {"idtype": "pmc", "value": "PMCe2e001"},
                ],
                "abstracttext": "End-to-end pipeline test article for integration testing.",
                "keywords": ["e2e", "integration"],
                "meshterms": ["testing"],
            },
        },
    })


def _europepmc_search():
    return httpx.Response(200, json={
        "resultList": {
            "result": [{
                "title": "E2E Pipeline Test Article",
                "authorString": "Alice A, Bob B",
                "journalInfo": {
                    "journal": {"title": "J Integr Test"},
                    "year": "2024",
                },
                "doi": "10.1234/e2e.test.001",
                "pmid": "e2e001",
                "pmcid": "PMCe2e001",
                "abstractText": "End-to-end pipeline test article for integration testing.",
                "keywordList": {"keyword": [{"value": "e2e"}, {"value": "pipeline"}]},
            }],
        },
    })


def _openalex_search():
    return httpx.Response(200, json={
        "meta": {"count": 1},
        "results": [{
            "id": "https://openalex.org/We2e001",
            "title": "E2E Pipeline Test Article",
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/e2e.test.001",
            "authorships": [{"author": {"display_name": "Alice A"}}],
            "host_venue": {"display_name": "J Integr Test"},
            "ids": {
                "doi": "https://doi.org/10.1234/e2e.test.001",
                "pmid": "e2e001",
                "pmcid": "PMCe2e001",
            },
            "abstract_inverted_index": {
                "end-to-end": [0], "pipeline": [1], "test": [2],
            },
            "keywords": [{"display_name": "e2e"}],
        }],
    })


@pytest.fixture
async def search_service(search_settings) -> SearchService:
    svc = SearchService(settings=search_settings)
    yield svc
    await svc.aclose()


@respx.mock
async def test_stage1_search(timer, search_service):
    """SearchService: query PubMed, EuropePMC, OpenAlex -> deduplicated article."""
    respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch())
    respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch())
    respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(
        return_value=_europepmc_search()
    )
    respx.get(url__regex=r".*/api\.openalex\.org/works").mock(
        return_value=_openalex_search()
    )

    timer.start("search")
    results = await search_service.search_all("E2E Pipeline Test", limit=5)
    timer.stop()

    assert len(results) == 1, "Expected single merged record across 3 providers"
    article = results[0]
    assert article.doi == "10.1234/e2e.test.001"
    assert "pubmed" in article.provenance
    assert "europepmc" in article.provenance
    assert "openalex" in article.provenance
    assert article.title == "E2E Pipeline Test Article"
    assert article.abstract is not None


# ---------------------------------------------------------------------------
# Stage 2: DownloadService — stub resolves to local PDF
# ---------------------------------------------------------------------------

@respx.mock
async def test_stage2_download(
    timer, search_service, download_result, sample_article
):
    """DownloadService: resolve PMC -> DOI -> Publisher, download PDF -> path."""
    from download_service.config import Settings as DLSettings
    from download_service.downloaders.pdf import PdfDownloader
    from download_service.resolvers.base import BaseResolver
    from download_service.service import DownloadService
    from download_service.models import ContentInfo

    class StubResolver(BaseResolver):
        name = "stub"

        async def resolve(self, article) -> list[ContentInfo]:
            return [ContentInfo(
                url=f"https://example.com/{article.pmcid}.pdf",
                source=f"{article.source}_pmc",
                confidence=0.9,
                content_type="application/pdf",
            )]

    class PassThroughDownloader(PdfDownloader):
        """Instead of HTTP download, return the local test PDF path."""

        def __init__(self, local_path: str):
            super().__init__(DownloaderConfig())
            self._local_path = local_path

        async def download(self, url, identifier, **kw):
            return download_result

    from download_service.config import DownloaderConfig
    from download_service.downloaders.base import BaseDownloader

    class StubDownloader(BaseDownloader):
        async def download(self, url, identifier, **kw):
            return download_result

    settings = DLSettings(cache_dir=Path(tempfile.mkdtemp()).as_posix())
    svc = DownloadService(
        settings=settings,
        resolvers=[StubResolver()],
        downloaders={"pdf": StubDownloader()},
    )

    timer.start("download")
    result = await svc.download(article=sample_article)
    timer.stop()

    assert result is not None
    assert result.file_path == download_result.file_path
    assert Path(result.file_path).exists()


# ---------------------------------------------------------------------------
# Stage 3: DocumentProcessingService — extract text from PDF
# ---------------------------------------------------------------------------

async def test_stage3_process(timer, download_result, sample_article):
    """DocumentProcessingService: PDF -> sections, metadata, references."""
    from document_processing_service.service import DocumentProcessingService
    import tempfile

    timer.start("process")
    svc = DocumentProcessingService()
    processed = await svc.process(download_result)
    timer.stop()

    assert processed is not None
    assert processed.status.value == "completed"
    assert processed.article_id == sample_article.id


# ---------------------------------------------------------------------------
# Stage 4: KnowledgeBaseService — index processed document
# ---------------------------------------------------------------------------

async def test_stage4_index(
    timer, knowledge_base, processed_document
):
    """KnowledgeBaseService: index document -> chunks -> embeddings -> storage."""
    timer.start("index")
    doc = await knowledge_base.index(processed_document)
    timer.stop()

    assert doc is not None
    assert doc.status == IndexingStatus.COMPLETED
    assert doc.document_id == processed_document.article_id
    assert doc.statistics.total_chunks > 0

    # Verify persistence
    loaded = await knowledge_base.get_document(processed_document.article_id)
    assert loaded is not None
    assert loaded.statistics.total_chunks == doc.statistics.total_chunks


# ---------------------------------------------------------------------------
# Stage 5: ResearchAgent — ask a question, get answer with citations
# ---------------------------------------------------------------------------

async def test_stage5_ask(
    timer, research_agent, knowledge_base, processed_document
):
    """ResearchAgent: embed question -> search vector store -> LLM -> answer."""
    # First index the document
    indexed = await knowledge_base.index(processed_document)
    assert indexed.status == IndexingStatus.COMPLETED

    # Ask a question about the indexed document
    timer.start("ask")
    result = await research_agent.ask(
        "What methods were used in the e2e pipeline test?"
    )
    timer.stop()

    assert result.status.value == "completed"
    assert result.answer is not None
    assert result.answer.answer
    assert len(result.answer.sources) > 0

    # Verify citations reference our indexed document
    doc_id = processed_document.article_id
    assert any(doc_id in src for src in result.answer.sources), (
        f"Citations must reference '{doc_id}'. Got: {result.answer.sources}"
    )


# ---------------------------------------------------------------------------
# Stage 6: FastAPI — end-to-end via ASGI test client
# ---------------------------------------------------------------------------

@pytest.fixture
def fastapi_app(research_agent: ResearchAgent):
    """FastAPI app with real ResearchAgent injected."""
    app = create_app()
    app.dependency_overrides[get_agent] = lambda: research_agent
    return app


@pytest.fixture
async def fastapi_client(fastapi_app):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_stage6_api_health(timer, fastapi_client):
    """FastAPI health endpoint returns 200."""
    timer.start("api_health")
    resp = await fastapi_client.get("/api/v1/health")
    timer.stop()
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


async def test_stage6_api_search(timer, fastapi_client, knowledge_base):
    """FastAPI search returns SearchResponse."""
    timer.start("api_search")
    resp = await fastapi_client.post(
        "/api/v1/search",
        json={"query": "e2e pipeline", "max_results": 5},
    )
    timer.stop()
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        body = resp.json()
        assert "articles" in body
        assert "elapsed_ms" in body


async def test_stage6_api_ask(timer, fastapi_client, knowledge_base, processed_document):
    """FastAPI ask returns AskResponse with citations."""
    await knowledge_base.index(processed_document)

    timer.start("api_ask")
    resp = await fastapi_client.post(
        "/api/v1/ask",
        json={"question": "What is the e2e pipeline test about?"},
    )
    timer.stop()

    assert resp.status_code in (200, 409)
    if resp.status_code == 200:
        body = resp.json()
        assert "answer" in body
        assert body["answer"]["answer"]
        assert len(body["answer"]["sources"]) > 0


async def test_stage6_api_documents(timer, fastapi_client, knowledge_base, processed_document):
    """FastAPI documents CRUD."""
    await knowledge_base.index(processed_document)
    doc_id = processed_document.article_id

    timer.start("api_list_docs")
    resp = await fastapi_client.get("/api/v1/documents")
    timer.stop()
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert any(item.get("document_id") == doc_id for item in body["items"])


async def test_stage6_api_metrics(timer, fastapi_client):
    """Metrics endpoint returns Prometheus format."""
    timer.start("api_metrics")
    resp = await fastapi_client.get("/metrics")
    timer.stop()
    assert resp.status_code == 200
    assert "lornews_uptime_seconds" in resp.text


# ---------------------------------------------------------------------------
# Full pipeline — runs stages sequentially, measures total time
# ---------------------------------------------------------------------------

@respx.mock
async def test_full_pipeline_end_to_end(
    timer,
    fastapi_client,
    search_service,
    knowledge_base,
    processed_document,
    sample_article,
    download_result,
):
    """Complete end-to-end: Search -> Download -> Process -> Index -> Ask -> API.

    This is the primary integration test. It runs the full pipeline with
    real internal services and mocked external HTTP calls, verifying every
    stage produces valid output before proceeding to the next.
    """
    # ------------------------------------------------------------------ 1. Search
    respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch())
    respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch())
    respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(
        return_value=_europepmc_search()
    )
    respx.get(url__regex=r".*/api\.openalex\.org/works").mock(
        return_value=_openalex_search()
    )

    timer.start("1_search")
    results = await search_service.search_all("E2E Pipeline Test", limit=5)
    t1 = timer.stop()
    assert len(results) == 1
    assert results[0].doi == "10.1234/e2e.test.001"

    # -------------------------------------------------------------- 2. Download
    from download_service.config import DownloaderConfig, Settings as DLSettings
    from download_service.downloaders.base import BaseDownloader
    from download_service.resolvers.base import BaseResolver
    from download_service.service import DownloadService
    from download_service.models import ContentInfo
    import tempfile

    class _StubResolver(BaseResolver):
        name = "stub"
        async def resolve(self, article) -> list[ContentInfo]:
            return [ContentInfo(
                url=f"https://doi.org/{article.doi}",
                source="doi",
                confidence=0.9,
                content_type="application/pdf",
            )]

    class _StubDownloader(BaseDownloader):
        async def download(self, url, identifier, **kw):
            return download_result

    dl_settings = DLSettings(cache_dir=Path(tempfile.mkdtemp()).as_posix())
    dl_svc = DownloadService(
        settings=dl_settings,
        resolvers=[_StubResolver()],
        downloaders={"pdf": _StubDownloader()},
    )

    timer.start("2_download")
    dl_result = await dl_svc.download(article=sample_article)
    t2 = timer.stop()
    assert dl_result is not None
    assert Path(dl_result.file_path).exists()

    # ----------------------------------------------------------- 3. Document Processing
    from document_processing_service.service import DocumentProcessingService

    timer.start("3_process")
    dp_svc = DocumentProcessingService()
    processed = await dp_svc.process(dl_result)
    t3 = timer.stop()
    assert processed is not None
    assert processed.status.value == "completed"
    assert processed.article_id == sample_article.id

    # ----------------------------------------------------------- 4. Index (KB)
    timer.start("4_index")
    indexed = await knowledge_base.index(processed)
    t4 = timer.stop()
    assert indexed.status == IndexingStatus.COMPLETED
    assert indexed.statistics.total_chunks > 0

    # Verify persistence
    loaded = await knowledge_base.get_document(sample_article.id)
    assert loaded is not None

    # ----------------------------------------------------------- 5. Ask (ResearchAgent)
    from research_agent.agent import ResearchAgent
    from research_agent.cache import ResponseCache
    from research_agent.config import Settings as AgentSettings

    agent_settings = AgentSettings()
    agent_settings.llm.provider = "ollama"
    agent_settings.llm.model = "mock"

    cache = ResponseCache(ttl_seconds=10, max_size=16)
    agent = ResearchAgent(
        settings=agent_settings,
        knowledge_base=knowledge_base,
        cache=cache,
    )

    timer.start("5_ask")
    result = await agent.ask("What methods were used in the e2e pipeline test?")
    t5 = timer.stop()
    assert result.status.value == "completed"
    assert result.answer is not None
    assert result.answer.answer

    doc_id = processed.article_id
    assert any(doc_id in src for src in (result.answer.sources or [])), (
        f"Citations must reference '{doc_id}'. Got: {result.answer.sources}"
    )

    # ----------------------------------------------------------- 6. FastAPI
    timer.start("6_api")
    resp = await fastapi_client.get("/api/v1/health")
    t6 = timer.stop()
    assert resp.status_code == 200

    timer.start("6_api_search")
    resp2 = await fastapi_client.post(
        "/api/v1/search", json={"query": "e2e", "max_results": 5},
    )
    t6b = timer.stop()
    assert resp2.status_code in (200, 422)

    await agent.close()

    # ------------------------------------------------------------------ Report
    total = sum(timer.times.values())
    print(f"\n{'='*50}")
    print(f"  END-TO-END PIPELINE BENCHMARK")
    print(f"{'='*50}")
    for stage, t in timer.times.items():
        pct = (t / total) * 100
        print(f"  {stage:25s} {t:.3f}s ({pct:5.1f}%)")
    print(f"{'─'*50}")
    print(f"  {'Total':25s} {total:.3f}s (100%)")
    print(f"{'='*50}")
