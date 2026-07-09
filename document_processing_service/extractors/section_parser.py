"""Section structure parser.

Heuristic: scans text for lines that look like numbered/introductory headings
(e.g., "1. Introduction", "ABSTRACT", "Methods") and splits content into sections.

This is a lightweight alternative to GROBID for when it is unavailable.
"""

from __future__ import annotations

import re
from typing import Any

from document_processing_service._async_utils import to_thread
from document_processing_service.extractors.base import BaseExtractor
from document_processing_service.models import ExtractedSection

_SECTION_HEADING_RE = re.compile(
    r"^(?P<num>(?:\d+\.?)+)?\s*(?P<title>[A-Z][A-Z\s\-/]+)$",
    re.IGNORECASE,
)
_KNOWN_SECTIONS: set[str] = {
    "abstract", "introduction", "background",
    "methods", "methodology", "materials and methods",
    "results", "discussion", "conclusion", "conclusions",
    "references", "acknowledgments", "acknowledgements",
    "supplementary", "appendix", "conflict of interest",
    "data availability", "funding", "author contributions",
}
# Sub-heading patterns (numbered 2.1, 2.1.1, etc.)
_SUB_HEADING_RE = re.compile(r"^\s*(\d+\.\d+(?:\.\d+)*)\s+(.+)$")


class SectionExtractor(BaseExtractor):
    name = "sections"

    def __init__(self, min_length: int = 20):
        self._min_length = min_length

    async def extract(self, text: str, **kwargs: Any) -> list[ExtractedSection]:  # type: ignore[override]
        sections = await to_thread(self._split_into_sections, text)
        result = []
        for heading, content, level in sections:
            if len(content.strip()) < self._min_length:
                continue
            result.append(ExtractedSection(
                heading=heading,
                content=content.strip(),
                level=level,
            ))
        if not result:
            # Fallback: entire text as single section
            result.append(ExtractedSection(
                heading="Body",
                content=text.strip(),
                level=1,
            ))
        return result

    @classmethod
    def _split_into_sections(cls, text: str) -> list[tuple[str, str, int]]:
        lines = text.split("\n")
        sections: list[tuple[str, str, int]] = []
        current_heading = "Abstract"  # default start
        current_level = 1
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            m = cls._classify_heading(stripped)
            if m:
                # Flush previous section
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines), current_level))
                    current_lines = []
                current_heading = m["title"]
                current_level = m["level"]
            else:
                current_lines.append(line)

        # Flush last section
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines), current_level))

        return sections

    @classmethod
    def _classify_heading(cls, line: str) -> dict | None:
        if not line:
            return None
        # Sub-heading numbered
        m = _SUB_HEADING_RE.match(line)
        if m:
            return {"title": m.group(2).strip(), "level": 2}
        # Known section title
        if line.lower().strip() in _KNOWN_SECTIONS:
            return {"title": line.strip(), "level": 1}
        # Short all-caps or title-case line that ends without punctuation
        words = line.split()
        if 1 <= len(words) <= 8 and not line.rstrip().endswith((".", ":", ";")):
            if line.isupper() or (line[0].isupper() and not line.endswith((".", "?", "!"))):
                return {"title": line.strip(), "level": 1}
        return None