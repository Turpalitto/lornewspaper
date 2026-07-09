"""Configuration for ResearchAgent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout_seconds: int = 60


@dataclass(slots=True)
class CacheConfig:
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 512


@dataclass(slots=True)
class WorkflowConfig:
    search_max_results: int = 10
    download_dir: str = "./downloads"
    parallel_downloads: int = 4
    skip_existing: bool = True


@dataclass(slots=True)
class Settings:
    llm: LLMConfig = field(default_factory=LLMConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)


def default_settings() -> Settings:
    return Settings()
