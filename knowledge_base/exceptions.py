"""KnowledgeBase exception hierarchy."""

from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base for all KnowledgeBase errors."""


class EmbeddingError(KnowledgeBaseError, RuntimeError):
    """Embedding generation failed."""


class VectorStoreError(KnowledgeBaseError, RuntimeError):
    """Vector store operation failed."""


class StorageError(KnowledgeBaseError, RuntimeError):
    """Document storage operation failed."""


class ChunkingError(KnowledgeBaseError, ValueError):
    """Chunking operation failed."""


class SearchError(KnowledgeBaseError, RuntimeError):
    """Search operation failed."""


class DocumentNotFoundError(KnowledgeBaseError, KeyError):
    """Document not found in storage."""


class ConfigurationError(KnowledgeBaseError, ValueError):
    """Invalid configuration."""