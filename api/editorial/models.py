"""Data models for the AI Editorial Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, UTC
from typing import Any


@dataclass(slots=True)
class EditorialPaper:
    """A paper in the editorial digest with editorial metadata."""
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    publication_date: date | None = None
    abstract: str = ""
    evidence_level: str = ""
    study_design: str = ""
    clinical_importance: float = 0.0
    topics: list[str] = field(default_factory=list)

    # Editorial fields
    editorial_commentary: str = ""
    clinical_relevance: str = ""
    practice_change: str = ""
    strength: str = ""
    limitation: str = ""
    is_top_story: bool = False
    is_breaking: bool = False
    is_controversial: bool = False


@dataclass(slots=True)
class TopStory:
    """The single most important paper of the day."""
    paper: EditorialPaper | None = None
    headline: str = ""
    why_it_matters: str = ""
    clinical_impact: str = ""
    key_finding: str = ""
    specialist_comment: str = ""


@dataclass(slots=True)
class ClinicalTakeaway:
    """What should an ENT surgeon remember today."""
    headline: str = ""
    body: str = ""
    action_items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ResearchControversy:
    """Two or more papers with conflicting findings."""
    title: str = ""
    topic: str = ""
    position_a: str = ""
    position_a_supporting_papers: list[str] = field(default_factory=list)
    position_b: str = ""
    position_b_supporting_papers: list[str] = field(default_factory=list)
    resolution: str = ""
    clinical_guidance: str = ""


@dataclass(slots=True)
class ResearchTrend:
    """An emerging research theme detected across multiple papers."""
    name: str = ""
    description: str = ""
    paper_count: int = 0
    momentum: str = ""  # emerging | growing | established | declining
    papers: list[EditorialPaper] = field(default_factory=list)


@dataclass(slots=True)
class EditorialSection:
    """A named section in the editorial digest."""
    title: str = ""
    icon: str = "📄"
    body: str = ""
    papers: list[EditorialPaper] = field(default_factory=list)


@dataclass(slots=True)
class EditorialDigest:
    """The complete editorial digest for a period."""
    id: str
    period: str  # "daily" | "weekly"
    date: date
    title: str
    subtitle: str = ""

    # Editorial sections
    executive_summary: list[str] = field(default_factory=list)
    top_story: TopStory = field(default_factory=TopStory)
    breaking_findings: list[EditorialPaper] = field(default_factory=list)
    clinical_changes: list[EditorialSection] = field(default_factory=list)
    practice_impact: list[str] = field(default_factory=list)
    controversies: list[ResearchControversy] = field(default_factory=list)
    research_trends: list[ResearchTrend] = field(default_factory=list)

    # All papers
    papers: list[EditorialPaper] = field(default_factory=list)

    # Metadata
    total_papers_reviewed: int = 0
    reading_time_minutes: int = 3
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
