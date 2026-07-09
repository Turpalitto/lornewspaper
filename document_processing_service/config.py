"""Configuration for DocumentProcessingService."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProcessingConfig:
    max_pages: int = 0  # 0 = no limit
    min_section_length: int = 20
    extract_tables: bool = True
    extract_figures: bool = True
    extract_references: bool = True
    ocr_fallback: bool = False
    timeout_seconds: float = 120.0


@dataclass(slots=True)
class Settings:
    user_agent: str = "DocumentProcessingService/0.1"
    cache_dir: str = "./process_cache"
    pdf: ProcessingConfig = field(default_factory=ProcessingConfig)
    extra: dict = field(default_factory=dict)


def default_settings() -> Settings:
    return Settings()