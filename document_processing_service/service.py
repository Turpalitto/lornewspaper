"""DocumentProcessingService orchestrator.

Pipeline:
  1. Open PDF -> TextExtractor
  2. OCR detection -> OCRDetector
  3. Section parsing -> SectionExtractor
  4. Reference extraction -> ReferenceExtractor
  5. Table extraction -> TableExtractor
  6. Figure extraction -> FigureExtractor
  7. Markdown generation -> markdown_generator
  8. Assemble ProcessedDocument

All CPU-bound operations run in thread pool via to_thread().
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import structlog

from document_processing_service._async_utils import to_thread
from document_processing_service.config import Settings, default_settings
from document_processing_service.extractors.figure_parser import FigureExtractor
from document_processing_service.extractors.reference_parser import ReferenceExtractor
from document_processing_service.extractors.section_parser import SectionExtractor
from document_processing_service.extractors.table_parser import TableExtractor
from document_processing_service.markdown_generator import generate_markdown
from document_processing_service.models import (
    DocumentMetadata,
    ExtractionStats,
    ProcessedDocument,
    ProcessingStatus,
)
from document_processing_service.ocr_detector import OCRDetector
from document_processing_service.text_extractor import TextExtractor
from download_service.models import DownloadResult

_LOG = structlog.get_logger("document_processing_service")


class DocumentProcessingService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        text_extractor: TextExtractor | None = None,
        ocr_detector: OCRDetector | None = None,
        section_extractor: "SectionExtractor | None" = None,
        reference_extractor: "ReferenceExtractor | None" = None,
        table_extractor: "TableExtractor | None" = None,
        figure_extractor: "FigureExtractor | None" = None,
    ) -> None:
        self._settings = settings or default_settings()
        self._text_extractor = text_extractor or TextExtractor()
        self._ocr_detector = ocr_detector or OCRDetector()
        self._section_extractor = section_extractor or SectionExtractor(
            min_length=self._settings.pdf.min_section_length,
        )
        self._reference_extractor = reference_extractor or ReferenceExtractor()
        self._table_extractor = table_extractor or TableExtractor()
        self._figure_extractor = figure_extractor or FigureExtractor()

    async def process(
        self,
        download_result: DownloadResult,
    ) -> ProcessedDocument:
        start = time.perf_counter()
        article_id = download_result.article_id
        file_path = download_result.file_path or ""

        result = ProcessedDocument(
            article_id=article_id,
            status=ProcessingStatus.FAILED,
            source_file=file_path,
            processing_started_at=_now(),
        )

        errors: list[str] = []
        doc = None
        page_texts: list[str] = []
        total_pages = 0
        raw_text = ""
        ocr_needed = False

        try:
            # 1. Open & extract text (blocking: fitz)
            doc, page_texts, total_pages = await self._text_extractor.extract(
                file_path,
                max_pages=self._settings.pdf.max_pages,
            )
            raw_text = "\n".join(page_texts)
            result.raw_text = raw_text

            # 2. OCR detection (blocking: fitz)
            ocr_needed = await self._ocr_detector.detect(doc)
            if ocr_needed and self._settings.pdf.ocr_fallback:
                _LOG.warning("ocr_required_but_not_available", article_id=article_id)

            # 3. Sections
            try:
                sections = await self._section_extractor.extract(raw_text)
                result.sections = sections
            except Exception as exc:
                errors.append(f"sections: {exc}")
                _log_warn("section_extraction_failed", article_id, exc)

            # 4. References
            try:
                if self._settings.pdf.extract_references:
                    refs = await self._reference_extractor.extract(raw_text)
                    result.references = refs
            except Exception as exc:
                errors.append(f"references: {exc}")
                _log_warn("reference_extraction_failed", article_id, exc)

            # 5. Tables (blocking: fitz + pandas)
            try:
                if self._settings.pdf.extract_tables:
                    tables = await self._table_extractor.extract(doc, raw_pages=page_texts)
                    result.tables = tables
            except Exception as exc:
                errors.append(f"tables: {exc}")
                _log_warn("table_extraction_failed", article_id, exc)

            # 6. Figures (blocking: fitz)
            try:
                if self._settings.pdf.extract_figures:
                    figures = await self._figure_extractor.extract(doc, raw_pages=page_texts)
                    result.figures = figures
            except Exception as exc:
                errors.append(f"figures: {exc}")
                _log_warn("figure_extraction_failed", article_id, exc)

            # 7. Metadata (CPU-bound text parsing)
            result.metadata = await to_thread(_extract_metadata, raw_text)

            # 8. Markdown (CPU-bound string formatting)
            result.markdown = await to_thread(generate_markdown, result)

            result.status = ProcessingStatus.PARTIAL if errors else ProcessingStatus.COMPLETED

        except Exception as exc:
            errors.append(str(exc))
            result.status = ProcessingStatus.FAILED
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

        elapsed = time.perf_counter() - start
        result.stats = ExtractionStats(
            total_pages=total_pages,
            total_characters=len(raw_text),
            sections_found=len(result.sections),
            references_found=len(result.references),
            tables_found=len(result.tables),
            figures_found=len(result.figures),
            ocr_required=ocr_needed,
            ocr_performed=False,
            extraction_time_ms=round(elapsed * 1000, 1),
            errors=errors,
        )

        result.processing_completed_at = _now()
        return result


def _now() -> datetime:
    return datetime.now(UTC)


def _extract_metadata(text: str) -> DocumentMetadata:
    lines = text.strip().split("\n")
    title = ""
    abstract = ""
    abstract_started = False

    for _i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if not title:
            title = stripped[:200]
        if stripped.lower().startswith("abstract"):
            abstract_started = True
            continue
        if abstract_started:
            if stripped.lower().startswith(("introduction", "background", "1.")):
                break
            abstract += " " + stripped
            if len(abstract) > 1500:
                abstract = abstract[:1500]
                break

    return DocumentMetadata(
        title=title,
        abstract=abstract.strip(),
    )


def _log_warn(msg: str, article_id: str, exc: Exception) -> None:
    _LOG.warning(msg, article_id=article_id, error=str(exc))
