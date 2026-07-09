"""Paper grouping algorithm.

Groups papers by:
  - Disease / condition
  - Procedure / intervention
  - ENT subspecialty topic
  - Study design type
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from api.digest.models import DigestItem, ENTSubspecialty, StudyDesign

_DISEASE_KEYWORDS: dict[str, ENTSubspecialty] = {
    "otitis media": ENTSubspecialty.OTOLOGY,
    "hearing loss": ENTSubspecialty.AUDIOLOGY,
    "tinnitus": ENTSubspecialty.OTOLOGY,
    "vertigo": ENTSubspecialty.VESTIBULAR,
    "meniere": ENTSubspecialty.VESTIBULAR,
    "sinusitis": ENTSubspecialty.RHINOLOGY,
    "nasal polyp": ENTSubspecialty.RHINOLOGY,
    "sleep apnea": ENTSubspecialty.SLEEP_MEDICINE,
    "tonsillectomy": ENTSubspecialty.PEDIATRIC_ENT,
    "laryngeal cancer": ENTSubspecialty.LARYNGOLOGY,
    "head and neck cancer": ENTSubspecialty.HEAD_NECK_SURGERY,
    "thyroid": ENTSubspecialty.HEAD_NECK_SURGERY,
    "cochlear implant": ENTSubspecialty.OTOLOGY,
    "skull base": ENTSubspecialty.SKULL_BASE,
    "rhinoplasty": ENTSubspecialty.FACIAL_PLASTICS,
    "facial nerve": ENTSubspecialty.FACIAL_PLASTICS,
    "dysphonia": ENTSubspecialty.LARYNGOLOGY,
    "presbycusis": ENTSubspecialty.AUDIOLOGY,
    "cholesteatoma": ENTSubspecialty.OTOLOGY,
    "fess": ENTSubspecialty.RHINOLOGY,
    "bppv": ENTSubspecialty.VESTIBULAR,
    "cpap": ENTSubspecialty.SLEEP_MEDICINE,
    "adenoidectomy": ENTSubspecialty.PEDIATRIC_ENT,
    "parotid": ENTSubspecialty.HEAD_NECK_SURGERY,
    "neck dissection": ENTSubspecialty.HEAD_NECK_SURGERY,
}

_PROCEDURE_KEYWORDS: dict[str, list[str]] = {
    "endoscopic surgery": ["endoscopic", "fess", "ess"],
    "microsurgery": ["microscope", "microsurgical", "microvascular"],
    "laser surgery": ["laser", "co2 laser", "krypton"],
    "implant": ["implant", "cochlear implant", "bone-anchored"],
    "reconstruction": ["reconstruct", "flap", "graft", "free flap"],
    "radiation therapy": ["radiation", "radiotherapy", "imrt"],
}


def assign_topic(item: DigestItem) -> list[ENTSubspecialty]:
    """Assign ENT subspecialty topic(s) to a paper based on title + abstract."""
    text = f"{item.title} {item.abstract}".lower()
    topics: list[ENTSubspecialty] = []

    for keyword, topic in _DISEASE_KEYWORDS.items():
        if keyword in text:
            topics.append(topic)

    # If no keyword match, try broader mapping
    if not topics:
        for topic in ENTSubspecialty:
            if topic != ENTSubspecialty.GENERAL_ENT:
                topic_name = topic.value.replace("_", " ")
                if topic_name in text:
                    topics.append(topic)

    if not topics:
        topics.append(ENTSubspecialty.GENERAL_ENT)

    return list(set(topics))


def assign_study_design(item: DigestItem) -> StudyDesign | None:
    """Detect study design from title + abstract."""
    text = f"{item.title} {item.abstract}".lower()

    if "meta-analysis" in text or "meta analysis" in text:
        return StudyDesign.META_ANALYSIS
    if "systematic review" in text:
        return StudyDesign.SYSTEMATIC_REVIEW
    if "randomized" in text or "rct" in text:
        return StudyDesign.RCT
    if "guideline" in text or "recommendation" in text:
        return StudyDesign.GUIDELINE
    if "cohort" in text or "prospective" in text:
        return StudyDesign.COHORT
    if "case-control" in text or "retrospective" in text:
        return StudyDesign.CASE_CONTROL
    if "case report" in text:
        return StudyDesign.CASE_REPORT
    if "case series" in text:
        return StudyDesign.CASE_SERIES
    if "review" in text:
        return StudyDesign.NARRATIVE_REVIEW
    if "vitro" in text or "vivo" in text or "cell" in text:
        return StudyDesign.BASIC_SCIENCE

    return None


def group_by_topic(items: list[DigestItem]) -> dict[ENTSubspecialty, list[DigestItem]]:
    """Group digest items by ENT subspecialty topic."""
    groups: dict[ENTSubspecialty, list[DigestItem]] = defaultdict(list)
    for item in items:
        for topic in item.topics:
            groups[topic].append(item)
    return dict(groups)


def extract_tags(item: DigestItem) -> list[str]:
    """Extract relevant tags from paper content."""
    text = f"{item.title} {item.abstract}".lower()
    tags: list[str] = []

    # Extract study design
    if item.study_design:
        tags.append(item.study_design.value.replace("_", " "))

    # Extract key clinical terms
    clinical_terms = [
        "diagnosis", "treatment", "surgery", "medical therapy",
        "imaging", "pathology", "epidemiology", "outcomes",
        "quality of life", "complications", "screening",
        "pediatric", "adult", "geriatric",
    ]
    for term in clinical_terms:
        if term in text:
            tags.append(term)

    return list(set(tags))
