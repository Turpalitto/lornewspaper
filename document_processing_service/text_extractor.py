"""Text extraction layer.

Opens PDF with PyMuPDF (fitz), extracts per-page text, detects OCR need.
All fitz calls run in thread pool to avoid blocking the event loop.
"""

from __future__ import annotations

from typing import Any

import fitz

from document_processing_service._async_utils import to_thread
from document_processing_service.exceptions import PDFEncryptedError, PDFOpenError


class TextExtractor:
    async def extract(self, file_path: str, max_pages: int = 0) -> tuple[Any, list[str], int]:
        return await to_thread(self._extract_sync, file_path, max_pages)

    async def extract_pages(self, file_path: str, max_pages: int = 0) -> tuple[Any, list[str], int]:
        return await self.extract(file_path, max_pages)

    def _extract_sync(self, file_path: str, max_pages: int = 0) -> tuple[Any, list[str], int]:
        try:
            doc = fitz.open(file_path)
        except Exception as exc:
            raise PDFOpenError(f"Cannot open {file_path}: {exc}") from exc

        if doc.is_encrypted:
            doc.close()
            raise PDFEncryptedError(f"{file_path} is encrypted")

        page_texts: list[str] = []
        total = len(doc)
        pages_to_read = min(total, max_pages) if max_pages > 0 else total

        for i in range(pages_to_read):
            page = doc.load_page(i)
            text = page.get_text()
            page_texts.append(text)

        return doc, page_texts, total
