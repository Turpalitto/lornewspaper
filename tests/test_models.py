"""Tests for the unified Article model."""

import pytest

from search_service.models import Article


def test_article_defaults():
    a = Article(source="pubmed", title="Hello")
    assert a.authors == []
    assert a.keywords == []
    assert a.mesh_terms == []
    assert a.provenance == []
    assert a.source == "pubmed"
    assert a.retrieved_at is not None


def test_derive_id_prefers_doi():
    a = Article(source="x", doi="10.1/ABC", pmid="1", pmcid="PMC2", title="T")
    assert a.derive_id() == "10.1/abc"


def test_derive_id_falls_back_to_pmid():
    a = Article(source="x", pmid="12345", title="T")
    assert a.derive_id() == "pmid:12345"


def test_derive_id_falls_back_to_title():
    a = Article(source="x", title="  Some Title  ")
    assert a.derive_id() == "title:some title"
