"""PDF downloader — thin subclass setting content-type expectations."""

from __future__ import annotations

from download_service.downloaders.base import _PDF_MIMES, BaseDownloader


class PdfDownloader(BaseDownloader):
    download_type = "pdf"
    expected_content_type = "application/pdf"
    valid_mime_types = _PDF_MIMES
