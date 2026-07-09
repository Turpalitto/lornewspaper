"""Tests for BaseProvider request pipeline (rate limit, retry, validation)."""

import httpx
import pytest
import respx
from pydantic import BaseModel

from search_service.base import BaseProvider
from search_service.config import ProviderCapabilities, ProviderConfig


class _StubModel(BaseModel):
    ok: str


class StubProvider(BaseProvider):
    name = "stub"
    capabilities = ProviderCapabilities()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def search(self, query, limit=20):
        return []

    async def search_by_date(self, query, from_year=None, to_year=None, limit=20):
        return []

    async def search_by_pmid(self, pmid):
        return None

    async def get_metadata(self, identifier):
        return None

    async def get_abstract(self, identifier):
        return None

    async def healthcheck(self):
        return True


def _cfg() -> ProviderConfig:
    return ProviderConfig(name="stub", base_url="https://api.test", rate=100.0, burst=100)


@respx.mock
@pytest.mark.asyncio
async def test_request_success():
    respx.get("https://api.test/search").mock(
        return_value=httpx.Response(200, json={"ok": "yes"})
    )
    p = StubProvider(_cfg())
    resp = await p._request_raw("GET", "/search")
    assert resp.status_code == 200
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_request_retries_on_500_then_succeeds():
    route = respx.get("https://api.test/flaky").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": "yes"}),
        ]
    )
    p = StubProvider(_cfg())
    resp = await p._request_raw("GET", "/flaky")
    assert resp.status_code == 200
    assert route.call_count == 2
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_request_no_retry_on_404():
    route = respx.get("https://api.test/missing").mock(
        return_value=httpx.Response(404, json={"error": "nf"})
    )
    p = StubProvider(_cfg())
    with pytest.raises(httpx.HTTPStatusError):
        await p._request_raw("GET", "/missing")
    assert route.call_count == 1  # no retry
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_validates_response_model():
    respx.get("https://api.test/bad").mock(
        return_value=httpx.Response(200, json={"wrong": "field"})
    )
    p = StubProvider(_cfg(), max_attempts=1)

    with pytest.raises(Exception):
        await p._fetch(
            endpoint="/bad",
            response_model=_StubModel,
            map_fn=lambda m: [],
        )
    await p.aclose()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_honors_retry_after():
    respx.get("https://api.test/rat").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"ok": "yes"}),
        ]
    )
    p = StubProvider(_cfg(), max_attempts=3)
    resp = await p._request_raw("GET", "/rat")
    assert resp.status_code == 200
    # Retry-After "0" -> no long pause; call still retried.
    await p.aclose()
