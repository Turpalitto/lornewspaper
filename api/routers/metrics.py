"""Prometheus metrics endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])

_uptime_start = time.monotonic()
_request_count: int = 0
_request_duration_sum: float = 0.0


def record_request(duration_seconds: float) -> None:
    global _request_count, _request_duration_sum
    _request_count += 1
    _request_duration_sum += duration_seconds


@router.get("/metrics")
async def metrics(_request: Request):
    uptime = time.monotonic() - _uptime_start
    avg_duration = 0.0
    if _request_count > 0:
        avg_duration = _request_duration_sum / _request_count

    lines = [
        "# HELP lornews_uptime_seconds Application uptime",
        "# TYPE lornews_uptime_seconds gauge",
        f"lornews_uptime_seconds {uptime:.2f}",
        "",
        "# HELP lornews_requests_total Total HTTP requests",
        "# TYPE lornews_requests_total counter",
        f"lornews_requests_total {_request_count}",
        "",
        "# HELP lornews_request_duration_seconds Average request duration",
        "# TYPE lornews_request_duration_seconds gauge",
        f"lornews_request_duration_seconds {avg_duration:.4f}",
        "",
    ]

    return PlainTextResponse(content="\n".join(lines), media_type="text/plain; charset=utf-8")
