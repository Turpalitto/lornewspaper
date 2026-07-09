"""Content Discovery Engine — orchestrates all discovery strategies."""

from __future__ import annotations

import uuid
from datetime import date, datetime, UTC
from typing import Any

import structlog

from api.discovery.author_graph import AuthorGraph
from api.discovery.models import (
    DiscoveryItem, DiscoveryResult, DiscoveryStrategy,
)
from api.discovery.quality_filter import QualityFilter
from api.discovery.strategies.author_tracking import AuthorTrackingStrategy
from api.discovery.strategies.citation_expansion import CitationExpansionStrategy
from api.discovery.strategies.journal_tracking import JournalTrackingStrategy
from api.discovery.strategies.keyword_search import KeywordSearchStrategy
from api.discovery.strategies.reference_expansion import ReferenceExpansionStrategy
from api.discovery.strategies.trend_detection import TrendDetectionStrategy
from api.discovery.trend_analysis import TrendAnalyzer

_LOG = structlog.get_logger("api.discovery")


class ContentDiscoveryEngine:
    """Continuously discover emerging ENT research using multiple strategies."""

    def __init__(self):
        self._keyword = KeywordSearchStrategy()
        self._citation = CitationExpansionStrategy()
        self._reference = ReferenceExpansionStrategy()
        self._author_track = AuthorTrackingStrategy()
        self._journal_track = JournalTrackingStrategy()
        self._trend_detect = TrendDetectionStrategy()
        self._quality = QualityFilter()
        self._graph = AuthorGraph()
        self._analyzer = TrendAnalyzer()

        self._results: dict[str, DiscoveryResult] = {}

    async def discover_today(self) -> DiscoveryResult:
        """Run all discovery strategies and produce today's discovery result."""
        result_id = str(uuid.uuid4())
        result = DiscoveryResult(id=result_id, date=date.today())

        all_items: list[DiscoveryItem] = []
        all_authors: list[Any] = []
        all_journals: list[Any] = []

        try:
            # Strategy 1: Keyword search
            _LOG.info("discovery_running", strategy="keyword")
            kw_items = await self._keyword.discover()
            all_items.extend(kw_items)
            result.strategies_used.append(DiscoveryStrategy.KEYWORD_SEARCH)

            # Strategy 2: Citation expansion
            _LOG.info("discovery_running", strategy="citation")
            cite_items = await self._citation.discover()
            all_items.extend(cite_items)
            result.strategies_used.append(DiscoveryStrategy.CITATION_EXPANSION)

            # Strategy 3: Reference expansion
            _LOG.info("discovery_running", strategy="reference")
            ref_items = await self._reference.discover()
            all_items.extend(ref_items)
            result.strategies_used.append(DiscoveryStrategy.REFERENCE_EXPANSION)

            # Strategy 4: Author tracking
            _LOG.info("discovery_running", strategy="author")
            auth_items, auth_people = await self._author_track.discover()
            all_items.extend(auth_items)
            all_authors.extend(auth_people)
            result.strategies_used.append(DiscoveryStrategy.AUTHOR_TRACKING)

            # Strategy 5: Journal tracking
            _LOG.info("discovery_running", strategy="journal")
            journal_items, journals = await self._journal_track.discover()
            all_items.extend(journal_items)
            all_journals.extend(journals)
            result.strategies_used.append(DiscoveryStrategy.JOURNAL_TRACKING)

            # Strategy 6: Trend detection
            _LOG.info("discovery_running", strategy="trend")
            trend_items, trending, emerging = await self._trend_detect.discover()
            all_items.extend(trend_items)
            result.trending_topics = trending
            result.emerging_topics = emerging
            result.strategies_used.append(DiscoveryStrategy.TREND_DETECTION)

        except Exception as exc:
            _LOG.error("discovery_strategy_failed", error=str(exc))

        # Apply quality filter
        _LOG.info("discovery_filtering", before=len(all_items))
        filtered = self._quality.filter(all_items)
        result.items = filtered
        result.total_discovered = len(filtered)
        _LOG.info("discovery_filtered", after=len(filtered))

        # Build author graph
        result.new_authors = self._graph.build(filtered)

        # Set top journals
        result.top_journals = all_journals[:10]

        # Run trend analysis
        trends = self._analyzer.analyze(filtered)
        result.emerging_topics = result.emerging_topics or []

        self._results[result_id] = result
        _LOG.info("discovery_complete",
                  total=result.total_discovered,
                  strategies=len(result.strategies_used),
                  authors=len(result.new_authors),
                  topics=len(result.trending_topics))

        return result

    async def get_discovery(self, result_id: str) -> DiscoveryResult | None:
        return self._results.get(result_id)

    async def get_latest(self) -> DiscoveryResult | None:
        if not self._results:
            return None
        return max(self._results.values(), key=lambda r: r.date)

    def get_trending_topics(self) -> list[Any]:
        latest = max(self._results.values(), key=lambda r: r.date) if self._results else None
        if latest:
            return latest.trending_topics
        return []

    def get_emerging_topics(self) -> list[Any]:
        latest = max(self._results.values(), key=lambda r: r.date) if self._results else None
        if latest:
            return latest.emerging_topics
        return []
