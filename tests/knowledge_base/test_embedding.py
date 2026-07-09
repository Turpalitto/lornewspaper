"""Tests for embedding providers + registry."""

import pytest

from knowledge_base.config import EmbeddingConfig
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.embedding.jina import JinaEmbeddingProvider
from knowledge_base.embedding.ollama import OllamaEmbeddingProvider
from knowledge_base.embedding.openai import OpenAIEmbeddingProvider
from knowledge_base.embedding.registry import get_embedding_provider
from knowledge_base.embedding.voyage import VoyageEmbeddingProvider
from knowledge_base.exceptions import ConfigurationError, EmbeddingError


class MockEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "mock"

    def __init__(self, dims: int = 4):
        self._dims = dims

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 100) / 100.0 for _ in range(self._dims)] for t in texts]

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return "mock-model"


@pytest.mark.asyncio
async def test_mock_provider():
    p = MockEmbeddingProvider(dims=4)
    vecs = await p.embed(["hello", "world"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 4
    assert len(vecs[1]) == 4


@pytest.mark.asyncio
async def test_embed_query_returns_single():
    p = MockEmbeddingProvider(dims=8)
    vec = await p.embed_query("test query")
    assert len(vec) == 8


@pytest.mark.asyncio
async def test_ollama_provider_instantiation():
    p = OllamaEmbeddingProvider(base_url="http://localhost:11434", model="nomic-embed-text")
    assert p.provider_name == "ollama"
    assert p.dimensions == 768
    assert p.model_name == "nomic-embed-text"


@pytest.mark.asyncio
async def test_openai_provider_instantiation():
    p = OpenAIEmbeddingProvider(api_key="test", model="text-embedding-3-small")
    assert p.provider_name == "openai"
    assert p.dimensions == 1536
    assert p.model_name == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_jina_provider_instantiation():
    p = JinaEmbeddingProvider(api_key="test", model="jina-embeddings-v3")
    assert p.provider_name == "jina"
    assert p.dimensions == 1024


@pytest.mark.asyncio
async def test_voyage_provider_instantiation():
    p = VoyageEmbeddingProvider(api_key="test", model="voyage-2")
    assert p.provider_name == "voyage"
    assert p.dimensions == 1024


@pytest.mark.asyncio
async def test_embedding_ollama_fails_without_server():
    p = OllamaEmbeddingProvider(base_url="http://localhost:1", model="nomic-embed-text")
    with pytest.raises(EmbeddingError):
        await p.embed(["test"])


@pytest.mark.asyncio
async def test_registry_returns_ollama_by_default():
    cfg = EmbeddingConfig(provider="ollama")
    p = get_embedding_provider(cfg)
    assert isinstance(p, OllamaEmbeddingProvider)


@pytest.mark.asyncio
async def test_registry_returns_openai():
    cfg = EmbeddingConfig(provider="openai", api_key="sk-test")
    p = get_embedding_provider(cfg)
    assert isinstance(p, OpenAIEmbeddingProvider)


@pytest.mark.asyncio
async def test_registry_returns_jina():
    cfg = EmbeddingConfig(provider="jina", api_key="test")
    p = get_embedding_provider(cfg)
    assert isinstance(p, JinaEmbeddingProvider)


@pytest.mark.asyncio
async def test_registry_returns_voyage():
    cfg = EmbeddingConfig(provider="voyage", api_key="test")
    p = get_embedding_provider(cfg)
    assert isinstance(p, VoyageEmbeddingProvider)


@pytest.mark.asyncio
async def test_registry_unknown_provider():
    cfg = EmbeddingConfig(provider="nonexistent")
    with pytest.raises(ConfigurationError):
        get_embedding_provider(cfg)


def test_base_class():
    """Verify base class constraints via mock."""
    assert issubclass(MockEmbeddingProvider, BaseEmbeddingProvider)