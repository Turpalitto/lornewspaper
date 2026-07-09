"""XML downloader — thin subclass setting content-type expectations."""

from __future__ import annotations

from download_service.downloaders.base import _XML_MIMES, BaseDownloader


class XmlDownloader(BaseDownloader):
    download_type = "xml"
    expected_content_type = "application/xml"
    valid_mime_types = _XML_MIMES
