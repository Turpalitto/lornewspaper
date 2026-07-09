"""Tests for digest grouping algorithm."""

from __future__ import annotations

from api.digest.grouping import assign_topic, assign_study_design, extract_tags, group_by_topic
from api.digest.models import DigestItem, ENTSubspecialty, StudyDesign


def _item(title: str = "", abstract: str = "") -> DigestItem:
    return DigestItem(id="test", title=title, abstract=abstract)


class TestGrouping:
    def test_assign_topic_by_keyword(self):
        item = _item(title="New developments in cochlear implant surgery")
        topics = assign_topic(item)
        assert ENTSubspecialty.OTOLOGY in topics

    def test_assign_topic_rhinology(self):
        item = _item(title="Endoscopic sinus surgery for chronic rhinosinusitis")
        topics = assign_topic(item)
        assert ENTSubspecialty.RHINOLOGY in topics

    def test_assign_topic_head_neck(self):
        item = _item(title="HPV-related oropharyngeal squamous cell carcinoma")
        topics = assign_topic(item)
        assert ENTSubspecialty.HEAD_NECK_SURGERY in topics

    def test_assign_topic_general_fallback(self):
        item = _item(title="General ENT research")
        topics = assign_topic(item)
        assert len(topics) >= 1

    def test_assign_study_design_meta_analysis(self):
        item = _item(abstract="A systematic review and meta-analysis of RCTs")
        assert assign_study_design(item) == StudyDesign.META_ANALYSIS

    def test_assign_study_design_rct(self):
        item = _item(abstract="We conducted a randomized controlled trial")
        assert assign_study_design(item) == StudyDesign.RCT

    def test_assign_study_design_case_report(self):
        item = _item(abstract="We report a case of")
        assert assign_study_design(item) == StudyDesign.CASE_REPORT

    def test_assign_study_design_guideline(self):
        item = _item(abstract="Clinical practice guideline for")
        assert assign_study_design(item) == StudyDesign.GUIDELINE

    def test_assign_study_design_none(self):
        item = _item(abstract="This paper discusses")
        assert assign_study_design(item) == StudyDesign.NARRATIVE_REVIEW

    def test_extract_tags(self):
        item = _item(
            title="Pediatric cochlear implant outcomes",
            abstract="A cohort study of surgical treatment outcomes in children",
        )
        tags = extract_tags(item)
        assert len(tags) >= 1

    def test_group_by_topic(self):
        otology = _item(title="Otitis media treatment")
        otology.topics = [ENTSubspecialty.OTOLOGY]
        rhinology = _item(title="Nasal polyps")
        rhinology.topics = [ENTSubspecialty.RHINOLOGY]

        groups = group_by_topic([otology, rhinology])
        assert ENTSubspecialty.OTOLOGY in groups
        assert ENTSubspecialty.RHINOLOGY in groups
        assert len(groups[ENTSubspecialty.OTOLOGY]) == 1
