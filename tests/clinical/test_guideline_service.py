"""Tests for GuidelineService."""

from __future__ import annotations

import pytest

from clinical_assistant.models.guideline import GuidelineSource, RecommendationStrength


class TestGuidelineService:
    @pytest.mark.asyncio
    async def test_ingest_text_creates_guideline(self, guideline_service, sample_guideline_text_ru):
        guideline = await guideline_service.ingest_text(
            title="Внебольничная пневмония",
            text=sample_guideline_text_ru,
            source=GuidelineSource.LOCAL,
        )
        assert guideline.id
        assert guideline.title_ru == "Внебольничная пневмония"
        assert guideline.source == GuidelineSource.LOCAL

    @pytest.mark.asyncio
    async def test_ingest_text_extracts_sections(self, guideline_service, sample_guideline_text_ru):
        guideline = await guideline_service.ingest_text(
            title="Test", text=sample_guideline_text_ru,
        )
        assert len(guideline.sections) >= 3

    @pytest.mark.asyncio
    async def test_ingest_text_extracts_recommendations(self, guideline_service, sample_guideline_text_ru):
        guideline = await guideline_service.ingest_text(
            title="Test", text=sample_guideline_text_ru,
        )
        assert len(guideline.recommendations) >= 5
        strengths = {r.strength for r in guideline.recommendations}
        assert RecommendationStrength.STRONG in strengths

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, guideline_service, sample_guideline_text_ru):
        await guideline_service.ingest_text(title="Pneumonia", text=sample_guideline_text_ru)
        results = await guideline_service.search("пневмония")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, guideline_service):
        results = await guideline_service.search("nonexistent condition xyz")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_guideline_by_id(self, guideline_service, sample_guideline_text_ru):
        g = await guideline_service.ingest_text(title="Test", text=sample_guideline_text_ru)
        found = guideline_service.get_guideline(g.id)
        assert found is not None
        assert found.id == g.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_guideline(self, guideline_service):
        assert guideline_service.get_guideline("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_guidelines(self, guideline_service, sample_guideline_text_ru):
        await guideline_service.ingest_text(title="G1", text=sample_guideline_text_ru)
        await guideline_service.ingest_text(title="G2", text=sample_guideline_text_ru)
        all_gs = guideline_service.list_guidelines()
        assert len(all_gs) >= 2

    @pytest.mark.asyncio
    async def test_rule_based_ask(self, guideline_service, sample_guideline_text_ru):
        await guideline_service.ingest_text(title="Pneumonia", text=sample_guideline_text_ru)
        result = await guideline_service.ask("амоксициллин дозировка")
        assert result.get("answer")
        recs = result.get("recommendations", [])
        assert len(recs) >= 1
