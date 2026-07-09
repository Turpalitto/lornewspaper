#!/usr/bin/env python3
"""End-to-end pipeline benchmark runner.

Runs the full pipeline multiple times and reports:
  - Per-stage latency (P50, P90, P99)
  - Total pipeline time
  - Stage-by-stage breakdown

Usage:
    python tests/e2e/benchmark.py [--iterations 10] [--output benchmark.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path
from statistics import median, quantiles
from typing import Any

import httpx
import respx

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.app import create_app
from api.dependencies import get_agent
from document_processing_service.service import DocumentProcessingService
from download_service.config import DownloaderConfig, Settings as DLSettings
from download_service.downloaders.base import BaseDownloader
from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from download_service.resolvers.base import BaseResolver
from download_service.service import DownloadService
from httpx import ASGITransport, AsyncClient
from knowledge_base.config import Settings as KBSettings
from knowledge_base.models import IndexingStatus
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.storage.sqlite import SQLiteStorage
from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings as AgentSettings
from search_service.config import ProviderConfig, Settings as SearchSettings
from search_service.service import SearchService

# Fixture imports
from tests.e2e.conftest import (
    DictVectorStore,
    MockEmbedder,
    _make_pdf_bytes,
    download_result as _make_download_result,
    processed_document as _make_processed_doc,
    sample_article as _make_sample_article,
    sample_pdf_path as _get_pdf_path,
)


def _pubmed_esearch():
    return httpx.Response(200, json={
        "esearchresult": {"idlist": ["e2e_bench_001"]},
    })


def _pubmed_efetch():
    return httpx.Response(200, json={
        "result": {
            "uids": ["e2e_bench_001"],
            "e2e_bench_001": {
                "title": "Benchmark Pipeline Test Article",
                "fulljournalname": "J Benchmark",
                "pubdate": "2024",
                "authors": [{"name": "Benchmark A"}],
                "articleids": [
                    {"idtype": "pubmed", "value": "e2e_bench_001"},
                    {"idtype": "doi", "value": "10.1234/bench.001"},
                    {"idtype": "pmc", "value": "PMCbench001"},
                ],
                "abstracttext": "Benchmark article for pipeline performance testing.",
                "keywords": ["benchmark"],
                "meshterms": ["performance"],
            },
        },
    })


def _europepmc_search():
    return httpx.Response(200, json={
        "resultList": {
            "result": [{
                "title": "Benchmark Pipeline Test Article",
                "authorString": "Benchmark A",
                "journalInfo": {"journal": {"title": "J Benchmark"}, "year": "2024"},
                "doi": "10.1234/bench.001",
                "pmid": "e2e_bench_001",
                "pmcid": "PMCbench001",
                "abstractText": "Benchmark article for pipeline performance testing.",
                "keywordList": {"keyword": [{"value": "benchmark"}]},
            }],
        },
    })


def _openalex_search():
    return httpx.Response(200, json={
        "meta": {"count": 1},
        "results": [{
            "id": "https://openalex.org/Wbench001",
            "title": "Benchmark Pipeline Test Article",
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/bench.001",
            "authorships": [{"author": {"display_name": "Benchmark A"}}],
            "host_venue": {"display_name": "J Benchmark"},
            "ids": {"doi": "https://doi.org/10.1234/bench.001", "pmid": "e2e_bench_001", "pmcid": "PMCbench001"},
            "abstract_inverted_index": {"benchmark": [0], "pipeline": [1]},
            "keywords": [{"display_name": "benchmark"}],
        }],
    })


class StubResolver(BaseResolver):
    name = "stub"
    async def resolve(self, article) -> list[ContentInfo]:
        return [ContentInfo(
            url=f"https://doi.org/{article.doi}",
            source="doi", confidence=0.9, content_type="application/pdf",
        )]


class StubDownloader(BaseDownloader):
    def __init__(self, pdf_path: str):
        self._pdf_path = pdf_path
    async def download(self, url, identifier, **kw):
        return DownloadResult(
            article_id=identifier, source="test", download_type="pdf",
            status=DownloadStatus.COMPLETED, file_path=self._pdf_path,
            mime_type="application/pdf",
        )


def _setup_services(pdf_path: str):
    """Initialize all services for a benchmark iteration."""
    article = _make_sample_article()
    article.id = "e2e_bench_001"
    article.doi = "10.1234/bench.001"

    kb_settings = KBSettings()
    kb_settings.storage.database_path = ":memory:"

    vector_store = DictVectorStore()
    embedder = MockEmbedder()
    kb = KnowledgeBaseService(
        settings=kb_settings,
        storage=SQLiteStorage(database_path=":memory:"),
        vector_store=vector_store,
        embedding_provider=embedder,
    )

    search_settings = SearchSettings()
    search_settings.concurrency_limit = 3
    search_settings.providers = {
        "pubmed": ProviderConfig(name="pubmed", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils", rate=100, burst=100),
        "europepmc": ProviderConfig(name="europepmc", base_url="https://www.ebi.ac.uk/europepmc/webservices/rest", rate=100, burst=100),
        "openalex": ProviderConfig(name="openalex", base_url="https://api.openalex.org", rate=100, burst=100),
    }
    search_svc = SearchService(settings=search_settings)

    dl_settings = DLSettings(cache_dir="/tmp/lornews_bench")
    dl_svc = DownloadService(
        settings=dl_settings,
        resolvers=[StubResolver()],
        downloaders={"pdf": StubDownloader(pdf_path)},
    )

    # Build processed document fixture
    processed = _make_processed_doc(article)
    processed.article_id = "e2e_bench_001"

    return article, kb, search_svc, dl_svc, processed


async def run_single_iteration(pdf_path: str, iteration: int) -> dict[str, float]:
    """Run one full pipeline iteration. Returns stage timings."""
    article, kb, search_svc, dl_svc, processed = _setup_services(pdf_path)
    times: dict[str, float] = {}

    try:
        # Stage 1: Search
        with respx.mock:
            respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch())
            respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch())
            respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(return_value=_europepmc_search())
            respx.get(url__regex=r".*/api\.openalex\.org/works").mock(return_value=_openalex_search())

            t0 = time.monotonic()
            results = await search_svc.search_all("Benchmark", limit=5)
            times["1_search"] = time.monotonic() - t0
        assert len(results) >= 1

        # Stage 2: Download
        t0 = time.monotonic()
        dl_result = await dl_svc.download(article=article)
        times["2_download"] = time.monotonic() - t0
        assert dl_result is not None

        # Stage 3: Process
        t0 = time.monotonic()
        dp_svc = DocumentProcessingService()
        processed_doc = await dp_svc.process(dl_result)
        times["3_process"] = time.monotonic() - t0
        assert processed_doc is not None

        # Stage 4: Index
        t0 = time.monotonic()
        indexed = await kb.index(processed_doc)
        times["4_index"] = time.monotonic() - t0
        assert indexed.status == IndexingStatus.COMPLETED

        # Stage 5: Ask
        agent_settings = AgentSettings()
        agent_settings.llm.provider = "ollama"
        agent = ResearchAgent(
            settings=agent_settings,
            knowledge_base=kb,
            cache=ResponseCache(ttl_seconds=10, max_size=16),
        )
        t0 = time.monotonic()
        result = await agent.ask("What methods were used?")
        times["5_ask"] = time.monotonic() - t0
        assert result.status.value == "completed"
        await agent.close()

        # Stage 6: API
        app = create_app()
        app.dependency_overrides[get_agent] = lambda: agent
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            t0 = time.monotonic()
            resp = await client.get("/api/v1/health")
            times["6_api"] = time.monotonic() - t0
            assert resp.status_code == 200

    finally:
        await kb.close()
        await search_svc.aclose()

    times["total"] = sum(times.values())
    return times


def _compute_stats(values: list[float]) -> dict[str, float]:
    if len(values) < 2:
        return {"min": values[0], "max": values[0], "p50": values[0], "p90": values[0], "p99": values[0]}
    q = quantiles(values, n=100)
    return {
        "min": min(values),
        "max": max(values),
        "p50": q[49],
        "p90": q[89],
        "p99": q[98],
        "mean": sum(values) / len(values),
    }


async def main():
    parser = argparse.ArgumentParser(description="E2E Pipeline Benchmark")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output file")
    args = parser.parse_args()

    print(f"LORNEWS E2E Pipeline Benchmark")
    print(f"{'='*60}")
    print(f"Iterations: {args.iterations}")
    print()

    # Create test PDF
    pdf_path = "/tmp/lornews_bench_paper.pdf"
    Path(pdf_path).write_bytes(_make_pdf_bytes())

    all_runs: list[dict[str, float]] = []
    stages = ["1_search", "2_download", "3_process", "4_index", "5_ask", "6_api"]

    for i in range(args.iterations):
        print(f"  Iteration {i+1}/{args.iterations}...", end=" ", flush=True)
        try:
            times = await run_single_iteration(pdf_path, i)
            all_runs.append(times)
            print(f"OK ({times['total']:.3f}s)")
        except Exception as e:
            print(f"FAILED: {e}")

    print()
    print(f"{'='*60}")
    print(f"  BENCHMARK RESULTS ({len(all_runs)} successful runs)")
    print(f"{'='*60}")
    print(f"  {'Stage':20s} {'P50':>8s} {'P90':>8s} {'P99':>8s} {'Mean':>8s}")
    print(f"  {'-'*52}")

    summary: dict[str, Any] = {"iterations": len(all_runs), "stages": {}}

    for stage in stages:
        values = [r[stage] for r in all_runs if stage in r]
        if not values:
            continue
        stats = _compute_stats(values)
        print(f"  {stage:20s} {stats['p50']:8.3f}s {stats['p90']:8.3f}s {stats['p99']:8.3f}s {stats['mean']:8.3f}s")
        summary["stages"][stage] = stats

    total_values = [r["total"] for r in all_runs if "total" in r]
    if total_values:
        stats = _compute_stats(total_values)
        print(f"  {'-'*52}")
        print(f"  {'Total':20s} {stats['p50']:8.3f}s {stats['p90']:8.3f}s {stats['p99']:8.3f}s {stats['mean']:8.3f}s")
        summary["total"] = stats

    print(f"{'='*60}")

    if args.output:
        Path(args.output).write_text(json.dumps(summary, indent=2))
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
