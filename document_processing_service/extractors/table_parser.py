"""Table extractor.

Uses PyMuPDF (fitz) table detection to locate and extract tabular content.
Falls back to heuristic text-based extraction when table detection is unavailable.
"""

from __future__ import annotations

import re
from typing import Any

from document_processing_service._async_utils import to_thread
from document_processing_service.extractors.base import BaseExtractor
from document_processing_service.models import ExtractedTable

_MULTI_SPACE = re.compile(r" {2,}")
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")


class TableExtractor(BaseExtractor):
    name = "tables"

    async def extract(  # noqa: PLR0913
        self,
        doc: Any,
        *,
        raw_pages: list[str] | None = None,
        **kwargs: Any,
    ) -> list[ExtractedTable]:
        tables = await to_thread(self._extract_via_fitz, doc)
        if not tables:
            tables = await to_thread(self._extract_via_text, raw_pages or [])
        return tables

    @staticmethod
    def _extract_via_fitz(doc) -> list[ExtractedTable]:
        result: list[ExtractedTable] = []
        try:
            for page_num, page in enumerate(doc):
                tabs = page.find_tables()
                for tab in tabs:
                    df = tab.to_pandas()
                    headers = list(df.columns) if df.columns is not None else []
                    rows = [[str(c) for c in row] for row in df.values]
                    md = _table_to_markdown(headers, rows)
                    result.append(ExtractedTable(
                        headers=headers,
                        rows=rows,
                        page_number=page_num + 1,
                        markdown=md,
                    ))
        except Exception:
            pass
        return result

    @staticmethod
    def _extract_via_text(pages: list[str]) -> list[ExtractedTable]:
        result: list[ExtractedTable] = []
        for page_num, page_text in enumerate(pages, 1):
            lines = page_text.split("\n")
            table_lines: list[str] = []
            in_table = False
            for line in lines:
                if _TABLE_ROW_RE.match(line.strip()):
                    in_table = True
                    table_lines.append(line)
                elif in_table and line.strip() == "":
                    result.append(_parse_markdown_table(table_lines, page_num))
                    table_lines = []
                    in_table = False
            if table_lines:
                result.append(_parse_markdown_table(table_lines, page_num))
        return result


def _table_to_markdown(headers: list[str], rows: list[list[str]]) -> str:
    if not headers and not rows:
        return ""
    lines: list[str] = []
    if headers:
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _parse_markdown_table(lines: list[str], page_num: int) -> ExtractedTable:
    headers: list[str] = []
    rows: list[list[str]] = []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if i == 0:
            headers = cells
        elif not all(c == "---" or c == "---" for c in cells):
            rows.append(cells)
    md = _table_to_markdown(headers, rows)
    return ExtractedTable(headers=headers, rows=rows, page_number=page_num, markdown=md)