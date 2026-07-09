"""OCR requirement detector.

Analyzes PDF pages for text density. If a page contains very few text
characters but has images, OCR may be required to extract content.
All fitz calls run in thread pool to avoid blocking the event loop.
"""

from __future__ import annotations

from typing import Any

from document_processing_service._async_utils import to_thread

_OCR_TEXT_THRESHOLD = 50
_OCR_IMAGE_AREA_RATIO = 0.3


class OCRDetector:
    async def detect(self, doc: Any) -> bool:
        return await to_thread(self._detect_sync, doc)

    async def pages_needing_ocr(self, doc: Any) -> list[int]:
        return await to_thread(self._pages_needing_ocr_sync, doc)

    def _detect_sync(self, doc: Any) -> bool:
        try:
            for page in doc:
                text = page.get_text()
                if len(text.strip()) < _OCR_TEXT_THRESHOLD:
                    images = page.get_images(full=True)
                    if images:
                        return True
            return False
        except Exception:
            return False

    def _pages_needing_ocr_sync(self, doc: Any) -> list[int]:
        pages: list[int] = []
        try:
            for i, page in enumerate(doc):
                text = page.get_text()
                if len(text.strip()) < _OCR_TEXT_THRESHOLD:
                    images = page.get_images(full=True)
                    if images:
                        pages.append(i + 1)
        except Exception:
            pass
        return pages
