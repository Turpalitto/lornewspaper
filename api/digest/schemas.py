"""Pydantic schemas for digest API."""

from __future__ import annotations

from datetime import date, datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from api.digest.models import (
    Digest, DigestItem, DigestPeriod, ENTSubspecialty,
    ENT_TOPIC_DISPLAY, ENT_ICONS, Topic,
)


class DigestItemResponse(BaseModel):
    id: str
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    abstract: str = ""
    clinical_relevance: str = ""
    novelty: str = ""
    study_design: str = ""
    evidence_level: str = ""
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    clinical_takeaway: str = ""
    summary_bullets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    clinical_importance: float = 0.0

    @classmethod
    def from_digest_item(cls, item: DigestItem) -> DigestItemResponse:
        return cls(
            id=item.id,
            title=item.title,
            authors=item.authors,
            journal=item.journal,
            publication_date=item.publication_date.isoformat() if item.publication_date else "",
            doi=item.doi,
            abstract=item.abstract[:500] if item.abstract else "",
            clinical_relevance=item.clinical_relevance,
            novelty=item.novelty,
            study_design=item.study_design.value if item.study_design else "",
            evidence_level=item.evidence_level.value if item.evidence_level else "",
            strengths=item.strengths,
            limitations=item.limitations,
            clinical_takeaway=item.clinical_takeaway,
            summary_bullets=item.summary_bullets,
            tags=item.tags,
            topics=[t.value for t in item.topics],
            clinical_importance=item.clinical_importance,
        )


class TopicResponse(BaseModel):
    id: str = ""
    display_name: str = ""
    icon: str = ""
    paper_count: int = 0
    summary: str = ""
    items: list[DigestItemResponse] = Field(default_factory=list)

    @classmethod
    def from_topic(cls, topic: Topic) -> TopicResponse:
        return cls(
            id=topic.id.value if topic.id else "",
            display_name=topic.display_name,
            icon=topic.icon,
            paper_count=topic.paper_count,
            summary=topic.summary,
            items=[DigestItemResponse.from_digest_item(i) for i in topic.items],
        )


class DigestResponse(BaseModel):
    id: str = ""
    period: str = ""
    date: str = ""
    title: str = ""
    topics: list[TopicResponse] = Field(default_factory=list)
    items: list[DigestItemResponse] = Field(default_factory=list)
    total_papers: int = 0
    trending: list[DigestItemResponse] = Field(default_factory=list)
    generated_at: str = ""

    @classmethod
    def from_digest(cls, digest: Digest) -> DigestResponse:
        return cls(
            id=digest.id,
            period=digest.period.value if digest.period else "",
            date=digest.date.isoformat() if digest.date else "",
            title=digest.title,
            topics=[TopicResponse.from_topic(t) for t in digest.topics],
            items=[DigestItemResponse.from_digest_item(i) for i in digest.items],
            total_papers=digest.total_papers,
            trending=[DigestItemResponse.from_digest_item(i) for i in digest.trending],
            generated_at=digest.generated_at.isoformat() if digest.generated_at else "",
        )


class DigestListResponse(BaseModel):
    items: list[DigestResponse] = Field(default_factory=list)
    total: int = 0


class TrendingResponse(BaseModel):
    items: list[DigestItemResponse] = Field(default_factory=list)
    total: int = 0
