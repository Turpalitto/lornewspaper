"""Pydantic schemas for guideline API."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from clinical_assistant.models.guideline import Guideline, GuidelineSection, Recommendation


class RecommendationResponse(BaseModel):
    id: str = ""
    text_ru: str = ""
    text_en: str = ""
    strength: str = ""
    evidence_level: str = ""
    population: str = ""
    intervention: str = ""
    comparator: str = ""
    outcomes: list[str] = Field(default_factory=list)
    source_paragraph: str = ""
    contraindications: list[str] = Field(default_factory=list)
    pregnancy: str = ""
    children: str = ""

    @classmethod
    def from_recommendation(cls, rec: Recommendation) -> RecommendationResponse:
        return cls(
            id=rec.id,
            text_ru=rec.text_ru,
            text_en=rec.text_en,
            strength=rec.strength.value if rec.strength else "",
            evidence_level=rec.evidence_level.value if rec.evidence_level else "",
            population=rec.population,
            intervention=rec.intervention,
            comparator=rec.comparator,
            outcomes=rec.outcomes,
            source_paragraph=rec.source_paragraph,
            contraindications=rec.contraindications,
            pregnancy=rec.pregnancy.value if rec.pregnancy else "",
            children=rec.children.value if rec.children else "",
        )


class GuidelineSectionResponse(BaseModel):
    id: str = ""
    heading: str = ""
    level: int = 1
    content: str = ""
    recommendations: list[RecommendationResponse] = Field(default_factory=list)

    @classmethod
    def from_section(cls, section: GuidelineSection) -> GuidelineSectionResponse:
        return cls(
            id=section.id,
            heading=section.heading,
            level=section.level,
            content=section.content,
            recommendations=[RecommendationResponse.from_recommendation(r) for r in section.recommendations],
        )


class GuidelineResponse(BaseModel):
    id: str = ""
    title_ru: str = ""
    title_en: str = ""
    source: str = ""
    version: str = ""
    organization: str = ""
    language: str = ""
    sections: list[GuidelineSectionResponse] = Field(default_factory=list)
    recommendations: list[RecommendationResponse] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)
    status: str = ""

    @classmethod
    def from_guideline(cls, g: Guideline) -> GuidelineResponse:
        return cls(
            id=g.id,
            title_ru=g.title_ru,
            title_en=g.title_en,
            source=g.source.value if g.source else "",
            version=g.version,
            organization=g.organization,
            language=g.language,
            sections=[GuidelineSectionResponse.from_section(s) for s in g.sections],
            recommendations=[RecommendationResponse.from_recommendation(r) for r in g.recommendations],
            icd10_codes=g.icd10_codes,
            mesh_terms=g.mesh_terms,
            status=g.status.value if g.status else "",
        )


class GuidelineListResponse(BaseModel):
    items: list[GuidelineResponse] = Field(default_factory=list)
    total: int = 0


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Search query (diagnosis, symptom, drug)")
    top_k: int = Field(default=10, ge=1, le=100)


class SearchResponse(BaseModel):
    items: list[GuidelineResponse] = Field(default_factory=list)
    total: int = 0
    elapsed_ms: float = 0


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Clinical question")
    guideline_ids: list[str] | None = Field(default=None, description="Filter to specific guidelines")


class RecommendationResult(BaseModel):
    text: str = ""
    strength: str = ""
    evidence_level: str = ""
    guideline: str = ""
    section: str = ""


class AskResponse(BaseModel):
    answer: str = ""
    recommendations: list[RecommendationResult] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence: float = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IngestResponse(BaseModel):
    guideline_id: str = ""
    title: str = ""
    sections: int = 0
    recommendations: int = 0
