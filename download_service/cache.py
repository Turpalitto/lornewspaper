"""Cache helpers for downloaded files."""

from __future__ import annotations

import os

from download_service.config import Settings


def cache_path(sha256_hex: str, extension: str, settings: Settings | None = None) -> str:
    """Return the full file path for a cached download.

    Uses a shallow two-level hash prefix tree to avoid all files sitting in
    a single directory.
    """
    base = getattr(settings, "cache_dir", "./download_cache") if settings else "./download_cache"
    prefix1 = sha256_hex[:2]
    prefix2 = sha256_hex[2:4]
    directory = os.path.join(base, prefix1, prefix2)
    os.makedirs(directory, exist_ok=True)
    filename = f"{sha256_hex}.{extension.lstrip('.')}"
    return os.path.join(directory, filename)


def resolve_cache_path(cache_dir: str, article_id: str, download_type: str) -> str:
    """Fallback cache path before sha256 is known (used during download)."""
    directory = os.path.join(cache_dir, "partial")
    os.makedirs(directory, exist_ok=True)
    filename = f"{article_id}.{download_type}.partial"
    return os.path.join(directory, filename)