"""Pydantic schemas for Editorial Engine API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from api.editorial.models import (
    ClinicalTakeaway, EditorialDigest, EditorialPaper, EditorialSection,
    ResearchControversy, ResearchTrend, TopStory,
)


class EditorialPaperResponse(BaseModel):
    id: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    doi: str = ""
    evidence_level: str = ""
    study_design: str = ""
    clinical_importance: float = 0.0
    topics: list[str] = Field(default_factory=list)
    editorial_commentary: str = ""
    clinical_relevance: str = ""
    practice_change: str = ""
    is_top_story: bool = False
    is_breaking: bool = False

    @classmethod
    def from_editorial_paper(cls, p: EditorialPaper) -> EditorialPaperResponse:
        return cls(
            id=p.id, title=p.title, authors=p.authors, journal=p.journal,
            doi=p.doi, evidence_level=p.evidence_level,
            study_design=p.study_design, clinical_importance=p.clinical_importance,
            topics=p.topics, editorial_commentary=p.editorial_commentary,
            clinical_relevance=p.clinical_relevance, practice_change=p.practice_change,
            is_top_story=p.is_top_story, is_breaking=p.is_breaking,
        )


class TopStoryResponse(BaseModel):
    headline: str = ""
    why_it_matters: str = ""
    clinical_impact: str = ""
    key_finding: str = ""
    specialist_comment: str = ""
    paper: EditorialPaperResponse | None = None

    @classmethod
    def from_top_story(cls, ts: TopStory) -> TopStoryResponse:
        return cls(
            headline=ts.headline, why_it_matters=ts.why_it_matters,
            clinical_impact=ts.clinical_impact, key_finding=ts.key_finding,
            specialist_comment=ts.specialist_comment,
            paper=EditorialPaperResponse.from_editorial_paper(ts.paper) if ts.paper else None,
        )


class ResearchControversyResponse(BaseModel):
    title: str = ""
    topic: str = ""
    position_a: str = ""
    position_b: str = ""
    resolution: str = ""
    clinical_guidance: str = ""

    @classmethod
    def from_controversy(cls, c: ResearchControversy) -> ResearchControversyResponse:
        return cls(
            title=c.title, topic=c.topic,
            position_a=c.position_a, position_b=c.position_b,
            resolution=c.resolution, clinical_guidance=c.clinical_guidance,
        )


class ResearchTrendResponse(BaseModel):
    name: str = ""
    description: str = ""
    paper_count: int = 0
    momentum: str = ""

    @classmethod
    def from_trend(cls, t: ResearchTrend) -> ResearchTrendResponse:
        return cls(
            name=t.name, description=t.description,
            paper_count=t.paper_count, momentum=t.momentum,
        )


class EditorialSectionResponse(BaseModel):
    title: str = ""
    icon: str = ""
    body: str = ""
    papers: list[EditorialPaperResponse] = Field(default_factory=list)

    @classmethod
    def from_section(cls, s: EditorialSection) -> EditorialSectionResponse:
        return cls(
            title=s.title, icon=s.icon, body=s.body,
            papers=[EditorialPaperResponse.from_editorial_paper(p) for p in s.papers],
        )


class EditorialDigestResponse(BaseModel):
    id: str = ""
    period: str = ""
    date: str = ""
    title: str = ""
    subtitle: str = ""
    executive_summary: list[str] = Field(default_factory=list)
    top_story: TopStoryResponse = Field(default_factory=TopStoryResponse)
    breaking_findings: list[EditorialPaperResponse] = Field(default_factory=list)
    clinical_changes: list[EditorialSectionResponse] = Field(default_factory=list)
    practice_impact: list[str] = Field(default_factory=list)
    controversies: list[ResearchControversyResponse] = Field(default_factory=list)
    research_trends: list[ResearchTrendResponse] = Field(default_factory=list)
    papers: list[EditorialPaperResponse] = Field(default_factory=list)
    total_papers_reviewed: int = 0
    reading_time_minutes: int = 3
    generated_at: str = ""

    @classmethod
    def from_editorial_digest(cls, d: EditorialDigest) -> EditorialDigestResponse:
        return cls(
            id=d.id, period=d.period,
            date=d.date.isoformat() if d.date else "",
            title=d.title, subtitle=d.subtitle,
            executive_summary=d.executive_summary,
            top_story=TopStoryResponse.from_top_story(d.top_story) if d.top_story else TopStoryResponse(),
            breaking_findings=[EditorialPaperResponse.from_editorial_paper(p) for p in d.breaking_findings],
            clinical_changes=[EditorialSectionResponse.from_section(s) for s in d.clinical_changes],
            practice_impact=d.practice_impact,
            controversies=[ResearchControversyResponse.from_controversy(c) for c in d.controversies],
            research_trends=[ResearchTrendResponse.from_trend(t) for t in d.research_trends],
            papers=[EditorialPaperResponse.from_editorial_paper(p) for p in d.papers],
            total_papers_reviewed=d.total_papers_reviewed,
            reading_time_minutes=d.reading_time_minutes,
            generated_at=d.generated_at.isoformat() if d.generated_at else "",
        )


class EditorialDigestListResponse(BaseModel):
    items: list[EditorialDigestResponse] = Field(default_factory=list)
    total: int = 0
