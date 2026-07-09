"""Tests for all resolvers (PMC, DOI, Publisher)."""

import httpx
import pytest
import respx

from download_service.config import Settings
from download_service.resolvers.doi import DOIResolver
from download_service.resolvers.pmc import PMCResolver
from download_service.resolvers.publisher import PublisherResolver
from search_service.models import Article


def _settings() -> Settings:
    return Settings()


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@pytest.mark.asyncio
async def test_pmc_resolver_returns_pdf_and_xml():
    article = Article(source="pubmed", title="Test", pmcid="PMC12345")
    r = PMCResolver(_client(), _settings())
    cands = await r.resolve(article)
    urls = [c.url for c in cands]
    assert any("/PMC12345/pdf/" in u for u in urls)
    assert any("efetch.fcgi" in u for u in urls)
    await _client().aclose()


@pytest.mark.asyncio
async def test_pmc_resolver_empty_when_no_pmcid():
    article = Article(source="pubmed", title="Test")
    r = PMCResolver(_client(), _settings())
    cands = await r.resolve(article)
    assert cands == []


@respx.mock
@pytest.mark.asyncio
async def test_doi_resolver_follows_redirect_to_pdf():
    doi_url = "https://doi.org/10.1/xyz"
    respx.head(doi_url).mock(
        return_value=httpx.Response(302, headers={"Location": "https://dl.example/paper.pdf"})
    )
    respx.head("https://dl.example/paper.pdf").mock(
        return_value=httpx.Response(200, headers={"content-type": "application/pdf"})
    )
    article = Article(source="pubmed", doi="10.1/xyz")
    r = DOIResolver(_client(), _settings())
    cands = await r.resolve(article)
    assert len(cands) == 1
    assert cands[0].mime_type == "application/pdf"
    assert cands[0].url == "https://dl.example/paper.pdf"


@respx.mock
@pytest.mark.asyncio
async def test_doi_resolver_no_doi_returns_empty():
    article = Article(source="pubmed", title="Test")
    r = DOIResolver(_client(), _settings())
    cands = await r.resolve(article)
    assert cands == []


@respx.mock
@pytest.mark.asyncio
async def test_publisher_resolver_returns_pdf_url():
    article = Article(
        source="pubmed",
        title="Test",
        pdf_url="https://pub.example/paper.pdf",
        url="https://pub.example/landing",
    )
    r = PublisherResolver(_client(), _settings())
    cands = await r.resolve(article)
    assert len(cands) == 2
    assert cands[0].mime_type == "application/pdf"
    assert cands[1].mime_type == "text/html"


@respx.mock
@pytest.mark.asyncio
async def test_publisher_resolver_empty_when_no_urls():
    article = Article(source="pubmed", title="Test")
    r = PublisherResolver(_client(), _settings())
    cands = await r.resolve(article)
    assert cands == []
