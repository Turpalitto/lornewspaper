"""Tests for SearchService fan-out, dedupe integration and partial failures."""

import pytest

from search_service.models import Article
from search_service.service import SearchService
from tests.stubs import StubProvider


def _art(source: str, doi: str | None = None, title: str = "T") -> Article:
    return Article(source=source, provenance=[source], doi=doi, title=title, pmid=None)


@pytest.mark.asyncio
async def test_search_all_merges_across_providers():
    p1 = StubProvider([_art("pubmed", "10.1/x", "Same Work")], name="pubmed")
    p2 = StubProvider([_art("europepmc", "10.1/x", "Same Work")], name="europepmc")
    svc = SearchService(providers=[p1, p2])
    results = await svc.search_all("query", limit=10)
    assert len(results) == 1
    merged = results[0]
    assert merged.doi == "10.1/x"
    assert set(merged.provenance) == {"pubmed", "europepmc"}
    await svc.aclose()


@pytest.mark.asyncio
async def test_search_all_isolates_provider_failure():
    good = StubProvider([_art("pubmed", "10.1/a")], name="pubmed")
    bad = StubProvider([], fail=True, name="europepmc")
    svc = SearchService(providers=[good, bad])
    results = await svc.search_all("query")
    # Only the good provider's result survives; no exception propagates.
    assert len(results) == 1
    assert results[0].source == "pubmed"
    await svc.aclose()


@pytest.mark.asyncio
async def test_search_by_provider_single_source():
    p = StubProvider([_art("pubmed", "10.1/a")], name="pubmed")
    svc = SearchService(providers=[p])
    results = await svc.search_by_provider("query", "pubmed")
    assert len(results) == 1
    await svc.aclose()


@pytest.mark.asyncio
async def test_search_by_provider_unknown_raises():
    svc = SearchService(providers=[StubProvider(name="pubmed")])
    with pytest.raises(ValueError):
        await svc.search_by_provider("q", "nonexistent")
    await svc.aclose()


@pytest.mark.asyncio
async def test_search_by_pmid_merges():
    p1 = StubProvider([_art("pubmed", "10.1/x", "Work")], name="pubmed")
    p2 = StubProvider([_art("openalex", "10.1/x", "Work")], name="openalex")
    svc = SearchService(providers=[p1, p2])
    results = await svc.search_by_pmid("12345")
    assert len(results) == 1
    assert set(results[0].provenance) == {"pubmed", "openalex"}
    await svc.aclose()


@pytest.mark.asyncio
async def test_concurrency_limit_respected():
    from tests.stubs import ConcurrencyCounter

    counter = ConcurrencyCounter()
    providers = [
        StubProvider([], delay=0.05, counter=counter, name=f"p{i}") for i in range(6)
    ]
    svc = SearchService(settings=_limit_settings(2), providers=providers)
    await svc.search_all("q")
    assert counter.max <= 2
    await svc.aclose()


def _limit_settings(limit: int):
    from search_service.config import Settings, default_settings

    s = default_settings()
    s.concurrency_limit = limit
    return s
