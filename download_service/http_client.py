"""Shared httpx.AsyncClient for DownloadService."""

from __future__ import annotations

import httpx

from download_service.config import Settings


def create_client(settings: Settings) -> httpx.AsyncClient:
    pdf_cfg = settings.downloaders.get("pdf")
    timeout = pdf_cfg.timeout if pdf_cfg else 30.0
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
        limits=httpx.Limits(max_connections=settings.max_concurrent),
    )
