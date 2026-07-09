"""Indexing pipeline — chunk → embed → store → vector."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import structlog

from knowledge_base._async_utils import to_thread
from knowledge_base.chunking.fixed import FixedChunker
from knowledge_base.chunking.section import SectionChunker
from knowledge_base.chunking.sentence import SentenceChunker
from knowledge_base.config import Settings
from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.exceptions import ChunkingError, EmbeddingError, StorageError, VectorStoreError
from knowledge_base.models import (
    Chunk,
    ChunkEmbedding,
    DocumentStatistics,
    IndexingStatus,
    KnowledgeDocument,
)
from document_processing_service.models import ProcessedDocument
from knowledge_base.storage.base import BaseStorage
from knowledge_base.vector.base import BaseVectorStore

_LOG = structlog.get_logger("knowledge_base")


class IndexingService:
    def __init__(
        self,
        settings: Settings,
        storage: BaseStorage,
        vector_store: BaseVectorStore,
        embedding_provider: BaseEmbeddingProvider,
    ):
        self._settings = settings
        self._storage = storage
        self._vector = vector_store
        self._embedding = embedding_provider
        self._chunker = self._build_chunker()

    def _build_chunker(self):
        cfg = self._settings.chunking
        if cfg.strategy == "section":
            return SectionChunker(min_chunk_length=cfg.min_chunk_length)
        if cfg.strategy == "sentence":
            return SentenceChunker(min_chunk_length=cfg.min_chunk_length)
        if cfg.strategy == "fixed":
            return FixedChunker(
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap,
                min_chunk_length=cfg.min_chunk_length,
            )
        raise ChunkingError(f"Unknown chunking strategy: {cfg.strategy}")

    async def index(self, processed_doc: ProcessedDocument) -> KnowledgeDocument:
        doc_id = processed_doc.article_id
        _LOG.info("indexing_document", document_id=doc_id)

        doc = KnowledgeDocument(
            document_id=doc_id,
            status=IndexingStatus.INDEXING,
            metadata=_extract_metadata(processed_doc),
            source_file=processed_doc.source_file,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        try:
            # 1. Chunk
            section_data = [
                {"heading": s.heading, "content": s.content, "level": s.level}
                for s in processed_doc.sections
            ]
            chunks = await to_thread(
                self._chunker.chunk,
                doc_id,
                processed_doc.raw_text or processed_doc.markdown,
                metadata={"sections": section_data},
            )
            doc.chunks = chunks
            doc.statistics.chunking_strategy = self._settings.chunking.strategy
            doc.statistics.chunk_overlap = self._settings.chunking.chunk_overlap

            _LOG.info("chunks_created", document_id=doc_id, count=len(chunks))

            # 2. Embed
            texts = [c.text for c in chunks]
            embeddings = await self._embedding.embed(texts)
            doc_embeddings: list[ChunkEmbedding] = []
            for i, chunk in enumerate(chunks):
                doc_embeddings.append(
                    ChunkEmbedding(
                        chunk_id=chunk.id,
                        document_id=doc_id,
                        embedding=embeddings[i],
                        model=self._embedding.model_name,
                        dimensions=self._embedding.dimensions,
                    )
                )
            doc.embeddings = doc_embeddings

            _LOG.info("embeddings_created", document_id=doc_id, count=len(doc_embeddings))

            # 3. Store chunks in SQLite
            await self._storage.save_chunks(chunks)
            await self._storage.save_embeddings(doc_embeddings)

            # 4. Store vectors
            await self._vector.upsert(doc_embeddings)

            # 5. Update statistics
            doc.statistics = _compute_stats(doc, chunks, doc_embeddings, self._embedding.model_name)

            # 6. Save document record
            doc.status = IndexingStatus.COMPLETED
            await self._storage.save_document(doc)

            _LOG.info("indexing_complete", document_id=doc_id, chunks=len(chunks))
            return doc

        except (ChunkingError, EmbeddingError, StorageError, VectorStoreError, ValueError) as exc:
            doc.status = IndexingStatus.FAILED
            doc.metadata["error"] = str(exc)
            await self._storage.save_document(doc)
            _LOG.error("indexing_failed", document_id=doc_id, error=str(exc))
            return doc


def _extract_metadata(processed: ProcessedDocument) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if hasattr(processed, "metadata") and processed.metadata:
        m = processed.metadata
        meta["title"] = getattr(m, "title", "")
        meta["abstract"] = getattr(m, "abstract", "")
        meta["authors"] = getattr(m, "authors", [])
        meta["journal"] = getattr(m, "journal", "")
        meta["year"] = getattr(m, "year", 0)
        meta["doi"] = getattr(m, "doi", "")
    meta["total_pages"] = processed.stats.total_pages if hasattr(processed, "stats") else 0
    return meta


def _compute_stats(
    doc: KnowledgeDocument,
    chunks: list[Chunk],
    embeddings: list[ChunkEmbedding],
    model_name: str,
) -> DocumentStatistics:
    total_tables = sum(len(c.tables) for c in chunks)
    total_figures = sum(len(c.figures) for c in chunks)
    total_citations = sum(len(c.citations) for c in chunks)
    return DocumentStatistics(
        total_chunks=len(chunks),
        total_tokens=sum(c.token_count for c in chunks),
        total_words=sum(c.word_count for c in chunks),
        total_tables=total_tables,
        total_figures=total_figures,
        total_citations=total_citations,
        embedding_model=model_name,
        chunking_strategy=doc.statistics.chunking_strategy if doc.statistics else "",
        chunk_overlap=doc.statistics.chunk_overlap if doc.statistics else 0,
    )