"""Embedding provider registry — switch providers via config."""

from __future__ import annotations

from knowledge_base.config import EmbeddingConfig
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.embedding.jina import JinaEmbeddingProvider
from knowledge_base.embedding.ollama import OllamaEmbeddingProvider
from knowledge_base.embedding.openai import OpenAIEmbeddingProvider
from knowledge_base.embedding.voyage import VoyageEmbeddingProvider
from knowledge_base.exceptions import ConfigurationError

_REGISTRY: dict[str, type[BaseEmbeddingProvider]] = {
    "openai": OpenAIEmbeddingProvider,
    "jina": JinaEmbeddingProvider,
    "voyage": VoyageEmbeddingProvider,
    "ollama": OllamaEmbeddingProvider,
}


def get_embedding_provider(config: EmbeddingConfig) -> BaseEmbeddingProvider:
    cls = _REGISTRY.get(config.provider)
    if cls is None:
        raise ConfigurationError(
            f"Unknown embedding provider '{config.provider}'. "
            f"Available: {list(_REGISTRY)}"
        )
    kwargs: dict = {}
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.base_url:
        kwargs["base_url"] = config.base_url
    if config.model:
        kwargs["model"] = config.model

    # Some providers accept extra args
    if config.provider == "ollama":
        return OllamaEmbeddingProvider(base_url=config.base_url, model=config.model)
    if config.provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=config.api_key or "",
            model=config.model,
            base_url=config.base_url,
        )
    if config.provider == "jina":
        return JinaEmbeddingProvider(
            api_key=config.api_key or "",
            model=config.model,
            base_url=config.base_url,
        )
    if config.provider == "voyage":
        return VoyageEmbeddingProvider(
            api_key=config.api_key or "",
            model=config.model,
            base_url=config.base_url,
        )
    return cls(**kwargs)