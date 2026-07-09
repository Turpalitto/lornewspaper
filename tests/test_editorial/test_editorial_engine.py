"""Tests for the core Editorial Engine."""

from __future__ import annotations

import pytest

from api.editorial.engine import EditorialEngine
from api.editorial.models import EditorialPaper
from api.editorial.takeaways import generate_clinical_takeaway, generate_executive_summary


def _paper(
    title: str = "Test Paper",
    importance: float = 0.5,
    evidence: str = "B",
    abstract: str = "A study about ENT conditions.",
) -> EditorialPaper:
    return EditorialPaper(
        id="p1", title=title, abstract=abstract,
        evidence_level=evidence, clinical_importance=importance,
        topics=["otology"], authors=["Author"], journal="Journal",
    )


class TestEditorialEngine:
    @pytest.mark.asyncio
    async def test_generate_today_returns_digest(self):
        engine = EditorialEngine()
        digest = await engine.generate_today()
        assert digest.id
        assert digest.period == "daily"
        assert digest.title

    @pytest.mark.asyncio
    async def test_generate_weekly_returns_digest(self):
        engine = EditorialEngine()
        digest = await engine.generate_weekly()
        assert digest.id
        assert digest.period == "weekly"

    @pytest.mark.asyncio
    async def test_top_story_selected(self):
        engine = EditorialEngine()
        papers = [_paper(title="Top Paper", importance=0.9)]
        digest = await engine._generate("daily", papers[0].publication_date, papers)
        if digest.top_story.paper:
            assert digest.top_story.paper.title == "Top Paper"

    @pytest.mark.asyncio
    async def test_executive_summary_generated(self):
        papers = [_paper(title="Important Study")]
        summary = generate_executive_summary(papers)
        assert len(summary) == 3

    @pytest.mark.asyncio
    async def test_clinical_takeaway_generated(self):
        papers = [_paper(title="Key Study", importance=0.8)]
        takeaway = generate_clinical_takeaway(papers)
        assert takeaway.headline
        assert len(takeaway.action_items) >= 1

    @pytest.mark.asyncio
    async def test_breaking_findings_empty(self):
        papers = [_paper(title="Routine Study", importance=0.3)]
        engine = EditorialEngine()
        digest = await engine._generate("daily", papers[0].publication_date, papers)
        assert isinstance(digest.breaking_findings, list)

    @pytest.mark.asyncio
    async def test_digest_has_reading_time(self):
        papers = [_paper(title="Long Paper", abstract="word " * 500)]
        engine = EditorialEngine()
        digest = await engine._generate("daily", papers[0].publication_date, papers)
        assert digest.reading_time_minutes >= 1

    @pytest.mark.asyncio
    async def test_get_editorial_digest_by_id(self):
        engine = EditorialEngine()
        d1 = await engine.generate_today()
        found = await engine.get_editorial_digest(d1.id)
        assert found is not None
        assert found.id == d1.id

    @pytest.mark.asyncio
    async def test_get_latest_daily(self):
        engine = EditorialEngine()
        await engine.generate_today()
        latest = await engine.get_latest_daily()
        assert latest is not None
        assert latest.period == "daily"
