"""Tests for RecommendationExtractor."""

from __future__ import annotations

import pytest

from clinical_assistant.models.guideline import (
    ChildrenCategory,
    EvidenceLevel,
    PregnancyCategory,
    RecommendationStrength,
)
from clinical_assistant.services.recommendation_extractor import RecommendationExtractor


class TestRecommendationExtractor:
    def test_extract_ru_strong_recommendation(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        strong = [r for r in recs if r.strength == RecommendationStrength.STRONG]
        assert len(strong) >= 1
        assert any("микробиологического" in (r.text_ru or "") for r in strong)

    def test_extract_ru_conditional_recommendation(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        conditional = [r for r in recs if r.strength == RecommendationStrength.CONDITIONAL]
        assert len(conditional) >= 2
        texts = " ".join(r.text_ru or "" for r in conditional)
        assert "амоксициллина" in texts

    def test_extract_not_recommended(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        not_rec = [r for r in recs if r.strength == RecommendationStrength.NOT_RECOMMENDED]
        assert len(not_rec) >= 1
        assert any("противовирусных" in (r.text_ru or "") for r in not_rec)

    def test_extract_evidence_level(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        levels = {r.evidence_level for r in recs if r.evidence_level}
        assert EvidenceLevel.A in levels or EvidenceLevel.B in levels

    def test_extract_contraindications(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        with_contra = [r for r in recs if r.contraindications]
        assert len(with_contra) >= 1

    def test_extract_pregnancy(self, extractor, sample_guideline_text_ru):
        recs = extractor.extract(sample_guideline_text_ru)
        pregnancy_recs = [r for r in recs if r.pregnancy]
        assert len(pregnancy_recs) >= 1

    def test_deduplication(self, extractor):
        text = """
        Мы рекомендуем использовать амоксициллин для лечения пневмонии.
        Рекомендуется применение амоксициллина.
        """
        recs = extractor.extract(text)
        hashes = {r.source_text_hash for r in recs if r.source_text_hash}
        assert len(hashes) == len(recs), "Duplicate recommendations detected"

    def test_empty_text(self, extractor):
        recs = extractor.extract("")
        assert recs == []

    def test_no_recommendations(self, extractor):
        recs = extractor.extract("This is a plain paragraph without any recommendations.")
        assert recs == []

    def test_english_patterns(self, extractor):
        text = """
        We strongly recommend antibiotic therapy within 4 hours of diagnosis (evidence level A).
        We recommend amoxicillin 500 mg three times daily for 7 days (evidence level B).
        We do not recommend routine use of antiviral agents.
        """
        recs = extractor.extract(text)
        assert len(recs) == 3
        strengths = {r.strength for r in recs}
        assert RecommendationStrength.STRONG in strengths
        assert RecommendationStrength.CONDITIONAL in strengths
        assert RecommendationStrength.NOT_RECOMMENDED in strengths
