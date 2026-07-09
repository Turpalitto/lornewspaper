"""Security middleware: headers, trusted hosts, basic rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Add security headers to every response."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message.get("headers", []))
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["X-XSS-Protection"] = "0"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                headers["Permissions-Policy"] = (
                    "camera=(), microphone=(), geolocation=()"
                )
                headers["Strict-Transport-Security"] = (
                    "max-age=63072000; includeSubDomains; preload"
                )
                message["headers"] = headers.raw
            await send(message)

        await self.app(scope, receive, send_with_headers)


class TrustedHostMiddleware:
    """Reject requests with untrusted Host headers."""

    def __init__(self, app: ASGIApp, allowed_hosts: list[str] | None = None):
        self.app = app
        self.allowed_hosts = allowed_hosts or ["*"]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "*" not in self.allowed_hosts:
            host = None
            for key, value in scope.get("headers", []):
                if key.lower() == b"host":
                    host = value.decode().split(":")[0]
                    break
            if host and host not in self.allowed_hosts:
                resp = PlainTextResponse("Invalid Host header", status_code=400)
                await resp(scope, receive, send)
                return

        await self.app(scope, receive, send)


class InMemoryRateLimiter:
    """Simple in-memory sliding window rate limiter.

    Not suitable for multi-process deployments — use Redis in production.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self._window
        self._attempts[key] = [
            t for t in self._attempts[key] if t > window_start
        ]
        if len(self._attempts[key]) >= self._max:
            return False
        self._attempts[key].append(now)
        return True


class RateLimitMiddleware:
    """Rate limit based on client IP."""

    def __init__(self, app: ASGIApp, max_requests: int = 60, window_seconds: int = 60):
        self.app = app
        self._limiter = InMemoryRateLimiter(max_requests, window_seconds)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = scope.get("client", ("",))[0] or "unknown"
        if not self._limiter.is_allowed(client_ip):
            resp = JSONResponse(
                content={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Try again later.",
                    "details": {},
                    "request_id": "",
                },
                status_code=429,
                headers={"Retry-After": "60"},
            )
            await resp(scope, receive, send)
            return

        await self.app(scope, receive, send)
