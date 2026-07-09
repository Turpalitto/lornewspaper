"""Tests for EuropePMCProvider via mocked REST API."""

from urllib.parse import unquote

import httpx
import pytest
import respx

from search_service.config import ProviderConfig
from search_service.providers.europepmc import EuropePMCProvider


def _record(pmid: str = "12345", title: str = "Example Title") -> dict:
    return {
        "title": title,
        "authorString": "Smith J, Doe K.",
        "journalInfo": {
            "journal": {"title": "J Example", "publisher": "Pub"},
            "year": "2021",
            "volume": "12",
            "issue": "3",
        },
        "pubYear": "2021",
        "doi": f"10.1/{pmid}",
        "pmid": pmid,
        "pmcid": f"PMC{pmid}",
        "abstractText": "An abstract here.",
        "keywordList": {"keyword": [{"value": "kw1"}, {"value": "kw2"}]},
        "meshTermList": {"meshTerm": [{"term": "Mesh1"}]},
        "fullTextUrlList": {
            "fullTextUrl": [{"documentStyle": "PDF", "url": f"https://pdf/{pmid}", "availability": "Free"}]
        },
        "language": "eng",
        "pubType": "Journal Article",
        "pageInfo": "100-110",
        "license": "CC-BY",
    }


def _cfg() -> ProviderConfig:
    return ProviderConfig(name="europepmc", base_url="https://www.ebi.ac.uk/europepmc/webservices/rest", rate=100, burst=100)


def _provider() -> EuropePMCProvider:
    return EuropePMCProvider(_cfg(), max_attempts=1)


@respx.mock
@pytest.mark.asyncio
async def test_search_maps_articles():
    respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(
            200, json={"resultList": {"result": [_record("1"), _record("2", "Second")]}}
        )
    )
    p = _provider()
    arts = await p.search("cancer", limit=10)
    assert len(arts) == 2
    a = arts[0]
    assert a.pmid == "1"
    assert a.doi == "10.1/1"
    assert a.pmcid == "PMC1"
    assert a.authors == ["Smith J", "Doe K."]
    assert a.journal == "J Example"
    assert a.year == 2021
    assert a.volume == "12"
    assert a.issue == "3"
    assert a.abstract == "An abstract here."
    assert a.keywords == ["kw1", "kw2"]
    assert a.mesh_terms == ["Mesh1"]
    assert a.pdf_url == "https://pdf/1"
    assert a.language == "eng"
    assert a.publication_type == ["Journal Article"]
    assert a.license == "CC-BY"
    assert a.source == "europepmc"
    assert a.provenance == ["europepmc"]
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_date_appends_year_filter():
    route = respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(200, json={"resultList": {"result": [_record("1")]}})
    )
    p = _provider()
    await p.search_by_date("covid", from_year=2020, to_year=2021, limit=5)
    req = route.calls.last.request
    assert "PUBLICATION_YEAR:2020-2021" in unquote(str(req.url))
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_pmid_uses_ext_id():
    route = respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(200, json={"resultList": {"result": [_record("555")]}})
    )
    p = _provider()
    art = await p.search_by_pmid("555")
    assert art is not None
    assert art.pmid == "555"
    assert "EXT_ID:555" in unquote(str(route.calls.last.request.url))
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_get_metadata_by_doi():
    route = respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(200, json={"resultList": {"result": [_record("7")]}})
    )
    p = _provider()
    art = await p.get_metadata("10.1/7")
    assert art is not None and art.doi == "10.1/7"
    assert 'DOI:"10.1/7"' in unquote(str(route.calls.last.request.url))
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_validation_failure_raises():
    respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(200, json={"wrong": []})
    )
    p = _provider()
    with pytest.raises(Exception):
        await p.search("x", limit=1)
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_healthcheck():
    respx.get(url__regex=r".*/search").mock(return_value=httpx.Response(200, json={"resultList": {"result": []}}))
    p = _provider()
    assert await p.healthcheck() is True
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_date_single_bound():
    from urllib.parse import unquote

    route = respx.get(url__regex=r".*/search").mock(
        return_value=httpx.Response(200, json={"resultList": {"result": [_record("1")]}})
    )
    p = _provider()
    # Only a lower bound -> >= filter, not a range.
    await p.search_by_date("covid", from_year=2020, to_year=None, limit=5)
    q = unquote(str(route.calls.last.request.url))
    assert "PUBLICATION_YEAR:>=2020" in q
    assert "PUBLICATION_YEAR:2020-" not in q
    await p.aclose()
