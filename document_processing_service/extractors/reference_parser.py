"""Reference parser.

Extracts references from the references/bibliography section of scientific papers.
Handles common numbering schemes: [1], (1), 1., etc.
"""

from __future__ import annotations

import re
from typing import Any

from document_processing_service.extractors.base import BaseExtractor
from document_processing_service.models import ExtractedReference

_REF_ITEM_RE = re.compile(
    r"(?:^|\n)\s*(?:(?:\[(\d+)\]|\((\d+)\)|(\d+)\.)\s*)?(.+?)(?=\n\s*(?:\[\d+\]|\(\d+\)|\d+\.)\s|\Z)",
    re.DOTALL,
)
_DOI_IN_TEXT_RE = re.compile(r"(?:doi|DOI)\s*[:.]?\s*(10\.\d{4,}/[^\s,;)]+)")
_YEAR_RE = re.compile(r"\(?(\d{4})\)?")
_TITLE_QUOTE_RE = re.compile(r"[""\u201c].+?[""\u201d]")


class ReferenceExtractor(BaseExtractor):
    name = "references"

    def __init__(self, max_references: int = 500):
        self._max = max_references

    async def extract(  # type: ignore[override]  # noqa: PLR0913
        self,
        text: str,
        *,
        references_section: str = "",
        **kwargs: Any,
    ) -> list[ExtractedReference]:
        source = references_section if references_section else text
        raw_items = self._split_references(source)
        result: list[ExtractedReference] = []
        for idx, ref_text in raw_items:
            ref = ExtractedReference(raw_text=ref_text.strip(), index=idx)
            # Extract DOI if present
            doi_m = _DOI_IN_TEXT_RE.search(ref_text)
            if doi_m:
                ref.doi = doi_m.group(1).strip().rstrip(".")
            # Extract year
            year_m = _YEAR_RE.search(ref_text)
            if year_m:
                ref.year = int(year_m.group(1))
            # Extract title (text in quotes if present)
            title_m = _TITLE_QUOTE_RE.search(ref_text)
            if title_m:
                ref.title = title_m.group(0).strip("\u201c\u201d\"")
            result.append(ref)
            if len(result) >= self._max:
                break
        return result

    @staticmethod
    def _split_references(text: str) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        matches = list(_REF_ITEM_RE.finditer(text))
        if not matches:
            # No structured references; return whole text as single reference
            return [("1", text.strip())]
        for m in matches:
            idx = m.group(1) or m.group(2) or m.group(3) or ""
            ref_text = m.group(4).strip()
            if ref_text:
                items.append((idx, ref_text))
        return items