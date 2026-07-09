"""Core Editorial Engine — transforms paper collection into polished editorial digest.

Pipeline:
  1. Accept DailyDigest from DigestGenerator
  2. Convert to EditorialPaper models
  3. Select top story
  4. Identify breaking findings
  5. Detect research themes and merge similar papers
  6. Detect research controversies
  7. Generate executive summary
  8. Generate clinical takeaway
  9. Assemble EditorialDigest
 10. Render in all output formats
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, UTC
from typing import Any

import structlog

from api.editorial.controversy import detect_controversies
from api.editorial.formats import render_markdown, render_newsletter, render_telegram, render_email
from api.editorial.models import (
    ClinicalTakeaway, EditorialDigest, EditorialPaper, EditorialSection,
    ResearchControversy, ResearchTrend, TopStory,
)
from api.editorial.takeaways import generate_clinical_takeaway, generate_executive_summary
from api.editorial.theme_detector import detect_themes, merge_similar_papers
from api.editorial.top_story import identify_breaking_findings, select_top_story

_LOG = structlog.get_logger("api.editorial")

try:
    from api.digest.models import Digest
    HAS_DIGEST = True
except ImportError:
    HAS_DIGEST = False
    Digest = Any


class EditorialEngine:
    """Produces publication-quality editorial digests."""

    def __init__(self):
        self._digests: dict[str, EditorialDigest] = {}

    async def generate_today(self, source_digest: Any = None) -> EditorialDigest:
        """Generate today's editorial digest.

        Accepts an optional Digest from the Digest Engine,
        or generates a minimal digest from available data.
        """
        papers = self._convert_papers(source_digest) if source_digest else []
        return await self._generate("daily", date.today(), papers)

    async def generate_weekly(self, source_digests: list[Any] | None = None) -> EditorialDigest:
        """Generate this week's editorial digest from 7 daily digests."""
        all_papers: list[EditorialPaper] = []
        if source_digests:
            for d in source_digests:
                all_papers.extend(self._convert_papers(d))
        return await self._generate("weekly", date.today(), all_papers)

    async def get_editorial_digest(self, digest_id: str) -> EditorialDigest | None:
        return self._digests.get(digest_id)

    async def get_latest_daily(self) -> EditorialDigest | None:
        daily = [d for d in self._digests.values() if d.period == "daily"]
        if daily:
            return max(daily, key=lambda d: d.date)
        return None

    async def _generate(
        self, period: str, ref_date: date, papers: list[EditorialPaper]
    ) -> EditorialDigest:
        """Core editorial generation pipeline."""
        digest_id = str(uuid.uuid4())

        period_label = "Today's" if period == "daily" else "This Week's"
        digest = EditorialDigest(
            id=digest_id,
            period=period,
            date=ref_date,
            title=f"{period_label} ENT Editorial Digest",
            subtitle=f"Curated evidence-based review for ENT specialists — {ref_date.isoformat()}",
            papers=papers,
            total_papers_reviewed=len(papers),
        )

        # Step 1: Select top story
        top_story = select_top_story(papers)
        if top_story and top_story.paper:
            digest.top_story = top_story
            top_story.paper.is_top_story = True
            _LOG.info("top_story_selected", title=top_story.headline[:80])

        # Step 2: Identify breaking findings
        digest.breaking_findings = identify_breaking_findings(papers)

        # Step 3: Detect research themes
        digest.research_trends = detect_themes(papers)

        # Step 4: Detect controversies
        digest.controversies = detect_controversies(papers)
        if digest.controversies:
            _LOG.info("controversies_detected", count=len(digest.controversies))

        # Step 5: Generate clinical changes sections
        digest.clinical_changes = self._generate_clinical_changes(papers)

        # Step 6: Generate practice impact
        digest.practice_impact = self._generate_practice_impact(papers)

        # Step 7: Generate executive summary
        digest.executive_summary = generate_executive_summary(papers)

        # Step 8: Generate reading time estimate
        total_chars = sum(len(p.title) + len(p.abstract) for p in papers)
        digest.reading_time_minutes = max(1, round(total_chars / 1500))

        self._digests[digest_id] = digest
        _LOG.info("editorial_digest_generated",
                  period=period, papers=len(papers), id=digest_id)
        return digest

    def _convert_papers(self, source_digest: Any) -> list[EditorialPaper]:
        """Convert Digest items to EditorialPaper models."""
        papers: list[EditorialPaper] = []
        if not HAS_DIGEST:
            return papers

        items = getattr(source_digest, "items", []) or []
        for item in items:
            paper = EditorialPaper(
                id=getattr(item, "id", ""),
                title=getattr(item, "title", ""),
                authors=getattr(item, "authors", []) or [],
                journal=getattr(item, "journal", "") or "",
                doi=getattr(item, "doi", "") or "",
                abstract=getattr(item, "abstract", "") or "",
                evidence_level=getattr(item, "evidence_level", None) or "",
                study_design=getattr(item, "study_design", None) or "",
                clinical_importance=getattr(item, "clinical_importance", 0.0) or 0.0,
                topics=[t.value if hasattr(t, "value") else str(t)
                        for t in (getattr(item, "topics", []) or [])],
            )
            papers.append(paper)
        return papers

    def _generate_clinical_changes(self, papers: list[EditorialPaper]) -> list[EditorialSection]:
        """Identify practice-changing research."""
        high_impact = [p for p in papers if p.clinical_importance >= 0.6]
        if not high_impact:
            return []

        return [
            EditorialSection(
                title="Practice-Changing Research",
                icon="🔄",
                body=f"{len(high_impact)} papers with potential clinical impact identified.",
                papers=high_impact[:5],
            )
        ]

    def _generate_practice_impact(self, papers: list[EditorialPaper]) -> list[str]:
        """Generate practice impact statements."""
        impacts: list[str] = []
        for paper in papers[:3]:
            if paper.evidence_level in ("A", "B"):
                impacts.append(
                    f"{paper.title[:100]} — consider impact on current practice "
                    f"({paper.evidence_level} evidence)"
                )
        if not impacts:
            impacts.append("No immediate practice changes indicated by current evidence.")
        return impacts
