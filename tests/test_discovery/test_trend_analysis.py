"""Tests for trend analysis."""

from __future__ import annotations

from api.discovery.models import DiscoveryItem
from api.discovery.trend_analysis import TrendAnalyzer


def _item(title: str = "", abstract: str = "") -> DiscoveryItem:
    return DiscoveryItem(
        id="t1", title=title, abstract=abstract,
        journal="Journal", authors=["Author"],
    )


class TestTrendAnalyzer:
    def test_detects_new_procedure(self):
        item = _item(title="Novel endoscopic technique for sinus surgery")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert len(result["new_procedures"]) >= 1

    def test_detects_new_device(self):
        item = _item(title="Novel implantable device for hearing restoration")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert len(result["new_devices"]) >= 1

    def test_detects_new_drug(self):
        item = _item(title="Novel therapeutic agent for tinnitus treatment")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert len(result["new_drugs"]) >= 1

    def test_detects_new_technique(self):
        item = _item(abstract="We used 3D-printed patient-specific implants")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert len(result["new_techniques"]) >= 1

    def test_detects_new_disease(self):
        item = _item(abstract="Long COVID otologic manifestations")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert len(result["new_diseases"]) >= 1

    def test_returns_empty_for_plain_text(self):
        item = _item(title="Routine follow-up study")
        analyzer = TrendAnalyzer()
        result = analyzer.analyze([item])
        assert all(len(v) == 0 for v in result.values())
