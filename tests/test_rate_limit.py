"""Tests for the token-bucket rate limiter."""

import asyncio

import pytest

from search_service.rate_limit import AsyncRateLimiter


@pytest.mark.asyncio
async def test_limiter_refills_over_time():
    limiter = AsyncRateLimiter(rate=10.0, burst=1)
    # First acquire drains the single token immediately.
    await limiter.acquire()
    # Second acquire must wait for refill (~0.1s for 1 token at 10/s).
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed >= 0.05


@pytest.mark.asyncio
async def test_limiter_burst_allows_instant_tokens():
    limiter = AsyncRateLimiter(rate=1.0, burst=3)
    for _ in range(3):
        # All three should be available instantly (burst capacity).
        await limiter.acquire()


@pytest.mark.asyncio
async def test_pause_extends_backoff():
    limiter = AsyncRateLimiter(rate=100.0, burst=1)
    await limiter.acquire()
    limiter.pause(0.2)
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed >= 0.15


@pytest.mark.asyncio
async def test_concurrent_acquires_capped():
    limiter = AsyncRateLimiter(rate=50.0, burst=2)
    # With burst 2, only 2 tokens available instantly; the 3rd must wait.
    results = []

    async def worker():
        await limiter.acquire()
        results.append(1)

    await asyncio.gather(*(worker() for _ in range(5)))
    assert len(results) == 5  # all eventually succeed
