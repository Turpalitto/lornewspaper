# DocumentProcessingService — Anchor Summary

## Purpose

Convert `DownloadResult` → `ProcessedDocument`. Extracts structured content from scientific PDFs: text, sections, references, tables, figures, metadata. Produces Markdown and extraction statistics.

---

## Public API

```python
class DocumentProcessingService:
    async def process(self, download_result: DownloadResult) -> ProcessedDocument

class ProcessedDocument(BaseModel):
    article_id: str
    status: ProcessingStatus         # COMPLETED | PARTIAL | FAILED
    markdown: str                    # generated Markdown
    metadata: DocumentMetadata       # title, abstract, authors, etc.
    sections: list[ExtractedSection] # heading + content + level + page mapping
    references: list[ExtractedReference]
    tables: list[ExtractedTable]
    figures: list[ExtractedFigure]
    page_mappings: list[PageMapping]
    stats: ExtractionStats           # pages, chars, counts, OCR flags, timing, errors
    source_file: str
    raw_text: str
    processing_started_at: datetime | None
    processing_completed_at: datetime | None

class ExtractedSection:
    heading: str
    content: str
    level: int          # 1 = major section, 2 = subsection
    page_mapping: list[PageMapping]

class ExtractedReference:
    raw_text: str, index: str
    doi: str | None, title: str | None
    authors: list[str], year: int | None, source: str | None

class ExtractedTable:
    caption: str, headers: list[str], rows: list[list[str]]
    page_number: int, markdown: str

class ExtractedFigure:
    caption: str, alt_text: str
    page_number: int, image_index: int

class ExtractionStats:
    total_pages, total_characters
    sections_found, references_found, tables_found, figures_found
    ocr_required: bool, ocr_performed: bool
    extraction_time_ms: float
    errors: list[str]
```

Construction:
```python
svc = DocumentProcessingService()
result = await svc.process(download_result)
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **Strategy pattern for extractors** | New extractor = one file implementing `BaseExtractor.extract()`. Plug-and-play. |
| **Per-extractor failure isolation** | Each wrapped in try/except. Failure → PARTIAL status + error logged. |
| **Heuristic section parsing** | No GROBID dependency. Regex detects numbered headings + known titles. |
| **PyMuPDF only** | Only available PDF lib. Sufficient for text + tables + images. |
| **ProcessedDocument always returned** | Never raises. Consumer inspects `.status` + `.stats.errors`. |

---

## Extension Points

1. **New extractor**: implement `BaseExtractor`, inject via constructor.
2. **GROBID integration**: replace heuristic section/reference parsers with GROBID client (same interface).
3. **OCR fallback**: set `Settings.pdf.ocr_fallback = True`, inject OCR-enabled text extractor.
4. **Custom metadata extraction**: override `_extract_metadata()`.

---

## Known Limitations

- **No GROBID integration.** Section and reference parsing is heuristic. May not handle all journal formats. GROBID integration recommended for production.
- **No encryption library.** Encrypted PDFs raise `PDFEncryptedError` — cannot be tested without crypto library.
- **No OCR.** OCR detection flags pages needing OCR but cannot perform it. Requires Tesseract or similar.
- **No Unpaywall figure download.** Figures are detected by page coordinates but not extracted as files.
- **No large-PDF pagination.** Entire PDF read into memory. 500+ page documents may cause memory pressure.

---

## Roadmap

| Item | Priority | Effort | Status |
|---|---|---|---|
| Heuristic section parser | High | 2h | ✅ Done |
| Reference extraction | High | 2h | ✅ Done |
| Table extraction | High | 2h | ✅ Done |
| Figure detection | Medium | 2h | ✅ Done |
| Markdown generation | Medium | 1h | ✅ Done |
| OCR detection | Medium | 1h | ✅ Done |
| GROBID integration | Low | 8h | Pending |
| Encrypted PDF handling | Low | 2h | Pending |
| Large PDF streaming | Low | 4h | Pending |
| Figure file extraction | Low | 3h | Pending |