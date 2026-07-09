"""Extract structured recommendations from clinical guideline text.

Parses guidelines for:
  - "We recommend..." / "Мы рекомендуем..." statements
  - Recommendation strength (strong, conditional, not recommended)
  - Evidence level (A, B, C, D)
  - PICO elements (Population, Intervention, Comparator, Outcomes)
  - Contraindications, pregnancy, pediatric information
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from clinical_assistant.models.guideline import (
    ChildrenCategory,
    EvidenceLevel,
    PregnancyCategory,
    Recommendation,
    RecommendationStrength,
)

# Russian recommendation patterns
_RU_RECOMMEND_RE = re.compile(
    r"(?:мы\s+)?рекоменду(?:ем|ется|ют)\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)
_RU_STRONGLY_RECOMMEND_RE = re.compile(
    r"(?:настоятельно\s+)?рекоменду(?:ем|ется|ют)\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)
_RU_NOT_RECOMMEND_RE = re.compile(
    r"(?:не\s+)?рекоменду(?:ем|ется|ют)\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)

# English recommendation patterns
_EN_RECOMMEND_RE = re.compile(
    r"(?:we\s+)?recommend(?:s|ed)?\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)
_EN_STRONGLY_RECOMMEND_RE = re.compile(
    r"strongly\s+recommend(?:s|ed)?\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)
_EN_NOT_RECOMMEND_RE = re.compile(
    r"(?:do\s+not|should\s+not|not\s+recommended)\s+(?P<text>[^.!?]+[.!?])",
    re.IGNORECASE,
)

# Evidence level patterns
_EVIDENCE_LEVEL_RE = re.compile(
    r"(?:уровень\s+)?доказательств(?:а|о|)?\s*(?:-\s*)?(?P<level>[ABCD])(?:\s*\([^)]*\))?",
    re.IGNORECASE,
)
_EN_EVIDENCE_LEVEL_RE = re.compile(
    r"(?:evidence\s+)?level\s+(?P<level>[ABCD])\b",
    re.IGNORECASE,
)
_GRADE_RE = re.compile(
    r"(?:сила\s+)?рекомендации\s*(?:-\s*)?(?P<grade>[123ABC])",
    re.IGNORECASE,
)

# PICO extraction patterns
_PICO_POPULATION_RE = re.compile(
    r"(?:у\s+)?пациентов?\s+(?:с|со)?\s*(?P<population>[^;,.]+)",
    re.IGNORECASE,
)

# Contraindication patterns
_CONTRAINDICATION_RE = re.compile(
    r"(?:противопоказан(?:о|а|ы)?|не\s+следует\s+применять)\s+(?P<text>[^.!?]+)",
    re.IGNORECASE,
)

# Pregnancy patterns
_PREGNANCY_SAFE_RE = re.compile(
    r"(?:может\s+)?применяться\s+(?:при\s+)?беременност",
    re.IGNORECASE,
)
_PREGNANCY_CAUTION_RE = re.compile(
    r"(?:с\s+)?осторожностью\s+(?:при\s+)?беременност",
    re.IGNORECASE,
)
_PREGNANCY_CONTRA_RE = re.compile(
    r"(?:противопоказан|не\s+рекомендуется)\s+(?:при\s+)?беременност",
    re.IGNORECASE,
)


class RecommendationExtractor:
    """Extract structured recommendations from guideline text."""

    def extract(self, text: str, guideline_id: str = "", section_id: str = "") -> list[Recommendation]:
        """Extract all recommendations from a text block."""
        recommendations: list[Recommendation] = []
        seen_hashes: set[str] = set()

        patterns = [
            (self._extract_ru_strong, "ru"),
            (self._extract_ru_recommend, "ru"),
            (self._extract_ru_not_recommend, "ru"),
            (self._extract_en_strong, "en"),
            (self._extract_en_recommend, "en"),
            (self._extract_en_not_recommend, "en"),
        ]

        for extract_fn, lang in patterns:
            for rec in extract_fn(text):
                rec.source_guideline_id = guideline_id
                rec.source_section_id = section_id
                rec.source_text_hash = self._hash_text(rec.text_ru or rec.text_en)
                if rec.source_text_hash not in seen_hashes:
                    seen_hashes.add(rec.source_text_hash)
                    recommendations.append(rec)

        self._enrich_with_context(text, recommendations)
        return recommendations

    def extract_from_section(self, section_text: str, heading: str, guideline_id: str, section_id: str) -> list[Recommendation]:
        """Extract recommendations from a single guideline section."""
        recs = self.extract(section_text, guideline_id, section_id)
        for rec in recs:
            if heading and not rec.population:
                rec.population = heading
        return recs

    def _extract_ru_strong(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _RU_STRONGLY_RECOMMEND_RE.finditer(text):
            recs.append(Recommendation(
                text_ru=match.group("text").strip(),
                strength=RecommendationStrength.STRONG,
            ))
        return recs

    def _extract_ru_recommend(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _RU_RECOMMEND_RE.finditer(text):
            matched = match.group("text").strip()
            if any(kw in matched.lower() for kw in ["настоятельно", "strongly"]):
                continue
            if any(kw in matched.lower() for kw in ["не рекоменду", "not recommend"]):
                continue
            recs.append(Recommendation(
                text_ru=matched,
                strength=RecommendationStrength.CONDITIONAL,
            ))
        return recs

    def _extract_ru_not_recommend(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _RU_NOT_RECOMMEND_RE.finditer(text):
            recs.append(Recommendation(
                text_ru=match.group("text").strip(),
                strength=RecommendationStrength.NOT_RECOMMENDED,
            ))
        return recs

    def _extract_en_strong(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _EN_STRONGLY_RECOMMEND_RE.finditer(text):
            recs.append(Recommendation(
                text_en=match.group("text").strip(),
                strength=RecommendationStrength.STRONG,
            ))
        return recs

    def _extract_en_recommend(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _EN_RECOMMEND_RE.finditer(text):
            matched = match.group("text").strip()
            if "strongly" in matched.lower():
                continue
            if any(kw in matched.lower() for kw in ["do not", "should not", "not recommend"]):
                continue
            recs.append(Recommendation(
                text_en=matched,
                strength=RecommendationStrength.CONDITIONAL,
            ))
        return recs

    def _extract_en_not_recommend(self, text: str) -> list[Recommendation]:
        recs = []
        for match in _EN_NOT_RECOMMEND_RE.finditer(text):
            recs.append(Recommendation(
                text_en=match.group("text").strip(),
                strength=RecommendationStrength.NOT_RECOMMENDED,
            ))
        return recs

    def _enrich_with_context(self, text: str, recommendations: list[Recommendation]) -> None:
        """Add evidence level, contraindications, pregnancy info to recommendations."""
        common_level = self._extract_evidence_level(text)
        contraindications = self._extract_contraindications(text)
        pregnancy = self._classify_pregnancy(text)

        for rec in recommendations:
            if not rec.evidence_level or rec.evidence_level == EvidenceLevel.EXPERT_OPINION:
                rec.evidence_level = common_level
            if contraindications:
                rec.contraindications = contraindications
            if pregnancy:
                rec.pregnancy = pregnancy

    def _extract_evidence_level(self, text: str) -> EvidenceLevel:
        match = _EVIDENCE_LEVEL_RE.search(text) or _EN_EVIDENCE_LEVEL_RE.search(text)
        if match:
            level = match.group("level").upper()
            for ev in EvidenceLevel:
                if ev.value == level:
                    return ev
        return EvidenceLevel.EXPERT_OPINION

    def _extract_contraindications(self, text: str) -> list[str]:
        return [m.group("text").strip() for m in _CONTRAINDICATION_RE.finditer(text)]

    def _classify_pregnancy(self, text: str) -> PregnancyCategory | None:
        if _PREGNANCY_CONTRA_RE.search(text):
            return PregnancyCategory.CONTRAINDICATED
        if _PREGNANCY_CAUTION_RE.search(text):
            return PregnancyCategory.CAUTION
        if _PREGNANCY_SAFE_RE.search(text):
            return PregnancyCategory.SAFE
        return None

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
