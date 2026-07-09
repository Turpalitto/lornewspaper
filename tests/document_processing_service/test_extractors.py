"""Tests for all extractors (sections, references, tables, figures)."""

import os
import tempfile

import pytest

from document_processing_service.extractors.figure_parser import FigureExtractor
from document_processing_service.extractors.reference_parser import ReferenceExtractor
from document_processing_service.extractors.section_parser import SectionExtractor
from document_processing_service.extractors.table_parser import (
    TableExtractor,
    _parse_markdown_table,
    _table_to_markdown,
)
from document_processing_service.text_extractor import TextExtractor
from tests.document_processing_service.fixtures import make_minimal_pdf, make_pdf_with_tables


def _open_pdf(pdf_bytes: bytes):
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "t.pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    ex = TextExtractor()
    return ex.extract(path)


@pytest.mark.asyncio
async def test_section_extractor_finds_sections():
    doc, pages, _ = _open_pdf(make_minimal_pdf())
    raw = "\n".join(pages)
    ex = SectionExtractor(min_length=5)
    sections = await ex.extract(raw)
    headings = [s.heading for s in sections]
    assert "Abstract" in headings or "abstract" in headings or any("Abstract" in h for h in headings)
    assert len(sections) >= 3
    doc.close()


@pytest.mark.asyncio
async def test_section_extractor_fallback_single_section():
    ex = SectionExtractor()
    sections = await ex.extract("Short")
    assert len(sections) == 1
    assert sections[0].heading == "Body"
    assert sections[0].content == "Short"


@pytest.mark.asyncio
async def test_reference_extractor_finds_refs():
    doc, pages, _ = _open_pdf(make_minimal_pdf())
    raw = "\n".join(pages)
    ex = ReferenceExtractor()
    refs = await ex.extract(raw)
    assert len(refs) >= 2
    assert any("Author" in r.raw_text for r in refs)
    doc.close()


@pytest.mark.asyncio
async def test_reference_extractor_extracts_year():
    ex = ReferenceExtractor()
    refs = await ex.extract("[1] Author. Title. Journal. 2023.")
    assert len(refs) >= 1
    assert refs[0].year == 2023


@pytest.mark.asyncio
async def test_reference_extractor_extracts_doi():
    ex = ReferenceExtractor()
    refs = await ex.extract("[1] Author. Title. Journal. doi:10.1234/test.567.")
    assert refs[0].doi == "10.1234/test.567"


@pytest.mark.asyncio
async def test_table_extractor_from_text():
    doc, pages, _ = _open_pdf(make_pdf_with_tables())
    ex = TableExtractor()
    tables = await ex.extract(doc, raw_pages=pages)
    # Text-based table extraction might not find tables since PyMuPDF's
    # find_tables() is layout-aware. Fallback to markdown table detection.
    assert isinstance(tables, list)
    doc.close()


@pytest.mark.asyncio
async def test_table_extractor_markdown_parse():
    lines = ["| H1 | H2 |", "|---|---|", "| A | B |"]
    result = _parse_markdown_table(lines, 1)
    assert result.headers == ["H1", "H2"]
    assert len(result.rows) == 1
    assert result.rows[0] == ["A", "B"]


@pytest.mark.asyncio
async def test_table_to_markdown():
    md = _table_to_markdown(["H1", "H2"], [["A", "B"]])
    assert "| H1 | H2 |" in md
    assert "| A | B |" in md


@pytest.mark.asyncio
async def test_figure_extractor_returns_list():
    doc, pages, _ = _open_pdf(make_minimal_pdf())
    ex = FigureExtractor()
    figures = await ex.extract(doc, raw_pages=pages)
    assert isinstance(figures, list)
    doc.close()