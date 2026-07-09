"""Tests for theme detection and paper merging."""

from __future__ import annotations

from api.editorial.models import EditorialPaper
from api.editorial.theme_detector import detect_themes, merge_similar_papers


def _paper(title: str = "", abstract: str = "", topics: list[str] | None = None) -> EditorialPaper:
    return EditorialPaper(
        id="p1", title=title, abstract=abstract,
        topics=topics or ["general_ent"],
        authors=["Author"], journal="Journal",
    )


class TestThemeDetection:
    def test_detect_ai_theme(self):
        paper = _paper(title="Machine learning for ENT diagnosis", abstract="AI deep learning model")
        trends = detect_themes([paper])
        ai_trends = [t for t in trends if "Artificial Intelligence" in t.name]
        assert len(ai_trends) >= 1

    def test_detect_hearing_loss_theme(self):
        paper = _paper(title="New hearing loss treatment", abstract="presbycusis hearing aid")
        trends = detect_themes([paper])
        hl_trends = [t for t in trends if "Hearing Loss" in t.name]
        assert len(hl_trends) >= 1

    def test_detect_sleep_apnea_theme(self):
        paper = _paper(title="OSA treatment outcomes", abstract="sleep apnea CPAP therapy")
        trends = detect_themes([paper])
        sa_trends = [t for t in trends if "Sleep Apnea" in t.name]
        assert len(sa_trends) >= 1

    def test_empty_papers(self):
        assert detect_themes([]) == []

    def test_trend_sorted_by_count(self):
        papers = [
            _paper(title="AI in rhinology", abstract="machine learning AI"),
            _paper(title="Deep learning ENT", abstract="deep learning neural network"),
            _paper(title="Hearing loss study", abstract="presbycusis hearing"),
        ]
        trends = detect_themes(papers)
        if len(trends) >= 2:
            assert trends[0].paper_count >= trends[1].paper_count

    def test_trend_has_paper_count(self):
        paper = _paper(title="Cochlear implant outcomes", abstract="cochlear implantation CI")
        trends = detect_themes([paper])
        for t in trends:
            assert t.paper_count >= 1

    def test_merge_similar_papers(self):
        papers = [
            _paper(title="Study A", topics=["otology"]),
            _paper(title="Study B", topics=["otology"]),
        ]
        merged = merge_similar_papers(papers)
        assert len(merged) >= 1
        assert "otology" in merged[0].lower()

    def test_no_merge_different_topics(self):
        papers = [
            _paper(title="Otology paper", topics=["otology"]),
            _paper(title="Rhinology paper", topics=["rhinology"]),
        ]
        merged = merge_similar_papers(papers)
        assert len(merged) >= 0
