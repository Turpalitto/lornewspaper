"""Research controversy detection.

Identifies papers with conflicting findings or recommendations
on the same clinical topic.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from api.editorial.models import EditorialPaper, ResearchControversy

# Controversy indicator keywords
_CONTRADICTION_PATTERNS = [
    (r"(?:however|but|yet|although|conversely|in contrast)", 0.3),
    (r"(?:no significant|not associated|no difference|not superior)", 0.5),
    (r"(?:failed to|did not|does not)", 0.4),
    (r"(?:controversy|controversial|debate|unresolved)", 0.8),
    (r"(?:conflicting|inconsistent|discrepancy|disagree)", 0.9),
    (r"(?:although|while|despite|however|однако|несмотря)", 0.3),
    (r"(?:не подтвердил|не выявил|не обнаружил|не показал)", 0.6),
    (r"(?:разногласия|противоречия|дискуссия|спорный)", 0.8),
]

_OPPOSITE_DIRECTIONS: list[tuple[list[str], list[str]]] = [
    (["increase", "improve", "superior"], ["decrease", "inferior", "worse"]),
    (["recommend", "effective", "benefit"], ["not recommend", "ineffective", "no benefit"]),
    (["safe"], ["unsafe", "toxic", "adverse"]),
]


def detect_controversies(papers: list[EditorialPaper]) -> list[ResearchControversy]:
    """Detect research controversies across papers.

    Groups papers by topic, then checks for:
    - Explicit contradiction keywords
    - Opposing directional claims
    - Opposing recommendations
    """
    topic_papers: dict[str, list[EditorialPaper]] = defaultdict(list)

    for paper in papers:
        for topic in paper.topics:
            topic_papers[topic].append(paper)

    controversies: list[ResearchControversy] = []

    for topic, topic_group in topic_papers.items():
        if len(topic_group) < 2:
            continue

        for i in range(len(topic_group)):
            for j in range(i + 1, len(topic_group)):
                a, b = topic_group[i], topic_group[j]
                score = _compute_controversy_score(a, b)
                if score >= 0.5:
                    controversy = _build_controversy(topic, a, b)
                    controversies.append(controversy)
                    a.is_controversial = True
                    b.is_controversial = True

    return controversies


def _compute_controversy_score(a: EditorialPaper, b: EditorialPaper) -> float:
    """Compute how likely two papers disagree (0.0-1.0)."""
    score = 0.0
    text_a = f"{a.title} {a.abstract}".lower()
    text_b = f"{b.title} {b.abstract}".lower()

    # Check explicit contradiction keywords
    for pattern, weight in _CONTRADICTION_PATTERNS:
        if re.search(pattern, text_a) or re.search(pattern, text_b):
            score += weight

    # Check opposite directions
    for pos_words, neg_words in _OPPOSITE_DIRECTIONS:
        a_pos = any(w in text_a for w in pos_words)
        a_neg = any(w in text_a for w in neg_words)
        b_pos = any(w in text_b for w in pos_words)
        b_neg = any(w in text_b for w in neg_words)

        if (a_pos and b_neg) or (a_neg and b_pos):
            score += 0.4

    return min(1.0, score)


def _build_controversy(topic: str, a: EditorialPaper, b: EditorialPaper) -> ResearchControversy:
    """Build a ResearchControversy from two apparently conflicting papers."""
    return ResearchControversy(
        title=f"Conflicting evidence on {topic}",
        topic=topic,
        position_a=f"{a.authors[0] if a.authors else 'Authors'} report findings on {a.title[:80]}",
        position_a_supporting_papers=[a.id],
        position_b=f"{b.authors[0] if b.authors else 'Authors'} report findings on {b.title[:80]}",
        position_b_supporting_papers=[b.id],
        resolution=(
            "The apparent disagreement may reflect differences in study population, "
            "methodology, or outcome measures. Further research is needed "
            "to reconcile these findings."
        ),
        clinical_guidance=(
            "Clinicians should consider both perspectives and evaluate "
            "the evidence quality when making treatment decisions."
        ),
    )
