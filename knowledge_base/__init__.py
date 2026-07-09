"""KnowledgeBaseService — central storage, chunking, embedding, retrieval."""

from knowledge_base.models import (
    Chunk,
    ChunkEmbedding,
    DocumentStatistics,
    KnowledgeDocument,
    SearchQuery,
    SearchResult,
    SearchResultItem,
)
from knowledge_base.service import KnowledgeBaseService

__all__ = [
    "KnowledgeBaseService",
    "KnowledgeDocument",
    "Chunk",
    "ChunkEmbedding",
    "KnowledgeStatistics",
    "SearchQuery",
    "SearchResult",
    "SearchResultItem",
]
__version__ = "0.1.0"