"""Tests for digest ranking algorithm."""

from __future__ import annotations

from datetime import date

from api.digest.models import DigestItem, ENTSubspecialty, EvidenceLevel, StudyDesign
from api.digest.ranking import compute_clinical_importance, rank_items


def _make_item(
    title: str = "Test Paper",
    evidence: EvidenceLevel | None = None,
    design: StudyDesign | None = None,
    journal: str = "",
    pub_date: date | None = None,
    topics: list[ENTSubspecialty] | None = None,
) -> DigestItem:
    return DigestItem(
        id="test-1",
        title=title,
        journal=journal,
        publication_date=pub_date or date.today(),
        evidence_level=evidence,
        study_design=design,
        topics=topics or [ENTSubspecialty.GENERAL_ENT],
    )


class TestRanking:
    def test_meta_analysis_ranked_higher_than_case_report(self):
        meta = _make_item(evidence=EvidenceLevel.A, design=StudyDesign.META_ANALYSIS)
        case = _make_item(evidence=EvidenceLevel.D, design=StudyDesign.CASE_REPORT)
        assert compute_clinical_importance(meta) > compute_clinical_importance(case)

    def test_rct_ranked_higher_than_expert_opinion(self):
        rct = _make_item(evidence=EvidenceLevel.A, design=StudyDesign.RCT)
        expert = _make_item(evidence=EvidenceLevel.D, design=None)
        assert compute_clinical_importance(rct) > compute_clinical_importance(expert)

    def test_top_journal_boosts_score(self):
        high_journal = _make_item(journal="New England Journal of Medicine", design=StudyDesign.RCT)
        low_journal = _make_item(journal="Unknown Journal", design=StudyDesign.RCT)
        assert compute_clinical_importance(high_journal) > compute_clinical_importance(low_journal)

    def test_recent_paper_scores_higher(self):
        recent = _make_item(pub_date=date.today())
        old = _make_item(pub_date=date(2020, 1, 1))
        assert compute_clinical_importance(recent) >= compute_clinical_importance(old)

    def test_head_neck_scored_higher_than_general(self):
        hn = _make_item(topics=[ENTSubspecialty.HEAD_NECK_SURGERY])
        general = _make_item(topics=[ENTSubspecialty.GENERAL_ENT])
        assert compute_clinical_importance(hn) > compute_clinical_importance(general)

    def test_score_in_range(self):
        item = _make_item(evidence=EvidenceLevel.B, design=StudyDesign.COHORT)
        score = compute_clinical_importance(item)
        assert 0.0 <= score <= 1.0

    def test_rank_items_orders_by_importance(self):
        low = _make_item(title="Low", evidence=EvidenceLevel.D)
        high = _make_item(title="High", evidence=EvidenceLevel.A)
        items = rank_items([low, high])
        assert items[0].title == "High"
        assert items[1].title == "Low"

    def test_empty_items_returns_empty(self):
        assert rank_items([]) == []
