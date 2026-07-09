"""Resilience tests: timeout, retry, and rate limiting at the provider level."""

import time

import httpx
import pytest

from search_service.config import ProviderConfig
from search_service.providers.pubmed import PubMedProvider


def _pubmed_client(handler, timeout: float = 5.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=timeout)


def _cfg(rate: float = 100.0, burst: int = 100) -> ProviderConfig:
    return ProviderConfig(name="pubmed", base_url="http://test", rate=rate, burst=burst)


@pytest.mark.asyncio
async def test_provider_timeout_surfaces():
    # MockTransport ignores real timeouts, so simulate the timeout exception
    # the client would raise on a slow upstream (still transient -> retried).
    async def handler(request):
        raise httpx.ReadTimeout("too slow", request=request)

    client = _pubmed_client(handler)
    p = PubMedProvider(_cfg(), client=client, max_attempts=1)
    with pytest.raises(httpx.TimeoutException):
        await p.search("q")
    await client.aclose()


@pytest.mark.asyncio
async def test_provider_retries_transient_then_succeeds():
    state = {"n": 0}

    async def handler(request):
        state["n"] += 1
        if state["n"] < 3:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={"esearchresult": {"idlist": []}})

    client = _pubmed_client(handler)
    p = PubMedProvider(_cfg(), client=client, max_attempts=4)
    result = await p.search("q")
    assert result == []
    assert state["n"] == 3  # two failures retried, third succeeds
    await client.aclose()


@pytest.mark.asyncio
async def test_rate_limiter_paces_requests():
    async def handler(request):
        return httpx.Response(200, json={})

    client = _pubmed_client(handler)
    # burst=1, rate=4 -> ~0.25s between tokens; generous lower bound.
    p = PubMedProvider(_cfg(rate=4.0, burst=1), client=client)

    starts = []
    for _ in range(3):
        starts.append(time.monotonic())
        await p._request_raw("GET", "/x")
    gaps = [starts[i + 1] - starts[i] for i in range(2)]
    # First call is instant (burst token); subsequent calls are paced ~0.25s.
    assert max(gaps) >= 0.15
    await client.aclose()
