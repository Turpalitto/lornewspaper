"""Tests for deduplication and metadata merge."""

from datetime import datetime, timezone

from search_service.dedupe import deduplicate, titles_similar
from search_service.models import Article


def _article(**kw) -> Article:
    base = dict(source="pubmed", provenance=["pubmed"])
    base.update(kw)
    return Article(**base)


def test_dedupe_by_doi():
    a = _article(doi="10.1/x", title="A")
    b = _article(doi="10.1/x", title="Different Title", source="europepmc", provenance=["europepmc"])
    out = deduplicate([a, b])
    assert len(out) == 1


def test_dedupe_by_pmid():
    a = _article(pmid="111", title="A")
    b = _article(pmid="111", title="B")
    assert len(deduplicate([a, b])) == 1


def test_dedupe_by_pmcid():
    a = _article(pmcid="PMC1", title="A")
    b = _article(pmcid="PMC1", title="B")
    assert len(deduplicate([a, b])) == 1


def test_dedupe_by_title_similarity():
    a = _article(title="The rapid spread of viruses")
    b = _article(title="The rapid spread of viruses.", source="openalex", provenance=["openalex"])
    assert len(deduplicate([a, b])) == 1


def test_no_dedupe_for_different_works():
    a = _article(doi="10.1/a", title="Alpha")
    b = _article(doi="10.1/b", title="Beta")
    assert len(deduplicate([a, b])) == 2


def test_merge_unions_lists_and_provenance():
    a = _article(
        doi="10.1/x",
        title="T",
        authors=["Smith"],
        keywords=["k1"],
        mesh_terms=["m1"],
        abstract=None,
    )
    b = _article(
        doi="10.1/x",
        title="T",
        source="europepmc",
        provenance=["europepmc"],
        authors=["Doe"],
        keywords=["k2"],
        mesh_terms=["m2"],
        abstract="An abstract",
    )
    merged = deduplicate([a, b])[0]
    assert set(merged.authors) == {"Smith", "Doe"}
    assert set(merged.keywords) == {"k1", "k2"}
    assert set(merged.mesh_terms) == {"m1", "m2"}
    assert merged.provenance == ["pubmed", "europepmc"]
    # scalar: target missing abstract filled from source
    assert merged.abstract == "An abstract"


def test_merge_prefers_latest_retrieved_at():
    older = datetime(2020, 1, 1, tzinfo=timezone.utc)
    newer = datetime(2024, 1, 1, tzinfo=timezone.utc)
    a = _article(doi="10.1/x", retrieved_at=older)
    b = _article(doi="10.1/x", retrieved_at=newer, source="openalex", provenance=["openalex"])
    merged = deduplicate([a, b])[0]
    assert merged.retrieved_at == newer


def test_titles_similar_threshold():
    assert titles_similar("Machine learning in bioinformatics", "Machine learning in bioinformatics!")
    assert not titles_similar("Alpha study", "Completely different beta examination")
