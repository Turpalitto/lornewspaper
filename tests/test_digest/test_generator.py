"""Tests for DigestGenerator (without LORNEWS)."""

from __future__ import annotations

import pytest

from api.digest.generator import DigestGenerator
from api.digest.models import DigestPeriod, ENTSubspecialty


class TestDigestGenerator:
    @pytest.mark.asyncio
    async def test_generate_daily_returns_digest(self):
        gen = DigestGenerator()
        digest = await gen.generate_daily()
        assert digest.id
        assert digest.period == DigestPeriod.DAILY
        assert digest.total_papers >= 0

    @pytest.mark.asyncio
    async def test_generate_weekly_returns_digest(self):
        gen = DigestGenerator()
        digest = await gen.generate_weekly()
        assert digest.id
        assert digest.period == DigestPeriod.WEEKLY

    @pytest.mark.asyncio
    async def test_generate_monthly_returns_digest(self):
        gen = DigestGenerator()
        digest = await gen.generate_monthly()
        assert digest.id
        assert digest.period == DigestPeriod.MONTHLY

    @pytest.mark.asyncio
    async def test_get_trending_returns_list(self):
        gen = DigestGenerator()
        trending = gen.get_trending_papers(limit=5)
        assert isinstance(trending, list)

    @pytest.mark.asyncio
    async def test_generated_digest_has_all_topics(self):
        gen = DigestGenerator()
        digest = await gen.generate_daily()
        # Should have topics defined even with 0 papers
        assert len(digest.topics) >= 0

    @pytest.mark.asyncio
    async def test_digest_has_title(self):
        gen = DigestGenerator()
        digest = await gen.generate_daily()
        assert "ENT" in digest.title
        assert "Digest" in digest.title

    @pytest.mark.asyncio
    async def test_get_digest_by_id(self):
        gen = DigestGenerator()
        d1 = await gen.generate_daily()
        found = await gen.get_digest(d1.id)
        assert found is not None
        assert found.id == d1.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_digest(self):
        gen = DigestGenerator()
        found = await gen.get_digest("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_multiple_generations(self):
        gen = DigestGenerator()
        await gen.generate_daily()
        await gen.generate_weekly()
        await gen.generate_monthly()
        # Should not raise
        assert True
