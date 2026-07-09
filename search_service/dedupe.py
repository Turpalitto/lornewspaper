"""Deduplication and metadata merging.

Two records are considered the same work when they share a DOI, PMID or PMCID,
or — as a fallback — their normalized titles are highly similar. When matched,
records are merged: non-null scalar fields are kept (latest non-null wins),
list fields are unioned, ``provenance`` accumulates contributing providers, and
``retrieved_at`` moves to the latest timestamp.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from search_service.models import Article

_TITLE_RE = re.compile(r"[^a-z0-9 ]+")


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    lowered = title.lower()
    cleaned = _TITLE_RE.sub(" ", lowered)
    return " ".join(cleaned.split())


def titles_similar(a: str | None, b: str | None, threshold: float = 0.85) -> bool:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    sa, sb = set(na.split()), set(nb.split())
    union = sa | sb
    if not union:
        return False
    return len(sa & sb) / len(union) >= threshold


def _same_identity(a: Article, b: Article) -> bool:
    if a.doi and b.doi and a.doi.lower().strip() == b.doi.lower().strip():
        return True
    if a.pmid and b.pmid and a.pmid == b.pmid:
        return True
    if a.pmcid and b.pmcid and a.pmcid.lower().strip() == b.pmcid.lower().strip():
        return True
    return titles_similar(a.title, b.title)


_SCALAR_FIELDS = (
    "title",
    "journal",
    "year",
    "doi",
    "pmid",
    "abstract",
    "url",
    "pdf_url",
    "pmcid",
    "language",
    "publisher",
    "volume",
    "issue",
    "pages",
    "license",
)

_LIST_FIELDS = ("authors", "keywords", "mesh_terms", "publication_type")


def merge_into(target: Article, source: Article) -> Article:
    """Merge ``source`` into ``target`` in place, preserving provenance."""
    for field in _SCALAR_FIELDS:
        tv = getattr(target, field)
        sv = getattr(source, field)
        if tv is None and sv is not None:
            setattr(target, field, sv)

    for field in _LIST_FIELDS:
        merged = list(getattr(target, field))
        for item in getattr(source, field):
            if item not in merged:
                merged.append(item)
        setattr(target, field, merged)

    if source.source and source.source not in target.provenance:
        target.provenance.append(source.source)

    if source.retrieved_at and (
        target.retrieved_at is None or source.retrieved_at > target.retrieved_at
    ):
        target.retrieved_at = source.retrieved_at

    target.id = target.derive_id()
    return target


def deduplicate(articles: Iterable[Article]) -> list[Article]:
    """Group and merge articles that refer to the same work."""
    groups: list[Article] = []
    for article in articles:
        match = None
        for group in groups:
            if _same_identity(group, article):
                match = group
                break
        if match is None:
            article.id = article.derive_id()
            groups.append(article)
        else:
            merge_into(match, article)
    return groups
