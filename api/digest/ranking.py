"""Paper ranking algorithm.

Ranks papers by:
  - Clinical importance (0.0-1.0)
  - Evidence level (A/B/C/D)
  - Journal quality (impact factor tier)
  - Novelty
  - Recency
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from api.digest.models import DigestItem, ENTSubspecialty, EvidenceLevel, StudyDesign

_EVIDENCE_WEIGHTS = {
    EvidenceLevel.A: 1.0,
    EvidenceLevel.B: 0.7,
    EvidenceLevel.C: 0.4,
    EvidenceLevel.D: 0.2,
}

_STUDY_WEIGHTS = {
    StudyDesign.META_ANALYSIS: 1.0,
    StudyDesign.SYSTEMATIC_REVIEW: 0.95,
    StudyDesign.GUIDELINE: 0.9,
    StudyDesign.RCT: 0.85,
    StudyDesign.COHORT: 0.6,
    StudyDesign.CASE_CONTROL: 0.5,
    StudyDesign.CASE_SERIES: 0.3,
    StudyDesign.CASE_REPORT: 0.2,
    StudyDesign.NARRATIVE_REVIEW: 0.15,
    StudyDesign.BASIC_SCIENCE: 0.25,
}

_JOURNAL_TIERS: dict[str, float] = {
    "new england journal of medicine": 1.0,
    "lancet": 1.0,
    "jama": 1.0,
    "bmj": 0.95,
    "otolaryngology–head and neck surgery": 0.85,
    "laryngoscope": 0.75,
    "international journal of pediatric otorhinolaryngology": 0.7,
    "european archives of oto-rhino-laryngology": 0.65,
    "otology & neurotology": 0.65,
    "clinical otolaryngology": 0.65,
    "head & neck": 0.7,
    "journal of vestibular research": 0.55,
    "sleep": 0.75,
    "facial plastic surgery": 0.5,
}

_TOPIC_IMPORTANCE: dict[ENTSubspecialty, float] = {
    ENTSubspecialty.HEAD_NECK_SURGERY: 0.9,
    ENTSubspecialty.PEDIATRIC_ENT: 0.85,
    ENTSubspecialty.OTOLOGY: 0.8,
    ENTSubspecialty.SLEEP_MEDICINE: 0.8,
    ENTSubspecialty.SKULL_BASE: 0.8,
    ENTSubspecialty.LARYNGOLOGY: 0.75,
    ENTSubspecialty.RHINOLOGY: 0.7,
    ENTSubspecialty.FACIAL_PLASTICS: 0.6,
    ENTSubspecialty.AUDIOLOGY: 0.6,
    ENTSubspecialty.VESTIBULAR: 0.6,
    ENTSubspecialty.GENERAL_ENT: 0.5,
}


def compute_clinical_importance(item: DigestItem) -> float:
    """Compute a composite clinical importance score (0.0-1.0)."""
    score = 0.0

    # Evidence level (0.0-0.3)
    if item.evidence_level:
        score += _EVIDENCE_WEIGHTS.get(item.evidence_level, 0.2) * 0.3
    else:
        score += 0.1

    # Study design (0.0-0.25)
    if item.study_design:
        score += _STUDY_WEIGHTS.get(item.study_design, 0.3) * 0.25
    else:
        score += 0.05

    # Journal quality (0.0-0.2)
    journal_lower = item.journal.lower()
    journal_weight = 0.1
    for name, weight in _JOURNAL_TIERS.items():
        if name in journal_lower:
            journal_weight = weight
            break
    score += journal_weight * 0.2

    # Topic importance (0.0-0.15)
    topic_weight = 0.5
    for topic in item.topics:
        topic_weight = max(topic_weight, _TOPIC_IMPORTANCE.get(topic, 0.5))
    score += topic_weight * 0.15

    # Recency (0.0-0.1)
    if item.publication_date:
        days_ago = (date.today() - item.publication_date).days
        recency = max(0.0, 1.0 - (days_ago / 365))
        score += recency * 0.1
    else:
        score += 0.02

    return round(min(1.0, score), 2)


def rank_items(items: list[DigestItem]) -> list[DigestItem]:
    """Rank items by clinical importance descending."""
    for item in items:
        item.clinical_importance = compute_clinical_importance(item)
    items.sort(key=lambda x: x.clinical_importance, reverse=True)
    return items
