#!/usr/bin/env python3
"""BenchmarkRunner — dataset-scaled performance validation.

Supports PubMed, EuropePMC, OpenAlex providers with smoke/medium/large datasets.

Usage:
    python tests/e2e/benchmark_runner.py \\
        --provider pubmed \\
        --query "machine learning" \\
        --limit 100 \\
        --output benchmark_results.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, quantiles
from typing import Any

import httpx
import respx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from document_processing_service.config import Settings as DPSettings
from document_processing_service.service import DocumentProcessingService
from download_service.config import Settings as DLSettings
from download_service.downloaders.base import BaseDownloader
from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from download_service.resolvers.base import BaseResolver
from download_service.service import DownloadService
from knowledge_base.config import Settings as KBSettings
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.storage.sqlite import SQLiteStorage
from knowledge_base.vector.base import BaseVectorStore
from knowledge_base.vector.chroma import ChromaVectorStore
from knowledge_base.models import Chunk, ChunkEmbedding, SearchQuery, SearchResult, SearchResultItem
from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings as AgentSettings
from search_service.config import ProviderConfig, Settings as SearchSettings
from search_service.service import SearchService

from tests.e2e.conftest import DictVectorStore, MockEmbedder, _make_pdf_bytes


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DOI = "10.1234/benchmark.{n}"
SAMPLE_PMID = "BM{n}"
SAMPLE_PMCID = "PMCbench{n}"

DATASET_SIZES = {
    "smoke": 10,
    "medium": 100,
    "large": 1000,
}


def _pubmed_esearch(count: int):
    ids = [str(1000000 + i) for i in range(count)]
    return httpx.Response(200, json={
        "esearchresult": {"idlist": ids},
    })


def _pubmed_efetch(count: int):
    results = {}
    for i in range(count):
        n = str(1000000 + i)
        results[n] = {
            "title": f"Benchmark Article {i}",
            "fulljournalname": "J Benchmark",
            "pubdate": "2024",
            "authors": [{"name": f"Author {i}"}],
            "articleids": [
                {"idtype": "pubmed", "value": n},
                {"idtype": "doi", "value": f"10.1234/bench.{i:04d}"},
                {"idtype": "pmc", "value": f"PMCbench{i:04d}"},
            ],
            "abstracttext": f"This is benchmark article {i} for performance testing." * 5,
            "keywords": [f"keyword-{i % 10}"],
            "meshterms": ["benchmark"],
        }
    return httpx.Response(200, json={"result": {"uids": list(results.keys()), **results}})


def _europepmc_search(count: int):
    results = []
    for i in range(count):
        results.append({
            "title": f"Benchmark Article {i}",
            "authorString": f"Author {i}",
            "journalInfo": {"journal": {"title": "J Benchmark"}, "year": "2024"},
            "doi": f"10.1234/bench.{i:04d}",
            "pmid": str(1000000 + i),
            "pmcid": f"PMCbench{i:04d}",
            "abstractText": f"This is benchmark article {i} for performance testing." * 5,
            "keywordList": {"keyword": [{"value": f"keyword-{i % 10}"}]},
        })
    return httpx.Response(200, json={"resultList": {"result": results}})


def _openalex_search(count: int):
    results = []
    for i in range(count):
        results.append({
            "id": f"https://openalex.org/Wbench{i:04d}",
            "title": f"Benchmark Article {i}",
            "publication_year": 2024,
            "doi": f"https://doi.org/10.1234/bench.{i:04d}",
            "authorships": [{"author": {"display_name": f"Author {i}"}}],
            "host_venue": {"display_name": "J Benchmark"},
            "ids": {
                "doi": f"https://doi.org/10.1234/bench.{i:04d}",
                "pmid": str(1000000 + i),
                "pmcid": f"PMCbench{i:04d}",
            },
            "abstract_inverted_index": {f"benchmark-{i}": [0]},
            "keywords": [{"display_name": f"keyword-{i % 10}"}],
        })
    return httpx.Response(200, json={"meta": {"count": count}, "results": results})


# ---------------------------------------------------------------------------
# Mock downloader that returns programmatic PDF
# ---------------------------------------------------------------------------

class FixtureDownloader(BaseDownloader):
    def __init__(self, pdf_path: str):
        self._pdf_path = pdf_path
        self.success_count = 0
        self.fail_count = 0
        self.fail_rate = 0.0

    async def download(self, url, identifier, **kw):
        if self.fail_rate > 0 and hash(identifier) % 100 < self.fail_rate * 100:
            self.fail_count += 1
            return None
        self.success_count += 1
        return DownloadResult(
            article_id=identifier, source="test", download_type="pdf",
            status=DownloadStatus.COMPLETED, file_path=self._pdf_path,
            mime_type="application/pdf",
        )


class FixtureResolver(BaseResolver):
    name = "fixture"
    async def resolve(self, article) -> list[ContentInfo]:
        return [ContentInfo(
            url=f"https://doi.org/{article.doi}",
            source="doi", confidence=0.9, content_type="application/pdf",
        )]


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

@dataclass
class StageMetrics:
    latency_ms: list[float] = field(default_factory=list)
    success: int = 0
    failure: int = 0


@dataclass
class BenchmarkResult:
    provider: str
    dataset_size: int
    stages: dict[str, StageMetrics] = field(default_factory=dict)
    total_duration_s: float = 0.0
    throughput_items_s: float = 0.0
    memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    ocr_usage: int = 0
    download_failures: int = 0
    processing_failures: int = 0
    indexing_success: int = 0
    retrieval_success: int = 0


class BenchmarkRunner:
    def __init__(self, provider: str, query: str, limit: int, output: str = ""):
        self.provider = provider
        self.query = query
        self.limit = max(1, min(limit, 1000))
        self.output = output
        self._pdf_path = "/tmp/lornews_bench_paper.pdf"
        self.result = BenchmarkResult(provider=provider, dataset_size=self.limit)

    async def run(self):
        print(f"\nBenchmarkRunner: provider={self.provider} query='{self.query}' limit={self.limit}")

        # Create test PDF
        Path(self._pdf_path).write_bytes(_make_pdf_bytes())

        # Initialize services
        search_svc = self._init_search()
        dl_svc, downloader = self._init_download()
        kb = self._init_kb()

        stages = ["search", "download", "process", "index", "retrieval"]
        for s in stages:
            self.result.stages[s] = StageMetrics()

        pdf_paths: list[str] = []

        try:
            # ---- Search ----
            async with respx.mock:
                self._mock_providers()
                t0 = time.perf_counter()
                articles = await search_svc.search_all(self.query, limit=self.limit)
                search_time = time.perf_counter() - t0

            self.result.stages["search"].latency_ms.append(search_time * 1000)
            self.result.stages["search"].success = len(articles)
            print(f"  Search: {len(articles)} articles in {search_time:.2f}s")

            # ---- Download + Process + Index ----
            for i, article in enumerate(articles):
                # Download
                t0 = time.perf_counter()
                dl_result = await dl_svc.download(article=article)
                dl_time = time.perf_counter() - t0
                self.result.stages["download"].latency_ms.append(dl_time * 1000)

                if dl_result is None:
                    self.result.download_failures += 1
                    self.result.stages["download"].failure += 1
                    continue
                self.result.stages["download"].success += 1

                # Process
                t0 = time.perf_counter()
                dp_svc = DocumentProcessingService()
                processed = await dp_svc.process(dl_result)
                proc_time = time.perf_counter() - t0
                self.result.stages["process"].latency_ms.append(proc_time * 1000)

                if processed is None or processed.status.value != "completed":
                    self.result.processing_failures += 1
                    self.result.stages["process"].failure += 1
                    continue
                self.result.stages["process"].success += 1
                if processed.stats and processed.stats.ocr_applied:
                    self.result.ocr_usage += 1

                # Index
                t0 = time.perf_counter()
                indexed = await kb.index(processed)
                idx_time = time.perf_counter() - t0
                self.result.stages["index"].latency_ms.append(idx_time * 1000)

                if indexed and indexed.status.value == "completed":
                    self.result.indexing_success += 1
                    self.result.stages["index"].success += 1
                else:
                    self.result.stages["index"].failure += 1

                pdf_paths.append(dl_result.file_path)

                if (i + 1) % 50 == 0:
                    print(f"  Progress: {i+1}/{len(articles)}")

            # ---- Retrieval ----
            t0 = time.perf_counter()
            results = await kb.search_text(self.query, top_k=10)
            ret_time = time.perf_counter() - t0
            self.result.stages["retrieval"].latency_ms.append(ret_time * 1000)
            self.result.stages["retrieval"].success = len(results.items)
            self.result.retrieval_success = len(results.items)
            print(f"  Retrieval: {len(results.items)} results in {ret_time:.2f}s")

        finally:
            await search_svc.aclose()
            await kb.close()

        # ---- Summary ----
        self.result.total_duration_s = sum(
            mean(m.latency_ms) / 1000 if m.latency_ms else 0
            for m in self.result.stages.values()
        )
        self.result.throughput_items_s = self.limit / max(self.result.total_duration_s, 0.001)

        return self.result

    def _init_search(self) -> SearchService:
        s = SearchSettings()
        s.concurrency_limit = 10
        s.http_timeout = 10.0
        s.providers = {
            "pubmed": ProviderConfig(name="pubmed", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils", rate=1000, burst=1000),
            "europepmc": ProviderConfig(name="europepmc", base_url="https://www.ebi.ac.uk/europepmc/webservices/rest", rate=1000, burst=1000),
            "openalex": ProviderConfig(name="openalex", base_url="https://api.openalex.org", rate=1000, burst=1000),
        }
        s.providers["pubmed"].enabled = self.provider in ("pubmed", "all")
        s.providers["europepmc"].enabled = self.provider in ("europepmc", "all")
        s.providers["openalex"].enabled = self.provider in ("openalex", "all")
        return SearchService(settings=s)

    def _init_download(self):
        dl = FixtureDownloader(self._pdf_path)
        settings = DLSettings(cache_dir="/tmp/lornews_bench_dl")
        svc = DownloadService(
            settings=settings,
            resolvers=[FixtureResolver()],
            downloaders={"pdf": dl},
        )
        return svc, dl

    def _init_kb(self) -> KnowledgeBaseService:
        s = KBSettings()
        s.storage.database_path = ":memory:"
        return KnowledgeBaseService(
            settings=s,
            storage=SQLiteStorage(database_path=":memory:"),
            vector_store=DictVectorStore(),
            embedding_provider=MockEmbedder(),
        )

    def _mock_providers(self):
        if self.provider in ("pubmed", "all"):
            respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch(self.limit))
            respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch(self.limit))
        if self.provider in ("europepmc", "all"):
            respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(
                return_value=_europepmc_search(self.limit))
        if self.provider in ("openalex", "all"):
            respx.get(url__regex=r".*/api\.openalex\.org/works").mock(
                return_value=_openalex_search(self.limit))

    def report(self) -> dict[str, Any]:
        stages = {}
        for name, metrics in self.result.stages.items():
            latencies = metrics.latency_ms
            stages[name] = {
                "avg_latency_ms": round(mean(latencies), 2) if latencies else 0,
                "p50_ms": round(sorted(latencies)[len(latencies) // 2], 2) if len(latencies) > 1 else 0,
                "p90_ms": round(sorted(latencies)[int(len(latencies) * 0.9)], 2) if len(latencies) > 1 else 0,
                "success": metrics.success,
                "failure": metrics.failure,
            }

        return {
            "provider": self.result.provider,
            "dataset_size": self.result.dataset_size,
            "stages": stages,
            "total_duration_s": round(self.result.total_duration_s, 2),
            "throughput_items_per_second": round(self.result.throughput_items_s, 2),
            "download_failures": self.result.download_failures,
            "processing_failures": self.result.processing_failures,
            "indexing_success": self.result.indexing_success,
            "retrieval_success": self.result.retrieval_success,
            "success_rate_pct": round(
                (self.result.indexing_success / max(self.result.dataset_size, 1)) * 100, 1
            ),
        }


async def main():
    parser = argparse.ArgumentParser(description="LORNEWS BenchmarkRunner")
    parser.add_argument("--provider", default="pubmed", choices=["pubmed", "europepmc", "openalex", "all"])
    parser.add_argument("--query", default="machine learning")
    parser.add_argument("--limit", type=int, default=10, help="Number of articles (use 10/100/1000 for dataset sizes)")
    parser.add_argument("--dataset", choices=["smoke", "medium", "large", "custom"], default="custom")
    parser.add_argument("--output", default="benchmark_results.json")
    args = parser.parse_args()

    if args.dataset != "custom":
        args.limit = DATASET_SIZES[args.dataset]

    runner = BenchmarkRunner(args.provider, args.query, args.limit, args.output)
    result = await runner.run()

    report = runner.report()
    print(f"\n{'='*60}")
    print(f"  BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"  Provider:      {report['provider']}")
    print(f"  Dataset size:  {report['dataset_size']}")
    print(f"  Success rate:  {report['success_rate_pct']}%")
    print(f"  Throughput:    {report['throughput_items_per_second']}/s")
    print(f"  Duration:      {report['total_duration_s']}s")
    print(f"{'─'*60}")
    for stage, metrics in report["stages"].items():
        print(f"  {stage:20s} avg={metrics['avg_latency_ms']:>8.1f}ms  "
              f"p50={metrics['p50_ms']:>8.1f}ms  "
              f"p90={metrics['p90_ms']:>8.1f}ms  "
              f"ok={metrics['success']} fail={metrics['failure']}")
    print(f"{'='*60}")

    if args.output:
        report["timestamp"] = datetime.now(UTC).isoformat()
        Path(args.output).write_text(json.dumps(report, indent=2))
        print(f"\nResults saved: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
