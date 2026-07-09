"""LLM provider registry and factory."""

from __future__ import annotations

import structlog

from research_agent.exceptions import ConfigurationError, UnknownProviderError
from research_agent.providers.base import BaseLLMProvider

_LOG = structlog.get_logger("research_agent")

_REGISTRY: dict[str, type[BaseLLMProvider]] = {}


def register(name: str, provider_cls: type[BaseLLMProvider]) -> None:
    """Register a provider class by name."""
    _REGISTRY[name] = provider_cls


def get_llm_provider(
    provider: str,
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> BaseLLMProvider:
    """Factory: create provider instance from registry."""
    cls = _REGISTRY.get(provider)
    if cls is None:
        available = ", ".join(_REGISTRY)
        raise UnknownProviderError(
            f"Unknown LLM provider '{provider}'. Available: {available}"
        )
    if not api_key and provider in ("openai", "anthropic", "gemini"):
        raise ConfigurationError(f"API key required for provider '{provider}'")
    kwargs: dict[str, str] = {"api_key": api_key, "model": model}
    if base_url:
        kwargs["base_url"] = base_url
    _LOG.info("llm_provider_created", provider=provider, model=model)
    return cls(**kwargs)


def list_providers() -> list[str]:
    """Return registered provider names."""
    return list(_REGISTRY)


def discover_providers() -> None:
    """Import and register all built-in providers, skipping missing packages."""
    _REGISTRY.clear()
    try:
        from research_agent.providers.openai import OpenAIProvider
        _REGISTRY["openai"] = OpenAIProvider
    except ImportError:
        _LOG.info("openai_package_not_installed")
    try:
        from research_agent.providers.anthropic import AnthropicProvider
        _REGISTRY["anthropic"] = AnthropicProvider
    except ImportError:
        _LOG.info("anthropic_package_not_installed")
    try:
        from research_agent.providers.gemini import GeminiProvider
        _REGISTRY["gemini"] = GeminiProvider
    except ImportError:
        _LOG.info("gemini_package_not_installed")
    try:
        from research_agent.providers.ollama import OllamaProvider
        _REGISTRY["ollama"] = OllamaProvider
    except ImportError:
        _LOG.info("ollama_package_not_installed")
    _LOG.info("providers_discovered", count=len(_REGISTRY))