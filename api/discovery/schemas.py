"""Pydantic schemas for Content Discovery Engine API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from api.discovery.models import (
    Author, DiscoveryItem, DiscoveryResult, JournalInfo, TrendTopic,
)


class DiscoveryItemResponse(BaseModel):
    id: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source: str = ""
    discovery_strategy: str = ""
    citation_count: int = 0
    topics: list[str] = Field(default_factory=list)

    @classmethod
    def from_item(cls, item: DiscoveryItem) -> DiscoveryItemResponse:
        return cls(
            id=item.id, title=item.title, authors=item.authors,
            journal=item.journal, doi=item.doi, pmid=item.pmid,
            abstract=item.abstract[:300] if item.abstract else "",
            source=item.source,
            discovery_strategy=item.discovery_strategy.value if item.discovery_strategy else "",
            citation_count=item.citation_count,
            topics=item.topics,
        )


class AuthorResponse(BaseModel):
    name: str = ""
    institutions: list[str] = Field(default_factory=list)
    paper_count: int = 0
    top_topics: list[str] = Field(default_factory=list)
    recent_papers: list[str] = Field(default_factory=list)

    @classmethod
    def from_author(cls, a: Author) -> AuthorResponse:
        return cls(
            name=a.name, institutions=a.institutions,
            paper_count=a.paper_count, top_topics=a.top_topics,
            recent_papers=a.recent_papers[:3],
        )


class JournalInfoResponse(BaseModel):
    name: str = ""
    impact_factor: float = 0.0
    papers_this_period: int = 0

    @classmethod
    def from_journal(cls, j: JournalInfo) -> JournalInfoResponse:
        return cls(
            name=j.name, impact_factor=j.impact_factor,
            papers_this_period=j.papers_this_period,
        )


class TrendTopicResponse(BaseModel):
    name: str = ""
    description: str = ""
    growth_rate: float = 0.0
    paper_count: int = 0
    momentum: str = ""
    emerging: bool = False

    @classmethod
    def from_trend(cls, t: TrendTopic) -> TrendTopicResponse:
        return cls(
            name=t.name, description=t.description,
            growth_rate=t.growth_rate, paper_count=t.paper_count,
            momentum=t.momentum, emerging=t.emerging,
        )


class NewDevelopmentsResponse(BaseModel):
    new_procedures: list[str] = Field(default_factory=list)
    new_devices: list[str] = Field(default_factory=list)
    new_drugs: list[str] = Field(default_factory=list)
    new_techniques: list[str] = Field(default_factory=list)
    new_diseases: list[str] = Field(default_factory=list)


class DiscoveryResultResponse(BaseModel):
    id: str = ""
    date: str = ""
    total_discovered: int = 0
    strategies_used: list[str] = Field(default_factory=list)
    items: list[DiscoveryItemResponse] = Field(default_factory=list)
    new_authors: list[AuthorResponse] = Field(default_factory=list)
    top_journals: list[JournalInfoResponse] = Field(default_factory=list)
    trending_topics: list[TrendTopicResponse] = Field(default_factory=list)
    emerging_topics: list[TrendTopicResponse] = Field(default_factory=list)
    generated_at: str = ""

    @classmethod
    def from_result(cls, r: DiscoveryResult) -> DiscoveryResultResponse:
        return cls(
            id=r.id, date=r.date.isoformat() if r.date else "",
            total_discovered=r.total_discovered,
            strategies_used=[s.value for s in r.strategies_used],
            items=[DiscoveryItemResponse.from_item(i) for i in r.items[:20]],
            new_authors=[AuthorResponse.from_author(a) for a in r.new_authors[:10]],
            top_journals=[JournalInfoResponse.from_journal(j) for j in r.top_journals],
            trending_topics=[TrendTopicResponse.from_trend(t) for t in r.trending_topics],
            emerging_topics=[TrendTopicResponse.from_trend(t) for t in r.emerging_topics],
            generated_at=r.generated_at.isoformat() if r.generated_at else "",
        )
