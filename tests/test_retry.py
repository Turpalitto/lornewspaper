"""Tests for the transient-only async retry decorator."""


import httpx
import pytest

from search_service.retry import TransientHTTPError, _parse_retry_after, async_retry


async def _no_sleep(_seconds: float) -> None:
    return None


@pytest.mark.asyncio
async def test_retry_transient_5xx_then_success():
    calls = {"n": 0}

    @async_retry(max_attempts=4, sleep=_no_sleep)
    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            req = httpx.Request("GET", "http://x")
            resp = httpx.Response(503, request=req)
            raise TransientHTTPError(resp, req)
        return "ok"

    result = await flaky()
    assert result == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_retry_on_network_error():
    calls = {"n": 0}

    @async_retry(max_attempts=3, sleep=_no_sleep)
    async def net_err():
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("boom", request=httpx.Request("GET", "http://x"))
        return "ok"

    assert await net_err() == "ok"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_no_retry_on_404():
    calls = {"n": 0}

    @async_retry(max_attempts=5, sleep=_no_sleep)
    async def not_found():
        calls["n"] += 1
        req = httpx.Request("GET", "http://x")
        resp = httpx.Response(404, request=req)
        # Non-transient: raise plain HTTPStatusError (not TransientHTTPError).
        raise httpx.HTTPStatusError("nf", request=req, response=resp)

    with pytest.raises(httpx.HTTPStatusError):
        await not_found()
    assert calls["n"] == 1  # no retries


@pytest.mark.asyncio
async def test_retry_respects_retry_after():
    # Retry-After is honoured by the rate limiter (it pauses the bucket), not by
    # tenacity's sleep. Here we verify the value is parsed and the call is
    # retried on 429.
    sleeps: list[float] = []

    async def _record(_s: float) -> None:
        sleeps.append(_s)

    @async_retry(max_attempts=2, sleep=_record)
    async def with_retry_after():
        req = httpx.Request("GET", "http://x")
        resp = httpx.Response(429, headers={"Retry-After": "7"}, request=req)
        raise TransientHTTPError(resp, req)

    with pytest.raises(TransientHTTPError):
        await with_retry_after()
    # A retry was attempted (call #2) and the Retry-After header was parsed.
    assert len(sleeps) == 1
    assert TransientHTTPError(
        httpx.Response(429, headers={"Retry-After": "7"}, request=httpx.Request("GET", "http://x")),
        httpx.Request("GET", "http://x"),
    ).retry_after == 7.0


def test_parse_retry_after_seconds():
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(429, headers={"Retry-After": "12"}, request=req)
    assert _parse_retry_after(resp) == 12.0


def test_parse_retry_after_missing():
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(429, request=req)
    assert _parse_retry_after(resp) is None
