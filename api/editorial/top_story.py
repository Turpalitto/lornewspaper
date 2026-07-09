"""Top story selection algorithm.

Selects the single most important paper of the day based on:
  - Clinical importance score (weighted)
  - Evidence level
  - Journal reputation
  - Novelty (keywords: "first", "novel", "breakthrough")
  - Practice-changing potential (keywords: "recommend", "should", "change")
"""

from __future__ import annotations

import re
from typing import Any

from api.editorial.models import EditorialPaper, TopStory

_PRACTICE_CHANGE_KEYWORDS = [
    "should", "recommend", "guideline", "practice change",
    "standard of care", "first-line", "indication",
    "новый стандарт", "рекомендуется", "следует",
]

_NOVELTY_KEYWORDS = [
    "first", "novel", "breakthrough", "innovative", "pioneering",
    "first-in-class", "landmark", "milestone",
    "впервые", "новый", "прорыв", "инновационный",
]

_BREAKING_KEYWORDS = [
    "emergency", "urgent", "critical", "life-threatening",
    "significant", "substantial", "major",
    "критический", "значительный", "существенный",
]

_HIGH_IMPACT_JOURNALS = [
    "new england journal of medicine", "lancet", "jama", "bmj",
    "nature medicine", "nature",
    "otolaryngology", "laryngoscope",
]


def select_top_story(papers: list[EditorialPaper]) -> TopStory | None:
    """Select the single most important paper as the top story."""
    if not papers:
        return None

    scored = [(paper, _compute_top_story_score(paper)) for paper in papers]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_paper, best_score = scored[0]
    if best_score < 0.3:
        return None

    return TopStory(
        paper=best_paper,
        headline=_generate_headline(best_paper),
        why_it_matters=_generate_why_it_matters(best_paper),
        clinical_impact=_generate_clinical_impact(best_paper),
        key_finding=_extract_key_finding(best_paper),
        specialist_comment=_generate_specialist_comment(best_paper),
    )


def identify_breaking_findings(papers: list[EditorialPaper], threshold: float = 0.6) -> list[EditorialPaper]:
    """Identify papers with breaking/urgent findings."""
    breaking = []
    for paper in papers:
        score = _compute_top_story_score(paper)
        text = f"{paper.title} {paper.abstract}".lower()
        has_breaking_keyword = any(kw in text for kw in _BREAKING_KEYWORDS)
        if score > threshold or has_breaking_keyword:
            paper.is_breaking = True
            breaking.append(paper)
    return breaking


def _compute_top_story_score(paper: EditorialPaper) -> float:
    """Compute a composite top-story worthiness score."""
    score = paper.clinical_importance * 0.4
    text = f"{paper.title} {paper.abstract}".lower()

    # Novelty boost (0.0-0.2)
    novelty_matches = sum(1 for kw in _NOVELTY_KEYWORDS if kw in text)
    score += min(0.2, novelty_matches * 0.05)

    # Practice change boost (0.0-0.2)
    change_matches = sum(1 for kw in _PRACTICE_CHANGE_KEYWORDS if kw in text)
    score += min(0.2, change_matches * 0.04)

    # Journal boost (0.0-0.2)
    journal_lower = paper.journal.lower()
    if any(jn in journal_lower for jn in _HIGH_IMPACT_JOURNALS):
        score += 0.2

    return min(1.0, score)


def _generate_headline(paper: EditorialPaper) -> str:
    """Generate a headline for the top story."""
    return paper.title


def _generate_why_it_matters(paper: EditorialPaper) -> str:
    """Generate 'why it matters' summary."""
    text = f"{paper.title} {paper.abstract}"
    if paper.evidence_level in ("A", "B"):
        return (
            f"This {paper.evidence_level}-level evidence study addresses "
            f"a clinically important question in {', '.join(paper.topics[:2])}. "
            f"The findings have direct implications for clinical decision-making."
        )
    return (
        f"This study provides new insights into {', '.join(paper.topics[:2])}. "
        f"Clinicians should be aware of these findings."
    )


def _generate_clinical_impact(paper: EditorialPaper) -> str:
    """Generate clinical impact statement."""
    return paper.practice_change or "Further research is needed to determine the full clinical impact."


def _extract_key_finding(paper: EditorialPaper) -> str:
    """Extract or generate a key finding statement."""
    return paper.clinical_relevance or "See abstract for key findings."


def _generate_specialist_comment(paper: EditorialPaper) -> str:
    """Generate an editorial comment as if from a specialist."""
    if paper.evidence_level in ("A", "B"):
        return (
            f"This is a well-conducted study that provides "
            f"{'strong' if paper.evidence_level == 'A' else 'moderate'} evidence. "
            f"Clinicians should consider incorporating these findings into their practice."
        )
    return (
        f"While this study has limitations, it raises important questions "
        f"that warrant further investigation."
    )
