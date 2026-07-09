"""Async token-bucket rate limiter.

Per-provider limiter throttles outgoing requests to ``rate`` req/s with a
``burst`` capacity. It is ``Retry-After`` aware: when a provider returns 429
the caller can ``pause`` the bucket for the server-requested duration.
"""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Token-bucket limiter.

    ``rate`` is tokens replenished per second; ``burst`` is the maximum
    tokens held. ``acquire`` blocks until a token is available, so callers
    naturally spread out and never exceed the server's published limit.
    """

    def __init__(self, rate: float = 3.0, burst: int = 5) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if burst < 1:
            raise ValueError("burst must be >= 1")
        self._rate = float(rate)
        self._burst = float(burst)
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()
        # Extra penalty seconds applied when a server asks us to back off.
        self._penalty_until = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                # Apply externally mandated backoff (Retry-After) first.
                if now < self._penalty_until:
                    wait = self._penalty_until - now
                    await asyncio.sleep(wait)
                    continue
                elapsed = now - self._updated
                self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                deficit = 1.0 - self._tokens
                await asyncio.sleep(deficit / self._rate)

    def pause(self, seconds: float) -> None:
        """Extend the backoff window by ``seconds`` (e.g. from Retry-After)."""
        if seconds <= 0:
            return
        now = time.monotonic()
        self._penalty_until = max(self._penalty_until, now) + float(seconds)

    async def wait_for(self, seconds: float) -> None:
        """Cooperative wait used by tests / manual throttling."""
        if seconds > 0:
            await asyncio.sleep(seconds)
