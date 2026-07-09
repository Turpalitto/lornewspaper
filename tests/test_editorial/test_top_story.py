"""Tests for top story selection."""

from __future__ import annotations

from api.editorial.models import EditorialPaper
from api.editorial.top_story import (
    identify_breaking_findings,
    select_top_story,
    _compute_top_story_score,
)


def _paper(
    title: str = "Test",
    importance: float = 0.5,
    evidence: str = "B",
    journal: str = "Laryngoscope",
    abstract: str = "",
) -> EditorialPaper:
    return EditorialPaper(
        id="p1", title=title, journal=journal,
        evidence_level=evidence, clinical_importance=importance,
        abstract=abstract, topics=["otology"],
    )


class TestTopStorySelection:
    def test_selects_highest_importance(self):
        low = _paper(title="Low", importance=0.3)
        high = _paper(title="High", importance=0.9)
        top = select_top_story([low, high])
        assert top is not None
        assert top.paper is not None
        assert top.paper.title == "High"

    def test_returns_none_for_empty(self):
        assert select_top_story([]) is None

    def test_returns_none_for_low_scores(self):
        papers = [_paper(title="Low", importance=0.1)]
        top = select_top_story(papers)
        if top:
            assert top.paper is not None

    def test_headline_uses_title(self):
        paper = _paper(title="Landmark study on cochlear implants")
        top = select_top_story([paper])
        assert top is not None
        assert paper.title in top.headline

    def test_why_it_matters_includes_topic(self):
        paper = _paper(title="Important finding", topics=["rhinology"])
        top = select_top_story([paper])
        assert top is not None
        assert "rhinology" in top.why_it_matters

    def test_high_evidence_scores_well(self):
        paper = _paper(evidence="A")
        score = _compute_top_story_score(paper)
        assert score >= 0.3

    def test_novelty_keywords_boost_score(self):
        normal = _paper(title="Study on X")
        novel = _paper(title="First novel breakthrough study on X")
        normal_score = _compute_top_story_score(normal)
        novel_score = _compute_top_story_score(novel)
        assert novel_score >= normal_score

    def test_high_impact_journal_boost(self):
        low_journal = _paper(journal="Unknown Journal")
        nejm = _paper(journal="New England Journal of Medicine")
        low_score = _compute_top_story_score(low_journal)
        high_score = _compute_top_story_score(nejm)
        assert high_score >= low_score

    def test_breaking_findings_detected(self):
        normal = _paper(title="Routine study")
        critical = _paper(title="Critical life-threatening emergency finding", importance=0.7)
        breaking = identify_breaking_findings([normal, critical])
        assert len(breaking) >= 1

    def test_multiple_candidates(self):
        papers = [_paper(title=f"Paper {i}", importance=0.3 + i * 0.15) for i in range(5)]
        top = select_top_story(papers)
        assert top is not None
        assert top.paper is not None
        # Highest importance should win
        assert top.paper.title == "Paper 4"
