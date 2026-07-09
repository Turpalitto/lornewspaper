"""Tests for quality filter."""

from __future__ import annotations

from datetime import date

from api.discovery.models import DiscoveryItem
from api.discovery.quality_filter import QualityFilter


def _item(title: str = "Test", doi: str = "10.1234/test") -> DiscoveryItem:
    return DiscoveryItem(
        id="t1", title=title, doi=doi,
        abstract="This is a full research paper abstract with sufficient content to pass quality filters.",
    )


class TestQualityFilter:
    def test_removes_duplicate_dois(self):
        f = QualityFilter()
        a = _item(doi="10.1/dup")
        b = _item(doi="10.1/dup")
        result = f.filter([a, b])
        assert len(result) == 1

    def test_removes_duplicate_titles(self):
        f = QualityFilter()
        a = _item(title="Same Title")
        b = _item(title="Same Title", doi="10.2/diff")
        result = f.filter([a, b])
        assert len(result) == 1

    def test_passes_unique_items(self):
        f = QualityFilter()
        a = _item(title="Paper A", doi="10.1/a")
        b = _item(title="Paper B", doi="10.1/b")
        result = f.filter([a, b])
        assert len(result) == 2

    def test_removes_empty_abstract(self):
        f = QualityFilter()
        item = _item(title="No abstract", doi="10.1/no")
        item.abstract = ""
        result = f.filter([item])
        assert len(result) == 0

    def test_removes_short_abstract(self):
        f = QualityFilter()
        item = _item(title="Short", doi="10.1/short")
        item.abstract = "Short"
        result = f.filter([item])
        assert len(result) == 0

    def test_removes_conference_abstract(self):
        f = QualityFilter()
        item = _item(title="Conference abstract #1234")
        item.abstract = "Presented at the annual meeting"
        result = f.filter([item])
        assert len(result) == 0

    def test_empty_input(self):
        f = QualityFilter()
        assert f.filter([]) == []

    def test_handles_large_batch(self):
        f = QualityFilter()
        items = [_item(title=f"Paper {i}", doi=f"10.1/{i}") for i in range(100)]
        result = f.filter(items)
        assert len(result) == 100
