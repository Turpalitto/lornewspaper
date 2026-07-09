"""DocumentProcessingService.

Extracts structured content from scientific PDFs: text, sections, references,
tables, figures. Produces Markdown and extraction statistics.
"""

from document_processing_service.models import (
    DocumentMetadata,
    ExtractedFigure,
    ExtractedReference,
    ExtractedSection,
    ExtractedTable,
    ExtractionStats,
    PageMapping,
    ProcessedDocument,
)
from document_processing_service.service import DocumentProcessingService

__all__ = [
    "DocumentProcessingService",
    "ProcessedDocument",
    "DocumentMetadata",
    "ExtractionStats",
    "ExtractedSection",
    "ExtractedReference",
    "ExtractedTable",
    "ExtractedFigure",
    "PageMapping",
]
__version__ = "0.1.0"