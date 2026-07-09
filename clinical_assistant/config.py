"""Configuration for Clinical Guideline Assistant."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GuidelineSourceConfig:
    ru_minzdrav_enabled: bool = True
    ru_minzdrav_base_url: str = "https://cr.minzdrav.gov.ru"
    nice_enabled: bool = False
    sign_enabled: bool = False
    who_enabled: bool = False
    check_interval_hours: int = 24


@dataclass(slots=True)
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 2048
    citation_confidence_threshold: float = 0.5


@dataclass(slots=True)
class Settings:
    app_name: str = "Clinical Guideline Assistant"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1/clinical"
    debug: bool = False
    log_level: str = "INFO"
    guideline: GuidelineSourceConfig = field(default_factory=GuidelineSourceConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @classmethod
    def from_env(cls) -> Settings:
        import os
        s = cls()
        s.debug = os.environ.get("CGA_DEBUG", "").lower() in ("1", "true")
        s.log_level = os.environ.get("CGA_LOG_LEVEL", "INFO")
        s.llm.provider = os.environ.get("CGA_LLM_PROVIDER", "openai")
        s.llm.model = os.environ.get("CGA_LLM_MODEL", "gpt-4o")
        s.llm.temperature = float(os.environ.get("CGA_LLM_TEMPERATURE", "0.1"))
        return s
