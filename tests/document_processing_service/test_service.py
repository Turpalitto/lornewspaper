"""Tests for DocumentProcessingService orchestrator and Markdown generator."""

import os
import tempfile

import pytest

from document_processing_service.markdown_generator import generate_markdown
from document_processing_service.models import (
    ExtractedReference,
    ExtractedSection,
    ExtractedTable,
    ProcessedDocument,
    ProcessingStatus,
)
from document_processing_service.service import DocumentProcessingService, _extract_metadata
from download_service.models import DownloadResult, DownloadStatus
from tests.document_processing_service.fixtures import make_minimal_pdf


def _write(pdf_bytes: bytes) -> str:
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test.pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


@pytest.mark.asyncio
async def test_process_successful():
    path = _write(make_minimal_pdf())
    dr = DownloadResult(
        article_id="test123",
        source="test",
        download_type="pdf",
        status=DownloadStatus.COMPLETED,
        file_path=path,
    )
    svc = DocumentProcessingService()
    result = await svc.process(dr)
    assert result.status == ProcessingStatus.COMPLETED
    assert result.article_id == "test123"
    assert result.source_file == path
    assert len(result.sections) >= 1
    assert result.stats.total_pages >= 1
    assert result.stats.total_characters > 0
    assert result.markdown != ""


@pytest.mark.asyncio
async def test_process_bad_path():
    dr = DownloadResult(
        article_id="bad",
        source="test",
        download_type="pdf",
        status=DownloadStatus.COMPLETED,
        file_path="/nonexistent/file.pdf",
    )
    svc = DocumentProcessingService()
    result = await svc.process(dr)
    assert result.status == ProcessingStatus.FAILED


@pytest.mark.asyncio
async def test_markdown_generator_with_sections():
    doc = ProcessedDocument(
        article_id="x",
        status=ProcessingStatus.COMPLETED,
        sections=[
            ExtractedSection(heading="Intro", content="Some intro text.", level=1),
            ExtractedSection(heading="Methods", content="Methods text.", level=2),
        ],
    )
    md = generate_markdown(doc)
    assert "## Intro" in md
    assert "### Methods" in md
    assert "Some intro text." in md


@pytest.mark.asyncio
async def test_markdown_generator_with_references():
    doc = ProcessedDocument(
        article_id="x",
        status=ProcessingStatus.COMPLETED,
        references=[
            ExtractedReference(raw_text="Author. Paper. 2023.", index="1"),
            ExtractedReference(raw_text="Author2. Paper2. 2024.", index="2"),
        ],
    )
    md = generate_markdown(doc)
    assert "[1]" in md
    assert "[2]" in md
    assert "Author. Paper. 2023." in md
    assert "## References" in md


@pytest.mark.asyncio
async def test_markdown_generator_with_tables():
    doc = ProcessedDocument(
        article_id="x",
        status=ProcessingStatus.COMPLETED,
        tables=[
            ExtractedTable(
                headers=["Name", "Value"],
                rows=[["A", "1"], ["B", "2"]],
                markdown="| Name | Value |\n| --- | --- |\n| A | 1 |\n| B | 2 |",
            ),
        ],
    )
    md = generate_markdown(doc)
    assert "## Tables" in md
    assert "Name" in md
    assert "Value" in md


@pytest.mark.asyncio
async def test_metadata_extraction():
    text = (
        "My Title Line\n"
        "Some author line\n"
        "\n"
        "Abstract\n"
        "This is the abstract content\n"
        "that spans multiple lines.\n"
        "\n"
        "Introduction\n"
        "Body text here.\n"
    )
    meta = _extract_metadata(text)
    assert "My Title Line" in meta.title
    assert "abstract" in meta.abstract.lower()
    assert "content" in meta.abstract


@pytest.mark.asyncio
async def test_empty_metadata():
    meta = _extract_metadata("")
    assert meta.title == ""
    assert meta.abstract == ""


@pytest.mark.asyncio
async def test_process_sets_timing():
    path = _write(make_minimal_pdf())
    dr = DownloadResult(
        article_id="timing_test",
        source="test",
        download_type="pdf",
        status=DownloadStatus.COMPLETED,
        file_path=path,
    )
    svc = DocumentProcessingService()
    result = await svc.process(dr)
    assert result.processing_started_at is not None
    assert result.processing_completed_at is not None
    assert result.processing_completed_at > result.processing_started_at
    assert result.stats.extraction_time_ms > 0