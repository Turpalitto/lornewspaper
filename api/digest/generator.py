"""DigestGenerator — LLM-powered evidence-based daily digest.

Pipeline:
  1. Search all ENT topics via LORNEWS SearchService
  2. Download, process, index new articles
  3. Group by topic (Disease, Procedure, Study type)
  4. Rank by clinical importance
  5. Generate LLM summaries per topic
  6. Assemble Digest
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, UTC
from typing import Any

import structlog

from api.digest.grouping import assign_study_design, assign_topic, group_by_topic, extract_tags
from api.digest.models import (
    Digest, DigestItem, DigestPeriod, ENTSubspecialty, Topic, ENT_TOPIC_DISPLAY, ENT_ICONS,
)
from api.digest.ranking import compute_clinical_importance
from api.digest.search_queries import TOPIC_QUERIES

_LOG = structlog.get_logger("api.digest")

try:
    from search_service.service import SearchService
    from knowledge_base.service import KnowledgeBaseService
    from research_agent.agent import ResearchAgent
    HAS_LORNEWS = True
except ImportError:
    HAS_LORNEWS = False
    SearchService = Any
    KnowledgeBaseService = Any
    ResearchAgent = Any


class DigestGenerator:
    """Generate evidence-based digests from ENT literature."""

    def __init__(
        self,
        search_service: SearchService | None = None,
        knowledge_base: KnowledgeBaseService | None = None,
        research_agent: ResearchAgent | None = None,
    ):
        self._search = search_service
        self._kb = knowledge_base
        self._agent = research_agent
        self._items: dict[str, DigestItem] = {}
        self._digests: dict[str, Digest] = {}

    async def generate_daily(self) -> Digest:
        """Generate today's digest."""
        return await self._generate(DigestPeriod.DAILY, date.today())

    async def generate_weekly(self) -> Digest:
        """Generate this week's digest."""
        return await self._generate(DigestPeriod.WEEKLY, date.today())

    async def generate_monthly(self) -> Digest:
        """Generate this month's digest."""
        return await self._generate(DigestPeriod.MONTHLY, date.today())

    async def generate_for_period(self, period: DigestPeriod, reference_date: date) -> Digest:
        """Generate digest for a specific period."""
        return await self._generate(period, reference_date)

    async def get_digest(self, digest_id: str) -> Digest | None:
        return self._digests.get(digest_id)

    def get_trending_papers(self, limit: int = 10) -> list[DigestItem]:
        """Get top trending papers across all digests."""
        all_items = list(self._items.values())
        all_items.sort(key=lambda x: x.clinical_importance, reverse=True)
        return all_items[:limit]

    async def _generate(self, period: DigestPeriod, reference_date: date) -> Digest:
        """Core digest generation logic."""
        digest_id = str(uuid.uuid4())
        period_name = {"daily": "Today", "weekly": "Weekly", "monthly": "Monthly"}[period.value]

        digest = Digest(
            id=digest_id,
            period=period,
            date=reference_date,
            title=f"{period_name} ENT Literature Digest — {reference_date.isoformat()}",
        )

        items: list[DigestItem] = []

        # Step 1: Search all ENT topics
        for topic in ENTSubspecialty:
            topic_items = await self._search_topic(topic, period, reference_date)
            items.extend(topic_items)

        # Step 2: Process and enrich items
        for item in items:
            item.topics = assign_topic(item)
            item.study_design = assign_study_design(item)
            item.tags = extract_tags(item)
            item.clinical_importance = compute_clinical_importance(item)
            self._items[item.id] = item

        # Step 3: Group by topic
        grouped = group_by_topic(items)
        digest.total_papers = len(items)
        digest.items = items

        digest.topics = []
        for topic_id, topic_items in grouped.items():
            t = Topic(
                id=topic_id,
                display_name=ENT_TOPIC_DISPLAY.get(topic_id, topic_id.value),
                icon=ENT_ICONS.get(topic_id, "📄"),
                items=topic_items,
                paper_count=len(topic_items),
            )
            digest.topics.append(t)

        # Step 4: Generate LLM summaries per topic
        if HAS_LORNEWS and self._agent:
            for topic in digest.topics:
                topic.summary = await self._generate_topic_summary(topic)

        digest.trending = sorted(
            items, key=lambda x: x.clinical_importance, reverse=True
        )[:10]

        self._digests[digest_id] = digest
        _LOG.info("digest_generated", period=period.value, papers=len(items), topics=len(digest.topics))
        return digest

    async def _search_topic(
        self, topic: ENTSubspecialty, period: DigestPeriod, reference_date: date
    ) -> list[DigestItem]:
        """Search recent publications for a specific ENT topic."""
        queries = TOPIC_QUERIES.get(topic, [])
        items: list[DigestItem] = []

        max_days = {"daily": 7, "weekly": 14, "monthly": 60}[period.value]
        date_filter = reference_date - timedelta(days=max_days)

        if not HAS_LORNEWS or not self._search:
            return self._mock_items(topic, queries[:1])

        from search_service.config import Settings as SearchSettings
        from search_service.service import SearchService

        svc = self._search or SearchService()
        try:
            for query in queries[:2]:  # Max 2 queries per topic to stay within rate limits
                results = await svc.search_all(query, limit=5)
                for article in results:
                    item = DigestItem(
                        id=str(uuid.uuid4()),
                        title=getattr(article, "title", "") or "",
                        authors=getattr(article, "authors", []) or [],
                        journal=getattr(article, "journal", "") or "",
                        doi=getattr(article, "doi", "") or "",
                        pmid=getattr(article, "pmid", "") or "",
                        abstract=getattr(article, "abstract", "") or "",
                    )
                    items.append(item)
        finally:
            if svc is not self._search:
                await svc.aclose()

        return items

    async def _generate_topic_summary(self, topic: Topic) -> str:
        """Generate an LLM-powered summary of papers in a topic."""
        if not topic.items:
            return "No new papers in this topic."

        titles = "\n".join(f"- {item.title}" for item in topic.items[:5])
        prompt = (
            f"Summarize the key clinical developments in {topic.display_name} "
            f"based on these recent papers:\n{titles}\n\n"
            f"Focus on: clinical relevance, novel findings, practice-changing results."
        )
        return prompt  # Placeholder — actual LLM call uses ResearchAgent

    def _mock_items(self, topic: ENTSubspecialty, queries: list[str]) -> list[DigestItem]:
        """Generate mock items for development/testing."""
        return []
