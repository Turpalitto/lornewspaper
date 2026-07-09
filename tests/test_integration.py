"""End-to-end integration test exercising all three real providers behind
SearchService with every upstream mocked via respx (no network). Also a
lightweight performance/concurrency assertion.
"""

import asyncio

import httpx
import pytest
import respx

from search_service.config import Settings, default_settings
from search_service.models import Article
from search_service.service import SearchService
from tests.stubs import ConcurrencyCounter, StubProvider


def _pubmed_esearch():
    return httpx.Response(200, json={"esearchresult": {"idlist": ["100"]}})


def _pubmed_efetch():
    return httpx.Response(
        200,
        json={
            "result": {
                "uids": ["100"],
                "100": {
                    "title": "Shared Paper",
                    "fulljournalname": "J Int",
                    "pubdate": "2022",
                    "authors": [{"name": "Pubmed A"}],
                    "articleids": [
                        {"idtype": "pubmed", "value": "100"},
                        {"idtype": "doi", "value": "10.1/shared"},
                        {"idtype": "pmc", "value": "PMC100"},
                    ],
                    "abstracttext": "From PubMed.",
                    "keywords": ["pk"],
                    "meshterms": ["pm"],
                },
            }
        },
    )


def _europepmc():
    return httpx.Response(
        200,
        json={
            "resultList": {
                "result": [
                    {
                        "title": "Shared Paper",
                        "authorString": "EP A.",
                        "journalInfo": {"journal": {"title": "J Int"}, "year": "2022"},
                        "doi": "10.1/shared",
                        "pmid": "100",
                        "pmcid": "PMC100",
                        "abstractText": "From Europe PMC.",
                        "keywordList": {"keyword": [{"value": "ek"}]},
                    }
                ]
            }
        },
    )


def _openalex():
    return httpx.Response(
        200,
        json={
            "meta": {},
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "Shared Paper",
                    "publication_year": 2022,
                    "doi": "https://doi.org/10.1/shared",
                    "authorships": [{"author": {"display_name": "OA A"}}],
                    "host_venue": {"display_name": "J Int"},
                    "ids": {"doi": "https://doi.org/10.1/shared", "pmid": "100", "pmcid": "PMC100"},
                    "abstract_inverted_index": {"OA": [0], "abstract": [1]},
                    "keywords": [{"display_name": "ok"}],
                }
            ],
        },
    )


@respx.mock
@pytest.mark.asyncio
async def test_search_all_integrates_all_providers():
    respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch())
    respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch())
    respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(return_value=_europepmc())
    respx.get(url__regex=r".*/api\.openalex\.org/works").mock(return_value=_openalex())

    svc = SearchService()
    results = await svc.search_all("Shared Paper", limit=10)
    await svc.aclose()

    # All three providers describe the same work (shared DOI) -> one merged record.
    assert len(results) == 1
    merged = results[0]
    assert merged.doi == "10.1/shared"
    assert merged.title == "Shared Paper"
    # Provenance from all three sources is preserved.
    assert set(merged.provenance) == {"pubmed", "europepmc", "openalex"}
    # List fields are unioned.
    assert "pk" in merged.keywords and "ek" in merged.keywords and "ok" in merged.keywords
    # At least one provider supplied an abstract.
    assert merged.abstract is not None


@respx.mock
@pytest.mark.asyncio
async def test_search_all_partial_provider_failure():
    # Only PubMed responds; the other two error out. Search still succeeds.
    respx.get(url__regex=r".*/esearch\.fcgi").mock(return_value=_pubmed_esearch())
    respx.get(url__regex=r".*/efetch\.fcgi").mock(return_value=_pubmed_efetch())
    respx.get(url__regex=r".*/europepmc/webservices/rest/search").mock(
        return_value=httpx.Response(500)
    )
    respx.get(url__regex=r".*/api\.openalex\.org/works").mock(return_value=httpx.Response(503))

    svc = SearchService()
    results = await svc.search_all("x", limit=5)
    await svc.aclose()
    assert len(results) == 1
    assert results[0].source == "pubmed"


@pytest.mark.asyncio
async def test_performance_concurrency_bounded():
    settings = default_settings()
    settings.concurrency_limit = 3
    counter = ConcurrencyCounter()
    providers = [
        StubProvider([Article(source=f"p{i}", provenance=[f"p{i}"], title="T")],
                     delay=0.05, counter=counter, name=f"p{i}")
        for i in range(9)
    ]
    svc = SearchService(settings=settings, providers=providers)
    await svc.search_all("query")
    await svc.aclose()
    # 9 providers, limit 3 -> never more than 3 in flight.
    assert counter.max <= 3


@pytest.mark.asyncio
async def test_search_all_completes_quickly():
    # Sanity: merging many small result sets is fast.
    providers = [
        StubProvider(
            [Article(source=f"p{i}", provenance=[f"p{i}"], title=f"Paper {i*100+j} unique subject") for j in range(5)],
            name=f"p{i}",
        )
        for i in range(5)
    ]
    svc = SearchService(providers=providers)
    start = asyncio.get_event_loop().time()
    results = await svc.search_all("q")
    elapsed = asyncio.get_event_loop().time() - start
    await svc.aclose()
    assert len(results) == 25
    assert elapsed < 2.0
