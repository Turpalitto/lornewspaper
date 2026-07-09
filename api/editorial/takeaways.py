"""Clinical takeaway generation.

Produces:
  - Today's Clinical Takeaway: "What should an ENT surgeon remember today?"
  - Executive summary (3 bullet points)
  - Practice impact statements
"""

from __future__ import annotations

from typing import Any

from api.editorial.models import ClinicalTakeaway, EditorialPaper

_CLINICAL_IMPORTANCE_PHRASES = [
    "Consider updating your clinical practice based on",
    "Be aware of new evidence regarding",
    "Take note of recent findings on",
    "Incorporate new knowledge about",
]


def generate_clinical_takeaway(papers: list[EditorialPaper]) -> ClinicalTakeaway:
    """Generate 'What should an ENT surgeon remember today?'"""
    if not papers:
        return ClinicalTakeaway(
            headline="No significant new findings today.",
            body="All current recommendations remain unchanged.",
            action_items=["Continue current practice."],
        )

    # Focus on highest-impact paper
    top_paper = max(papers, key=lambda p: p.clinical_importance)

    return ClinicalTakeaway(
        headline=f"Key takeaway: {top_paper.title[:100]}",
        body=_generate_takeaway_body(top_paper),
        action_items=_generate_action_items(papers[:3]),
    )


def generate_executive_summary(papers: list[EditorialPaper]) -> list[str]:
    """Generate a 3-bullet executive summary."""
    if not papers:
        return ["No new publications today."]

    bullets: list[str] = []

    # Bullet 1: Top story
    top = max(papers, key=lambda p: p.clinical_importance)
    bullets.append(f"{top.title[:120]} — {', '.join(top.authors[:2])} ({top.journal})")

    # Bullet 2: Practice-changing finding
    practice_changes = [p for p in papers if p.practice_change]
    if practice_changes:
        pc = max(practice_changes, key=lambda p: p.clinical_importance)
        bullets.append(f"Practice impact: {pc.practice_change[:150]}")
    else:
        bullets.append(f"{len(papers)} new ENT publications reviewed this period.")

    # Bullet 3: Overall assessment
    high_quality = len([p for p in papers if p.evidence_level in ("A", "B")])
    if high_quality > 0:
        bullets.append(
            f"{high_quality} high-quality stud{'y' if high_quality == 1 else 'ies'} "
            f"(evidence level A/B) among {len(papers)} new papers."
        )
    else:
        bullets.append("Further high-quality research is needed in these areas.")

    return bullets


def _generate_takeaway_body(paper: EditorialPaper) -> str:
    """Generate the body of the clinical takeaway."""
    return (
        f"A new study in {paper.journal} ({paper.evidence_level or 'N/A'} evidence) "
        f"by {', '.join(paper.authors[:3])} examines {paper.title[:80]}. "
        f"{paper.clinical_relevance or 'This may affect clinical decision-making.'}"
    )


def _generate_action_items(papers: list[EditorialPaper]) -> list[str]:
    """Generate actionable clinical recommendations."""
    actions = []
    for paper in papers:
        if paper.practice_change:
            actions.append(paper.practice_change[:120])
        elif paper.evidence_level in ("A", "B"):
            actions.append(
                f"Review findings on {paper.title[:80]} "
                f"({paper.evidence_level} evidence)"
            )

    if not actions:
        actions.append("Continue current evidence-based practice.")

    return actions[:3]
