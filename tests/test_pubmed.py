"""Tests for PubMedProvider via mocked E-utilities."""

import httpx
import pytest
import respx

from search_service.config import ProviderConfig
from search_service.providers.pubmed import PubMedProvider


def _record(uid: str, title: str = "Example Study") -> dict:
    return {
        "uid": uid,
        "title": title,
        "fulljournalname": "J Example",
        "source": "J Example",
        "pubdate": "2022 Jan-Feb",
        "authors": [{"name": "Smith J", "authtype": "Author"}],
        "articleids": [
            {"idtype": "pubmed", "value": uid},
            {"idtype": "doi", "value": f"10.1/{uid}"},
            {"idtype": "pmc", "value": f"PMC{uid}"},
        ],
        "abstracttext": "This is the abstract.",
        "keywords": ["kw1", "kw2"],
        "meshterms": ["MeSH1", "MeSH2"],
        "fulltexturl": [{"content": "pdf", "url": f"https://pdf/{uid}", "availability": "Free"}],
        "lang": ["eng"],
        "pubtype": ["Journal Article"],
        "publishername": "Pub",
        "volume": "5",
        "issue": "2",
        "pages": "100-110",
    }


def _cfg() -> ProviderConfig:
    return ProviderConfig(name="pubmed", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils", rate=100, burst=100)


def _provider() -> PubMedProvider:
    return PubMedProvider(_cfg(), max_attempts=1)


@respx.mock
@pytest.mark.asyncio
async def test_search_returns_mapped_articles():
    respx.get(url__regex=r".*/esearch\.fcgi").mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["123", "456"]}})
    )
    respx.get(url__regex=r".*/efetch\.fcgi").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "uids": ["123", "456"],
                    "123": _record("123"),
                    "456": _record("456", "Other"),
                }
            },
        )
    )
    p = _provider()
    arts = await p.search("cancer", limit=10)
    assert len(arts) == 2
    a = arts[0]
    assert a.pmid == "123"
    assert a.doi == "10.1/123"
    assert a.pmcid == "PMC123"
    assert a.title == "Example Study"
    assert a.authors == ["Smith J"]
    assert a.year == 2022
    assert a.abstract == "This is the abstract."
    assert a.keywords == ["kw1", "kw2"]
    assert a.mesh_terms == ["MeSH1", "MeSH2"]
    assert a.pdf_url == "https://pdf/123"
    assert a.url == "https://pubmed.ncbi.nlm.nih.gov/123/"
    assert a.source == "pubmed"
    assert a.provenance == ["pubmed"]
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_date_sets_datetype():
    route = respx.get(url__regex=r".*/esearch\.fcgi").mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["1"]}})
    )
    respx.get(url__regex=r".*/efetch\.fcgi").mock(
        return_value=httpx.Response(200, json={"result": {"uids": ["1"], "1": _record("1")}})
    )
    p = _provider()
    arts = await p.search_by_date("covid", from_year=2020, to_year=2021, limit=5)
    assert len(arts) == 1
    req = route.calls.last.request
    assert "datetype=pdat" in str(req.url)
    assert "mindate=2020" in str(req.url)
    assert "maxdate=2021" in str(req.url)
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_get_abstract():
    respx.get(url__regex=r".*/esearch\.fcgi").mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["9"]}})
    )
    respx.get(url__regex=r".*/efetch\.fcgi").mock(
        return_value=httpx.Response(200, json={"result": {"uids": ["9"], "9": _record("9")}})
    )
    p = _provider()
    abstract = await p.get_abstract("9")
    assert abstract == "This is the abstract."
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_validation_failure_raises():
    respx.get(url__regex=r".*/esearch\.fcgi").mock(
        return_value=httpx.Response(200, json={"esearchresult": {"idlist": ["1"]}})
    )
    # efetch returns a shape missing "result" -> pydantic validation fails.
    respx.get(url__regex=r".*/efetch\.fcgi").mock(
        return_value=httpx.Response(200, json={"wrong": "shape"})
    )
    p = _provider()
    with pytest.raises(Exception):
        await p.search("x", limit=1)
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_healthcheck_true_and_false():
    respx.get(url__regex=r".*/einfo\.fcgi").mock(
        return_value=httpx.Response(200, json={"einforesult": {"dbname": "pubmed"}})
    )
    p = _provider()
    assert await p.healthcheck() is True
    await p.aclose()

    respx.get(url__regex=r".*/einfo\.fcgi").mock(
        return_value=httpx.Response(503)
    )
    p2 = _provider()
    assert await p2.healthcheck() is False
    await p2.aclose()
