"""DocumentProcessingService exception hierarchy."""

from __future__ import annotations


class DocumentProcessingError(Exception):
    """Base for all DocumentProcessingService errors."""


class PDFOpenError(DocumentProcessingError, FileNotFoundError):
    """PDF file could not be opened."""


class PDFEncryptedError(DocumentProcessingError, PermissionError):
    """PDF is encrypted and cannot be processed."""


class ExtractionError(DocumentProcessingError, RuntimeError):
    """Content extraction failed."""