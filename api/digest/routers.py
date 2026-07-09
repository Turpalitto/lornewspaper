"""Daily Digest API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from api.digest.generator import DigestGenerator
from api.digest.models import DigestPeriod, ENTSubspecialty
from api.digest.schemas import (
    DigestItemResponse,
    DigestResponse,
    DigestListResponse,
    TopicResponse,
    TrendingResponse,
)

router = APIRouter(prefix="/digest", tags=["digest"])

_generator = DigestGenerator()


@router.get("/today", response_model=DigestResponse, operation_id="get_today_digest")
async def get_today_digest():
    """Get today's ENT literature digest."""
    digest = await _generator.generate_daily()
    return DigestResponse.from_digest(digest)


@router.get("/week", response_model=DigestResponse, operation_id="get_weekly_digest")
async def get_weekly_digest():
    """Get this week's ENT literature digest."""
    digest = await _generator.generate_weekly()
    return DigestResponse.from_digest(digest)


@router.get("/month", response_model=DigestResponse, operation_id="get_monthly_digest")
async def get_monthly_digest():
    """Get this month's ENT literature digest."""
    digest = await _generator.generate_monthly()
    return DigestResponse.from_digest(digest)


@router.get("/topic/{topic_name}", response_model=TopicResponse, operation_id="get_topic_digest")
async def get_topic_digest(topic_name: str):
    """Get digest for a specific ENT subspecialty topic."""
    try:
        topic = ENTSubspecialty(topic_name)
    except ValueError:
        valid = [t.value for t in ENTSubspecialty]
        raise HTTPException(
            status_code=404,
            detail=f"Unknown topic '{topic_name}'. Valid: {', '.join(valid)}",
        )

    digest = await _generator.generate_daily()
    for t in digest.topics:
        if t.id == topic:
            return TopicResponse.from_topic(t)

    return TopicResponse(id=topic.value, display_name=topic.value)


@router.get("/trending", response_model=TrendingResponse, operation_id="get_trending_papers")
async def get_trending_papers(limit: int = 10):
    """Get trending papers across all topics."""
    items = _generator.get_trending_papers(limit=limit)
    return TrendingResponse(
        items=[DigestItemResponse.from_digest_item(i) for i in items],
        total=len(items),
    )
