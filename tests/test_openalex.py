"""Tests for OpenAlexProvider via mocked REST API."""

import httpx
import pytest
import respx

from search_service.config import ProviderConfig
from search_service.providers.openalex import OpenAlexProvider


def _work(openalex_id: str = "W1", title: str = "OpenAlex Study") -> dict:
    return {
        "id": f"https://openalex.org/{openalex_id}",
        "title": title,
        "publication_year": 2021,
        "doi": "https://doi.org/10.1/W1",
        "type": "journal-article",
        "language": "en",
        "authorships": [
            {"author": {"display_name": "Smith, J"}},
            {"author": {"display_name": "Doe, K"}},
        ],
        "host_venue": {
            "display_name": "J Open",
            "publisher": "OpenPub",
            "volume": "9",
            "issue": "1",
            "pages": "1-10",
        },
        "ids": {
            "openalex": f"https://openalex.org/{openalex_id}",
            "doi": "https://doi.org/10.1/W1",
            "pmid": "123456",
            "pmcid": "PMC777",
        },
        "abstract_inverted_index": {"We": [0], "studied": [1], "cells": [2]},
        "keywords": [{"display_name": "biology"}],
        "concepts": [{"display_name": "Cell Biology"}],
        "best_oa_location": {
            "pdf_url": "https://oa/pdf/W1",
            "landing_page_url": "https://oa/W1",
            "license": "CC-BY",
        },
    }


def _cfg() -> ProviderConfig:
    return ProviderConfig(
        name="openalex",
        base_url="https://api.openalex.org",
        rate=100,
        burst=100,
        extra={"mailto": "search@example.org"},
    )


def _provider() -> OpenAlexProvider:
    return OpenAlexProvider(_cfg(), max_attempts=1)


@respx.mock
@pytest.mark.asyncio
async def test_search_maps_articles():
    respx.get(url__regex=r".*/works").mock(
        return_value=httpx.Response(
            200, json={"meta": {"count": 2}, "results": [_work("W1"), _work("W2", "Second")]}
        )
    )
    p = _provider()
    arts = await p.search("cells", limit=10)
    assert len(arts) == 2
    a = arts[0]
    assert a.title == "OpenAlex Study"
    assert a.authors == ["Smith, J", "Doe, K"]
    assert a.journal == "J Open"
    assert a.year == 2021
    assert a.doi == "https://doi.org/10.1/W1"
    assert a.pmid == "123456"
    assert a.pmcid == "PMC777"
    assert a.abstract == "We studied cells"
    assert a.keywords == ["biology"]
    assert a.mesh_terms == ["Cell Biology"]
    assert a.pdf_url == "https://oa/pdf/W1"
    assert a.url == "https://oa/W1"
    assert a.language == "en"
    assert a.publication_type == ["journal-article"]
    assert a.license == "CC-BY"
    assert a.source == "openalex"
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_date_adds_filter():
    from urllib.parse import unquote

    route = respx.get(url__regex=r".*/works").mock(
        return_value=httpx.Response(200, json={"meta": {}, "results": [_work()]})
    )
    p = _provider()
    await p.search_by_date("covid", from_year=2020, to_year=2021, limit=5)
    q = unquote(str(route.calls.last.request.url))
    assert "from_publication_date:2020-01-01" in q
    assert "to_publication_date:2021-12-31" in q
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_search_by_pmid_uses_filter():
    from urllib.parse import unquote

    route = respx.get(url__regex=r".*/works").mock(
        return_value=httpx.Response(200, json={"meta": {}, "results": [_work()]})
    )
    p = _provider()
    art = await p.search_by_pmid("123456")
    assert art is not None and art.pmid == "123456"
    assert "pmid:123456" in unquote(str(route.calls.last.request.url))
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_get_metadata_by_doi():
    from urllib.parse import unquote

    route = respx.get(url__regex=r".*/works").mock(
        return_value=httpx.Response(200, json={"meta": {}, "results": [_work()]})
    )
    p = _provider()
    art = await p.get_metadata("10.1/W1")
    assert art is not None and art.doi == "https://doi.org/10.1/W1"
    assert "doi:https://doi.org/10.1/W1" in unquote(str(route.calls.last.request.url))
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_validation_failure_raises():
    respx.get(url__regex=r".*/works").mock(
        return_value=httpx.Response(200, json={"meta": {}, "wrong": []})
    )
    p = _provider()
    with pytest.raises(Exception):
        await p.search("x", limit=1)
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_healthcheck():
    respx.get(url__regex=r".*/works").mock(return_value=httpx.Response(200, json={"meta": {}, "results": []}))
    p = _provider()
    assert await p.healthcheck() is True
    await p.aclose()
