"""Data models for the Content Discovery Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, UTC
from enum import StrEnum
from typing import Any


class DiscoveryStrategy(StrEnum):
    KEYWORD_SEARCH = "keyword_search"
    CITATION_EXPANSION = "citation_expansion"
    REFERENCE_EXPANSION = "reference_expansion"
    AUTHOR_TRACKING = "author_tracking"
    JOURNAL_TRACKING = "journal_tracking"
    TREND_DETECTION = "trend_detection"


@dataclass(slots=True)
class Author:
    name: str = ""
    institutions: list[str] = field(default_factory=list)
    country: str = ""
    h_index: int = 0
    paper_count: int = 0
    top_topics: list[str] = field(default_factory=list)
    orcid: str = ""
    recent_papers: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JournalInfo:
    name: str = ""
    issn: str = ""
    impact_factor: float = 0.0
    papers_this_period: int = 0
    top_topics: list[str] = field(default_factory=list)
    is_predatory: bool = False


@dataclass(slots=True)
class TrendTopic:
    name: str = ""
    description: str = ""
    growth_rate: float = 0.0  # % increase in publications
    paper_count: int = 0
    momentum: str = ""  # exploding | growing | stable | declining
    related_terms: list[str] = field(default_factory=list)
    key_papers: list[str] = field(default_factory=list)
    emerging: bool = False  # Newly detected topic


@dataclass(slots=True)
class DiscoveryItem:
    id: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    publication_date: date | None = None
    abstract: str = ""
    source: str = ""  # PubMed, EuropePMC, OpenAlex, Crossref, bioRxiv, medRxiv, DOAJ
    discovery_strategy: DiscoveryStrategy = DiscoveryStrategy.KEYWORD_SEARCH
    citation_count: int = 0
    reference_count: int = 0
    topics: list[str] = field(default_factory=list)
    is_retracted: bool = False
    is_predatory: bool = False
    is_conference_abstract: bool = False
    relevance_score: float = 0.0


@dataclass(slots=True)
class DiscoveryResult:
    id: str
    date: date
    items: list[DiscoveryItem] = field(default_factory=list)
    strategies_used: list[DiscoveryStrategy] = field(default_factory=list)
    total_discovered: int = 0
    new_authors: list[Author] = field(default_factory=list)
    top_journals: list[JournalInfo] = field(default_factory=list)
    trending_topics: list[TrendTopic] = field(default_factory=list)
    emerging_topics: list[TrendTopic] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
