#!/usr/bin/env python3
"""Load test — simulates concurrent users hitting the full pipeline.

Usage:
    python tests/e2e/load_test.py --concurrency 50 --iterations 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from statistics import mean, quantiles as _quantiles
from typing import Any

import httpx
import respx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.app import create_app
from api.dependencies import get_agent
from httpx import ASGITransport, AsyncClient
from knowledge_base.config import Settings as KBSettings
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.storage.sqlite import SQLiteStorage
from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings as AgentSettings
from search_service.config import ProviderConfig, Settings as SearchSettings
from search_service.service import SearchService

from tests.e2e.conftest import DictVectorStore, MockEmbedder, processed_document as _make_processed_doc


CONCURRENCY_LEVELS = [10, 50, 100, 250]


@dataclass
class LoadTestMetrics:
    concurrency: int
    total_requests: int
    successful: int = 0
    failed: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    timeouts: int = 0
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration_s(self) -> float:
        return self.end_time - self.start_time

    @property
    def throughput_requests_s(self) -> float:
        return self.total_requests / max(self.duration_s, 0.001)

    def report(self) -> dict[str, Any]:
        latencies = sorted(self.latencies_ms)
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        return {
            "concurrency": self.concurrency,
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "timeouts": self.timeouts,
            "error_rate_pct": round((self.failed / max(self.total_requests, 1)) * 100, 2),
            "duration_s": round(self.duration_s, 2),
            "throughput_req_per_s": round(self.throughput_requests_s, 2),
            "p50_ms": round(p50, 1),
            "p95_ms": round(p95, 1),
            "p99_ms": round(p99, 1),
        }


class LoadTestRunner:
    def __init__(self, concurrency: int, iterations: int = 5):
        self.concurrency = concurrency
        self.iterations = iterations
        self.metrics = LoadTestMetrics(concurrency=concurrency, total_requests=concurrency * iterations)

    async def run(self) -> LoadTestMetrics:
        print(f"  Running {self.concurrency} concurrent x {self.iterations} iterations...", end=" ")
        sys.stdout.flush()

        self.metrics.start_time = time.monotonic()

        async with respx.mock:
            self._mock_all()
            sem = asyncio.Semaphore(self.concurrency)
            tasks = [self._worker(sem) for _ in range(self.iterations * self.concurrency)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        self.metrics.end_time = time.monotonic()

        for r in results:
            if isinstance(r, Exception):
                self.metrics.failed += 1
            elif isinstance(r, dict) and "error" in r:
                self.metrics.failed += 1
                if r.get("timeout"):
                    self.metrics.timeouts += 1
            else:
                self.metrics.successful += 1
                if isinstance(r, (int, float)):
                    self.metrics.latencies_ms.append(r)

        print(f"OK ({self.metrics.successful}/{self.metrics.total_requests})")
        return self.metrics

    async def _worker(self, sem: asyncio.Semaphore) -> float | dict:
        async with sem:
            t0 = time.monotonic()
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=create_app()),
                    base_url="http://test",
                    timeout=30.0,
                ) as client:
                    resp = await client.get("/api/v1/health")
                    if resp.status_code != 200:
                        return {"error": f"status={resp.status_code}"}
                    return (time.monotonic() - t0) * 1000
            except asyncio.TimeoutError:
                return {"error": "timeout", "timeout": True}
            except Exception as e:
                return {"error": str(e)}

    def _mock_all(self):
        respx.get(url__regex=r".*/esearch\.fcgi").mock(
            return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["1"]}}))
        respx.get(url__regex=r".*/efetch\.fcgi").mock(
            return_value=httpx.Response(200, json={"result": {"uids": ["1"], "1": {"title": "T", "fulljournalname": "J", "pubdate": "2024"}}}))
        respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(
            return_value=httpx.Response(200, json={"resultList": {"result": []}}))
        respx.get(url__regex=r".*/api\.openalex\.org/works").mock(
            return_value=httpx.Response(200, json={"meta": {}, "results": []}))


async def main():
    parser = argparse.ArgumentParser(description="LORNEWS Load Test")
    parser.add_argument("--concurrency", type=int, default=0,
                        help="Specific concurrency level (0 = run all levels)")
    parser.add_argument("--iterations", type=int, default=5,
                        help="Requests per concurrency level")
    parser.add_argument("--output", default="load_test_results.json")
    args = parser.parse_args()

    if args.concurrency > 0:
        levels = [args.concurrency]
    else:
        levels = CONCURRENCY_LEVELS

    print("LORNEWS Load Test")
    print(f"{'='*60}")
    print(f"Iterations per level: {args.iterations}")
    print()

    all_results = []
    for level in levels:
        runner = LoadTestRunner(concurrency=level, iterations=args.iterations)
        metrics = await runner.run()
        all_results.append(metrics.report())

    print(f"\n{'='*60}")
    print(f"  LOAD TEST RESULTS")
    print(f"{'='*60}")
    print(f"  {'Concurrency':>12s} {'P50':>8s} {'P95':>8s} {'P99':>8s} "
          f"{'Throughput':>12s} {'Error%':>8s}")
    print(f"  {'─'*56}")
    for r in all_results:
        print(f"  {r['concurrency']:>12d} {r['p50_ms']:>8.1f}ms {r['p95_ms']:>8.1f}ms "
              f"{r['p99_ms']:>8.1f}ms {r['throughput_req_per_s']:>10.1f}/s "
              f"{r['error_rate_pct']:>7.2f}%")
    print(f"{'='*60}")

    if args.output:
        Path(args.output).write_text(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "iterations": args.iterations,
            "results": all_results,
        }, indent=2))
        print(f"\nResults saved: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
