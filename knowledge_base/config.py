"""KnowledgeBase configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ChunkingConfig:
    strategy: str = "section"
    chunk_size: int = 512
    chunk_overlap: int = 64
    min_chunk_length: int = 20


@dataclass(slots=True)
class EmbeddingConfig:
    provider: str = "ollama"
    model: str = "nomic-embed-text"
    dimensions: int = 768
    api_key: str = ""
    base_url: str = "http://localhost:11434"
    batch_size: int = 16


@dataclass(slots=True)
class VectorConfig:
    backend: str = "chroma"
    collection_name: str = "documents"
    persist_directory: str = "./vector_store"
    distance: str = "cosine"


@dataclass(slots=True)
class StorageConfig:
    backend: str = "sqlite"
    database_path: str = "./knowledge_base.db"


@dataclass(slots=True)
class Settings:
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)


def default_settings() -> Settings:
    return Settings()