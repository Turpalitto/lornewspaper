"""DownloadService.

Resolves Article objects to downloadable content (PDF, XML), downloads with
integrity verification, and returns unified ``DownloadResult``.
"""

from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from download_service.service import DownloadService

__all__ = ["DownloadService", "DownloadResult", "DownloadStatus", "ContentInfo"]
__version__ = "0.1.0"
