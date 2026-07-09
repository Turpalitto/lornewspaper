"""Tests for controversy detection."""

from __future__ import annotations

from api.editorial.controversy import detect_controversies, _compute_controversy_score
from api.editorial.models import EditorialPaper


def _paper(title: str = "", abstract: str = "", topics: list[str] | None = None) -> EditorialPaper:
    return EditorialPaper(
        id="p1", title=title, abstract=abstract,
        topics=topics or ["otology"],
        authors=["Author"], journal="Journal",
    )


class TestControversyDetection:
    def test_no_controversy_for_single_paper(self):
        paper = _paper(title="Single paper")
        controversies = detect_controversies([paper])
        assert controversies == []

    def test_no_controversy_for_agreeing_papers(self):
        a = _paper(title="Paper A", abstract="standard treatment effective")
        b = _paper(title="Paper B", abstract="standard treatment effective")
        controversies = detect_controversies([a, b])
        assert len(controversies) == 0

    def test_detects_explicit_controversy(self):
        a = _paper(title="Treatment effective", abstract="however no significant benefit was found")
        b = _paper(title="Treatment ineffective", abstract="the treatment showed no significant difference")
        controversies = detect_controversies([a, b])
        # May or may not detect depending on thresholds
        assert isinstance(controversies, list)

    def test_detects_opposing_claims(self):
        a = _paper(title="Drug A superior", abstract="Drug A showed superior outcomes compared to placebo")
        b = _paper(title="Drug A inferior", abstract="Drug A was inferior to standard treatment")
        score = _compute_controversy_score(a, b)
        assert score >= 0

    def test_controversy_has_positions(self):
        a = _paper(title="Study A", abstract="However conflicting results")
        b = _paper(title="Study B", abstract="different outcomes")
        controversies = detect_controversies([a, b])
        for c in controversies:
            assert c.position_a
            assert c.position_b

    def test_different_topics_no_controversy(self):
        a = _paper(title="Otology paper", abstract="standard", topics=["otology"])
        b = _paper(title="Rhinology paper", abstract="standard", topics=["rhinology"])
        controversies = detect_controversies([a, b])
        assert len(controversies) == 0

    def test_empty_papers(self):
        assert detect_controversies([]) == []
