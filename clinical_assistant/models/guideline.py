"""Domain models for clinical guidelines and recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class GuidelineSource(StrEnum):
    RU_MINZDRAV = "ru_minzdrav"
    NICE = "nice"
    SIGN = "sign"
    WHO = "who"
    PUBMED = "pubmed"
    LOCAL = "local"


class GuidelineStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DRAFT = "draft"


class RecommendationStrength(StrEnum):
    STRONG = "strong"
    CONDITIONAL = "conditional"
    NOT_RECOMMENDED = "not_recommended"
    OPEN = "open"  # No recommendation (further research needed)


class EvidenceLevel(StrEnum):
    A = "A"  # High: RCTs or meta-analyses
    B = "B"  # Moderate: well-designed cohort/case-control
    C = "C"  # Low: case series, poor-quality studies
    D = "D"  # Very low: expert opinion
    EXPERT_OPINION = "expert_opinion"


class PregnancyCategory(StrEnum):
    SAFE = "safe"
    CAUTION = "caution"
    CONTRAINDICATED = "contraindicated"
    UNKNOWN = "unknown"


class ChildrenCategory(StrEnum):
    SAFE = "safe"
    CAUTION = "caution"
    CONTRAINDICATED = "contraindicated"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class Guideline:
    id: str
    title_ru: str = ""
    title_en: str = ""
    source: GuidelineSource = GuidelineSource.RU_MINZDRAV
    version: str = ""
    publication_date: date | None = None
    organization: str = ""
    language: str = "ru"
    url: str = ""
    sections: list[GuidelineSection] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    icd10_codes: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    status: GuidelineStatus = GuidelineStatus.ACTIVE


@dataclass(slots=True)
class GuidelineSection:
    id: str
    heading: str = ""
    level: int = 1
    content: str = ""
    recommendations: list[Recommendation] = field(default_factory=list)


@dataclass(slots=True)
class Recommendation:
    id: str
    text_ru: str = ""
    text_en: str = ""
    strength: RecommendationStrength = RecommendationStrength.OPEN
    evidence_level: EvidenceLevel = EvidenceLevel.EXPERT_OPINION
    population: str = ""
    intervention: str = ""
    comparator: str = ""
    outcomes: list[str] = field(default_factory=list)
    grade: str = ""
    source_guideline_id: str = ""
    source_section_id: str = ""
    source_paragraph: str = ""
    source_text_hash: str = ""
    icd10_codes: list[str] = field(default_factory=list)
    atc_codes: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    drug_ids: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    pregnancy: PregnancyCategory = PregnancyCategory.UNKNOWN
    children: ChildrenCategory = ChildrenCategory.UNKNOWN
    renal_adjustment: str = ""
