"""Editorial Engine API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from api.editorial.engine import EditorialEngine
from api.editorial.formats import render_markdown, render_newsletter, render_telegram
from api.editorial.schemas import (
    EditorialDigestResponse,
    EditorialDigestListResponse,
)

router = APIRouter(prefix="/editorial", tags=["editorial"])

_engine = EditorialEngine()


@router.get("/today", response_model=EditorialDigestResponse, operation_id="get_today_editorial")
async def get_today_editorial():
    """Get today's editorial digest — the top story, key findings, and clinical takeaway."""
    digest = await _engine.generate_today()
    response = EditorialDigestResponse.from_editorial_digest(digest)
    return response


@router.get("/week", response_model=EditorialDigestResponse, operation_id="get_weekly_editorial")
async def get_weekly_editorial():
    """Get this week's editorial digest."""
    digest = await _engine.generate_weekly()
    response = EditorialDigestResponse.from_editorial_digest(digest)
    return response


@router.get("/today/markdown", operation_id="get_today_editorial_markdown")
async def get_today_editorial_markdown():
    """Get today's editorial digest as Markdown (newsletter-ready)."""
    digest = await _engine.generate_today()
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=render_markdown(digest),
        media_type="text/markdown",
        headers={"Content-Disposition": "inline; filename=editorial.md"},
    )


@router.get("/today/telegram", operation_id="get_today_editorial_telegram")
async def get_today_editorial_telegram():
    """Get today's editorial digest as Telegram message."""
    digest = await _engine.generate_today()
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=render_telegram(digest),
        media_type="text/plain",
    )


@router.get("/today/newsletter", operation_id="get_today_editorial_newsletter")
async def get_today_editorial_newsletter():
    """Get today's editorial digest as HTML newsletter."""
    digest = await _engine.generate_today()
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=render_newsletter(digest))
