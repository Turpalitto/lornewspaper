"""Tests for author graph."""

from __future__ import annotations

from api.discovery.author_graph import AuthorGraph
from api.discovery.models import DiscoveryItem


def _item(title: str = "", authors: list[str] | None = None) -> DiscoveryItem:
    return DiscoveryItem(
        id="t1", title=title, authors=authors or ["Author A"],
        journal="Journal", abstract="Abstract.",
    )


class TestAuthorGraph:
    def test_build_returns_authors(self):
        g = AuthorGraph()
        items = [_item(authors=["Alice"]), _item(authors=["Bob"])]
        authors = g.build(items)
        assert len(authors) >= 2

    def test_counts_papers_per_author(self):
        g = AuthorGraph()
        items = [_item(authors=["Alice"]), _item(authors=["Alice"]), _item(authors=["Bob"])]
        authors = g.build(items)
        alice = next(a for a in authors if a.name == "Alice")
        assert alice.paper_count == 2

    def test_tracks_recent_papers(self):
        g = AuthorGraph()
        items = [_item(title="Paper A", authors=["Alice"])]
        authors = g.build(items)
        alice = next(a for a in authors if a.name == "Alice")
        assert "Paper A" in alice.recent_papers

    def test_empty_items(self):
        g = AuthorGraph()
        assert g.build([]) == []

    def test_get_top_institutions(self):
        g = AuthorGraph()
        items = [_item(authors=["Alice"])]
        g.build(items)
        inst = g.get_top_institutions()
        assert isinstance(inst, list)
