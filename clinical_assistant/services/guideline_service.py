"""Guideline ingestion, indexing, and search service.

Uses LORNEWS for:
  - Document processing (PDF text extraction)
  - Knowledge base (chunking, embedding, vector search)
  - ResearchAgent (RAG for question answering)
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import structlog

from clinical_assistant.models.guideline import (
    Guideline,
    GuidelineSection,
    GuidelineSource,
    GuidelineStatus,
    Recommendation,
)
from clinical_assistant.services.recommendation_extractor import RecommendationExtractor
from clinical_assistant.services.citation_verifier import CitationVerifier

_LOG = structlog.get_logger("clinical_assistant")

# LORNEWS imports (external dependency)
try:
    from document_processing_service.models import ProcessedDocument
    from knowledge_base.models import SearchResult
    from knowledge_base.service import KnowledgeBaseService
    from research_agent.agent import ResearchAgent
    HAS_LORNEWS = True
except ImportError:
    HAS_LORNEWS = False
    ProcessedDocument = Any
    SearchResult = Any
    KnowledgeBaseService = Any
    ResearchAgent = Any


class GuidelineService:
    """Ingest, index, and search clinical guidelines."""

    def __init__(
        self,
        knowledge_base: KnowledgeBaseService | None = None,
        recommendation_extractor: RecommendationExtractor | None = None,
        citation_verifier: CitationVerifier | None = None,
    ):
        self._recommendation_extractor = recommendation_extractor or RecommendationExtractor()
        self._citation_verifier = citation_verifier or CitationVerifier()
        self._kb = knowledge_base
        self._guidelines: dict[str, Guideline] = {}

    async def ingest_pdf(self, file_path: str, source: GuidelineSource = GuidelineSource.RU_MINZDRAV) -> Guideline:
        """Ingest a guideline PDF through the LORNEWS pipeline.

        Uses DocumentProcessingService for text extraction,
        RecommendationExtractor for parsing, KnowledgeBaseService for indexing.
        """
        if not HAS_LORNEWS:
            raise RuntimeError("LORNEWS is required for PDF ingestion")

        from document_processing_service.service import DocumentProcessingService
        from download_service.models import DownloadResult, DownloadStatus

        # 1. Extract text via LORNEWS DocumentProcessingService
        _LOG.info("guideline_extracting", file_path=file_path)
        dl_result = DownloadResult(
            article_id=Path(file_path).stem,
            source=source.value,
            download_type="pdf",
            status=DownloadStatus.COMPLETED,
            file_path=file_path,
            mime_type="application/pdf",
        )
        processor = DocumentProcessingService()
        processed = await processor.process(dl_result)

        # 2. Build Guideline model
        guideline = self._build_guideline(processed, source, file_path)

        # 3. Extract recommendations from each section
        for section in processed.sections:
            section_id = str(uuid.uuid4())
            recs = self._recommendation_extractor.extract_from_section(
                section.content, section.heading, guideline.id, section_id,
            )
            gs = GuidelineSection(
                id=section_id,
                heading=section.heading,
                level=section.level or 1,
                content=section.content,
                recommendations=recs,
            )
            guideline.sections.append(gs)
            guideline.recommendations.extend(recs)

        # 4. Index in KnowledgeBase via LORNEWS
        await self._index_guideline(guideline, processed)

        # 5. Register citations
        await self._register_citations(guideline)

        self._guidelines[guideline.id] = guideline
        _LOG.info("guideline_ingested", id=guideline.id, title=guideline.title_ru, sections=len(guideline.sections))
        return guideline

    async def ingest_text(self, title: str, text: str, source: GuidelineSource = GuidelineSource.LOCAL) -> Guideline:
        """Ingest a guideline from raw text (no PDF processing needed)."""
        guideline = Guideline(
            id=str(uuid.uuid4()),
            title_ru=title,
            source=source,
            status=GuidelineStatus.ACTIVE,
        )

        # Simple section split by double newline
        blocks = text.strip().split("\n\n")
        for i, block in enumerate(blocks):
            lines = block.strip().split("\n")
            heading = lines[0] if lines else ""
            content = "\n".join(lines[1:]) if len(lines) > 1 else block
            section_id = str(uuid.uuid4())
            recs = self._recommendation_extractor.extract_from_section(
                content, heading, guideline.id, section_id,
            )
            gs = GuidelineSection(id=section_id, heading=heading, level=1, content=content, recommendations=recs)
            guideline.sections.append(gs)
            guideline.recommendations.extend(recs)

        if HAS_LORNEWS:
            await self._index_guideline(guideline)
            await self._register_citations(guideline)

        self._guidelines[guideline.id] = guideline
        return guideline

    async def search(self, query: str, top_k: int = 10) -> list[Guideline]:
        """Search guidelines by query text using LORNEWS KnowledgeBase vector search."""
        if not HAS_LORNEWS or self._kb is None:
            return self._keyword_search(query, top_k)

        result = await self._kb.search_text(query, top_k=top_k)
        doc_ids = set()
        for item in result.items:
            if item.chunk.document_id:
                doc_ids.add(item.chunk.document_id)

        return [g for gid, g in self._guidelines.items() if gid in doc_ids]

    async def ask(self, question: str, guideline_ids: list[str] | None = None) -> dict[str, Any]:
        """Ask a clinical question. Uses LORNEWS ResearchAgent for RAG."""
        if not HAS_LORNEWS:
            return self._rule_based_answer(question, guideline_ids)

        from research_agent.agent import ResearchAgent
        from research_agent.cache import ResponseCache
        from research_agent.config import Settings

        settings = Settings()
        settings.llm.provider = os.environ.get("CGA_LLM_PROVIDER", "openai")
        settings.llm.model = os.environ.get("CGA_LLM_MODEL", "gpt-4o")

        agent = ResearchAgent(settings=settings, knowledge_base=self._kb, cache=ResponseCache())
        try:
            result = await agent.ask(question)
            if result.answer:
                return {
                    "answer": result.answer.answer,
                    "sources": result.answer.sources or [],
                    "confidence": result.answer.confidence,
                    "elapsed_ms": result.elapsed_ms,
                }
        finally:
            await agent.close()

        return self._rule_based_answer(question, guideline_ids)

    def get_guideline(self, guideline_id: str) -> Guideline | None:
        return self._guidelines.get(guideline_id)

    def list_guidelines(self) -> list[Guideline]:
        return list(self._guidelines.values())

    async def _index_guideline(self, guideline: Guideline, processed: Any = None) -> None:
        """Index guideline in LORNEWS KnowledgeBase."""
        if not HAS_LORNEWS or self._kb is None:
            return

        from knowledge_base.config import Settings as KBSettings
        from knowledge_base.storage.sqlite import SQLiteStorage
        from knowledge_base.vector.base import BaseVectorStore

        if self._kb is None:
            self._kb = KnowledgeBaseService(settings=KBSettings())

        if processed is not None:
            # Use existing ProcessedDocument from ingestion
            await self._kb.index(processed)

    async def _register_citations(self, guideline: Guideline) -> None:
        """Register all recommendation source texts for citation verification."""
        for rec in guideline.recommendations:
            text = rec.text_ru or rec.text_en
            if text:
                self._citation_verifier.register_text(text, guideline.id)

    def _build_guideline(self, processed: Any, source: GuidelineSource, file_path: str) -> Guideline:
        """Build Guideline model from ProcessedDocument."""
        title = ""
        if hasattr(processed, "metadata") and processed.metadata:
            title = getattr(processed.metadata, "title", "") or ""

        return Guideline(
            id=str(uuid.uuid4()),
            title_ru=title,
            source=source,
            status=GuidelineStatus.ACTIVE,
            url=file_path,
        )

    def _keyword_search(self, query: str, top_k: int = 10) -> list[Guideline]:
        """Fallback keyword search when LORNEWS is unavailable."""
        query_lower = query.lower()
        scored: list[tuple[Guideline, float]] = []

        for guideline in self._guidelines.values():
            score = 0.0
            if query_lower in guideline.title_ru.lower():
                score += 10
            for section in guideline.sections:
                if query_lower in section.content.lower():
                    score += 5
                for rec in section.recommendations:
                    if query_lower in (rec.text_ru or "").lower():
                        score += 3
            if score > 0:
                scored.append((guideline, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [g for g, _ in scored[:top_k]]

    def _rule_based_answer(self, question: str, guideline_ids: list[str] | None = None) -> dict[str, Any]:
        """Fallback rule-based answer when LLM is unavailable."""
        guidelines = self._guidelines.values()
        if guideline_ids:
            guidelines = [g for g in guidelines if g.id in guideline_ids]

        relevant_recs: list[dict[str, Any]] = []
        q_lower = question.lower()

        for guideline in guidelines:
            for rec in guideline.recommendations:
                text = (rec.text_ru or rec.text_en or "").lower()
                if any(word in text for word in q_lower.split()):
                    relevant_recs.append({
                        "text": rec.text_ru or rec.text_en,
                        "strength": rec.strength.value,
                        "evidence_level": rec.evidence_level.value,
                        "guideline": guideline.title_ru or guideline.title_en,
                        "section": "",
                    })

        return {
            "answer": "Found relevant recommendations based on keyword matching.",
            "sources": [],
            "recommendations": relevant_recs,
            "confidence": 0.3,
        }
