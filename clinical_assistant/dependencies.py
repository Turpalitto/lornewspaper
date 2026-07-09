"""FastAPI dependency injection."""

from __future__ import annotations

from clinical_assistant.services.guideline_service import GuidelineService
from clinical_assistant.services.recommendation_extractor import RecommendationExtractor
from clinical_assistant.services.citation_verifier import CitationVerifier

_guideline_service: GuidelineService | None = None


def get_guideline_service() -> GuidelineService:
    global _guideline_service
    if _guideline_service is None:
        _guideline_service = GuidelineService()
    return _guideline_service


def get_recommendation_extractor() -> RecommendationExtractor:
    return RecommendationExtractor()


def get_citation_verifier() -> CitationVerifier:
    return CitationVerifier()
