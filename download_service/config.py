"""Configuration for DownloadService.

Most settings have sensible defaults but are overridable per deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DownloaderConfig:
    """Per-downloader tunables."""

    content_type: str = "application/pdf"
    rate: float = 3.0
    burst: int = 5
    timeout: float = 30.0
    max_size_bytes: int = 50 * 1024 * 1024  # 50 MB cap
    retry_attempts: int = 4


@dataclass(slots=True)
class Settings:
    """Runtime configuration for DownloadService."""

    user_agent: str = "DownloadService/0.1 (+https://example.org)"
    cache_dir: str = "./download_cache"
    max_concurrent: int = 3
    log_level: str = "INFO"
    unpaywall_email: str = ""
    downloaders: dict[str, DownloaderConfig] = field(default_factory=lambda: {
        "pdf": DownloaderConfig(content_type="application/pdf"),
        "xml": DownloaderConfig(content_type="application/xml"),
    })
    extra: dict[str, Any] = field(default_factory=dict)


def default_settings() -> Settings:
    return Settings()