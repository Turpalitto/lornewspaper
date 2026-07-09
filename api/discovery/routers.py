"""Content Discovery Engine API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.discovery.engine import ContentDiscoveryEngine
from api.discovery.schemas import (
    AuthorResponse, DiscoveryResultResponse, JournalInfoResponse,
    NewDevelopmentsResponse, TrendTopicResponse,
)

router = APIRouter(prefix="/discovery", tags=["discovery"])

_engine = ContentDiscoveryEngine()


@router.get("/today", response_model=DiscoveryResultResponse, operation_id="get_today_discovery")
async def get_today_discovery():
    """Run all discovery strategies and return today's results."""
    result = await _engine.discover_today()
    return DiscoveryResultResponse.from_result(result)


@router.get("/trending", response_model=list[TrendTopicResponse], operation_id="get_trending_topics")
async def get_trending_topics():
    """Get currently trending ENT research topics."""
    topics = _engine.get_trending_topics()
    return [TrendTopicResponse.from_trend(t) for t in topics]


@router.get("/emerging", response_model=list[TrendTopicResponse], operation_id="get_emerging_topics")
async def get_emerging_topics():
    """Get newly emerging ENT research topics."""
    topics = _engine.get_emerging_topics()
    return [TrendTopicResponse.from_trend(t) for t in topics]


@router.get("/authors", response_model=list[AuthorResponse], operation_id="get_top_authors")
async def get_top_authors():
    """Get top ENT researchers by recent publication count."""
    result = await _engine.get_latest()
    if not result:
        return []
    return [AuthorResponse.from_author(a) for a in result.new_authors]


@router.get("/journals", response_model=list[JournalInfoResponse], operation_id="get_top_journals")
async def get_top_journals():
    """Get top ENT journals by publication volume."""
    result = await _engine.get_latest()
    if not result:
        return []
    return [JournalInfoResponse.from_journal(j) for j in result.top_journals]


@router.get("/developments", response_model=NewDevelopmentsResponse, operation_id="get_new_developments")
async def get_new_developments():
    """Get new procedures, devices, drugs, and techniques detected."""
    from api.discovery.trend_analysis import TrendAnalyzer
    result = await _engine.get_latest()
    if not result:
        return NewDevelopmentsResponse()
    analyzer = TrendAnalyzer()
    trends = analyzer.analyze(result.items)
    return NewDevelopmentsResponse(**trends)
