"""Data models for the Daily Digest."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, UTC
from enum import StrEnum
from typing import Any


class DigestPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ENTSubspecialty(StrEnum):
    OTOLOGY = "otology"
    RHINOLOGY = "rhinology"
    LARYNGOLOGY = "laryngology"
    HEAD_NECK_SURGERY = "head_neck_surgery"
    AUDIOLOGY = "audiology"
    VESTIBULAR = "vestibular"
    SLEEP_MEDICINE = "sleep_medicine"
    PEDIATRIC_ENT = "pediatric_ent"
    FACIAL_PLASTICS = "facial_plastic_surgery"
    SKULL_BASE = "skull_base_surgery"
    GENERAL_ENT = "general_ent"


ENT_TOPIC_DISPLAY = {
    ENTSubspecialty.OTOLOGY: "Otology",
    ENTSubspecialty.RHINOLOGY: "Rhinology",
    ENTSubspecialty.LARYNGOLOGY: "Laryngology",
    ENTSubspecialty.HEAD_NECK_SURGERY: "Head & Neck Surgery",
    ENTSubspecialty.AUDIOLOGY: "Audiology",
    ENTSubspecialty.VESTIBULAR: "Vestibular Disorders",
    ENTSubspecialty.SLEEP_MEDICINE: "Sleep Medicine",
    ENTSubspecialty.PEDIATRIC_ENT: "Pediatric ENT",
    ENTSubspecialty.FACIAL_PLASTICS: "Facial Plastic Surgery",
    ENTSubspecialty.SKULL_BASE: "Skull Base Surgery",
    ENTSubspecialty.GENERAL_ENT: "General ENT",
}

ENT_ICONS = {
    ENTSubspecialty.OTOLOGY: "🦻",
    ENTSubspecialty.RHINOLOGY: "👃",
    ENTSubspecialty.LARYNGOLOGY: "🗣️",
    ENTSubspecialty.HEAD_NECK_SURGERY: "🏥",
    ENTSubspecialty.AUDIOLOGY: "🔊",
    ENTSubspecialty.VESTIBULAR: "🌀",
    ENTSubspecialty.SLEEP_MEDICINE: "😴",
    ENTSubspecialty.PEDIATRIC_ENT: "👶",
    ENTSubspecialty.FACIAL_PLASTICS: "✨",
    ENTSubspecialty.SKULL_BASE: "🧠",
    ENTSubspecialty.GENERAL_ENT: "📋",
}


class EvidenceLevel(StrEnum):
    A = "A"   # High: RCT / meta-analysis
    B = "B"   # Moderate: cohort / case-control
    C = "C"   # Low: case series
    D = "D"   # Very low: expert opinion


class StudyDesign(StrEnum):
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    RCT = "rct"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CASE_SERIES = "case_series"
    CASE_REPORT = "case_report"
    NARRATIVE_REVIEW = "narrative_review"
    GUIDELINE = "guideline"
    BASIC_SCIENCE = "basic_science"


@dataclass(slots=True)
class DigestItem:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    publication_date: date | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    clinical_relevance: str = ""
    novelty: str = ""
    study_design: StudyDesign | None = None
    evidence_level: EvidenceLevel | None = None
    strengths: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    clinical_takeaway: str = ""
    summary_bullets: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    topics: list[ENTSubspecialty] = field(default_factory=list)
    clinical_importance: float = 0.0  # 0.0 - 1.0
    url: str = ""


@dataclass(slots=True)
class Topic:
    id: ENTSubspecialty
    display_name: str = ""
    icon: str = ""
    items: list[DigestItem] = field(default_factory=list)
    paper_count: int = 0
    summary: str = ""


@dataclass(slots=True)
class Digest:
    id: str
    period: DigestPeriod
    date: date
    title: str
    topics: list[Topic] = field(default_factory=list)
    items: list[DigestItem] = field(default_factory=list)
    total_papers: int = 0
    trending: list[DigestItem] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
