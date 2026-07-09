"""ResearchAgent — high-level orchestrator for research workflows."""

from __future__ import annotations

import time
from typing import Any

import structlog

from research_agent.cache import ResponseCache
from research_agent.config import Settings, default_settings
from research_agent.exceptions import (
    AgentBusyError,
    DocumentNotFoundError,
    ResearchAgentError,
)
from research_agent.models import (
    AgentRequest,
    AgentResult,
    AgentStatus,
    Answer,
)
from research_agent.prompts.qa import QA_SYSTEM_PROMPT, build_qa_prompt
from research_agent.prompts.similar import SIMILAR_SYSTEM_PROMPT, build_similar_prompt
from research_agent.prompts.summarize import SUMMARIZE_SYSTEM_PROMPT, build_summary_prompt
from research_agent.providers.registry import discover_providers, get_llm_provider
from research_agent.workflow import (
    download_article,
    full_ingest_pipeline,
    index_document,
    process_document,
    search_articles,
)

_LOG = structlog.get_logger("research_agent")


def _pdf_path_to_download_result(path: str):
    """Create a minimal download result from a PDF path for processing."""
    from pathlib import Path

    article_id = Path(path).stem
    try:
        from download_service.models import DownloadResult, DownloadStatus
        return DownloadResult(
            article_id=article_id,
            source="manual",
            download_type="pdf",
            status=DownloadStatus.COMPLETED,
            file_path=path,
            mime_type="application/pdf",
        )
    except ImportError:
        class _Fake:
            article_id = article_id
            source = "manual"
            download_type = "pdf"
            file_path = path
            mime_type = "application/pdf"
            class _S:
                value = "completed"
            status = _S()
        return _Fake()


class ResearchAgent:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        knowledge_base=None,
        cache: ResponseCache | None = None,
    ):
        self._settings = settings or default_settings()
        self._kb = knowledge_base
        self._cache = cache or ResponseCache(
            ttl_seconds=self._settings.cache.ttl_seconds,
            max_size=self._settings.cache.max_size,
        )
        self._status = AgentStatus.IDLE
        discover_providers()

    @property
    def status(self) -> AgentStatus:
        return self._status

    async def _ensure_kb(self):
        if self._kb is None:
            from knowledge_base.config import Settings as KBSettings
            from knowledge_base.service import KnowledgeBaseService
            s = KBSettings()
            s.storage.database_path = os.environ.get(
                "KB_DATABASE_PATH", ":memory:"
            )
            if persist := os.environ.get("KB_VECTOR_PERSIST_DIR"):
                s.vector.persist_directory = persist
            self._kb = KnowledgeBaseService(settings=s)
        return self._kb

    async def close(self) -> None:
        if self._kb is not None:
            await self._kb.close()

    async def __aenter__(self) -> ResearchAgent:
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    # ---- public API -------------------------------------------------------

    async def search(self, query: str, max_results: int = 10) -> AgentResult:
        return await self._run(
            AgentRequest(query=query, max_results=max_results),
            self._do_search,
        )

    async def search_and_download(
        self, query: str, max_results: int = 5
    ) -> AgentResult:
        return await self._run(
            AgentRequest(query=query, max_results=max_results),
            self._do_search_and_download,
        )

    async def ingest(self, query: str, max_results: int = 5) -> AgentResult:
        return await self._run(
            AgentRequest(query=query, max_results=max_results),
            self._do_ingest,
        )

    async def ingest_article(self, article: dict[str, Any]) -> AgentResult:
        req = AgentRequest(query=article.get("title", ""))
        async def _run_ingest(_req, _res):
            await self._do_ingest_article(_req, _res, article)
        return await self._run(req, _run_ingest)

    async def ingest_pdf(self, path: str) -> AgentResult:
        req = AgentRequest(query=path)
        async def _run_ingest_pdf(_req, _res):
            await self._do_ingest_pdf(_req, _res, path)
        return await self._run(req, _run_ingest_pdf)

    async def ask(self, question: str, **kwargs) -> AgentResult:
        req = AgentRequest(
            query=question,
            llm_provider=kwargs.pop("llm_provider", self._settings.llm.provider),
            temperature=kwargs.pop("temperature", self._settings.llm.temperature),
            max_tokens=kwargs.pop("max_tokens", self._settings.llm.max_tokens),
        )
        return await self._run(req, self._do_ask)

    async def summarize(self, document_id: str) -> AgentResult:
        req = AgentRequest(document_id=document_id)
        return await self._run(req, self._do_summarize)

    async def similar(self, document_id: str) -> AgentResult:
        req = AgentRequest(document_id=document_id)
        return await self._run(req, self._do_similar)

    async def search_chunks(self, query: str, **kwargs) -> AgentResult:
        req = AgentRequest(query=query, **kwargs)
        return await self._run(req, self._do_search_chunks)

    async def search_documents(self, query: str) -> AgentResult:
        req = AgentRequest(query=query)
        return await self._run(req, self._do_search_documents)

    # ---- internal ---------------------------------------------------------

    async def _run(self, request: AgentRequest, fn) -> AgentResult:
        if self._status == AgentStatus.RUNNING:
            raise AgentBusyError("Agent is already running")
        self._status = AgentStatus.RUNNING
        start = time.perf_counter()
        result = AgentResult(request=request, status=AgentStatus.RUNNING)
        try:
            await fn(request, result)
            result.status = AgentStatus.COMPLETED
        except ResearchAgentError as exc:
            result.status = AgentStatus.FAILED
            result.error = str(exc)
            _LOG.error("agent_error", error=str(exc))
        except Exception as exc:
            result.status = AgentStatus.FAILED
            result.error = f"Unexpected error: {exc}"
            _LOG.error("agent_unexpected_error", error=str(exc))
        finally:
            result.elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            self._status = AgentStatus.IDLE
        return result

    async def _do_search(self, req: AgentRequest, result: AgentResult) -> None:
        articles = await search_articles(req.query, req.max_results)
        result.articles = articles

    async def _do_search_and_download(
        self, req: AgentRequest, result: AgentResult
    ) -> None:
        articles = await search_articles(req.query, req.max_results)
        result.articles = articles
        for article in articles:
            await download_article(article, download_dir=self._settings.workflow.download_dir)

    async def _do_ingest(self, req: AgentRequest, result: AgentResult) -> None:
        docs = await full_ingest_pipeline(
            req.query,
            max_results=req.max_results,
            download_dir=self._settings.workflow.download_dir,
        )
        result.documents = [
            await self._load_doc(d["document_id"])
            for d in docs if "document_id" in d
        ]

    async def _do_ingest_article(
        self, req: AgentRequest, result: AgentResult, article: dict
    ) -> None:
        path = await download_article(article, download_dir=self._settings.workflow.download_dir)
        if path:
            from research_agent.workflow import _make_download_result
            dl_result = _make_download_result(article, path)
            processed = await process_document(dl_result)
            if processed:
                doc = await index_document(processed)
                if doc:
                    result.documents = [doc]

    async def _do_ingest_pdf(
        self, req: AgentRequest, result: AgentResult, path: str
    ) -> None:
        processed = await process_document(
            _pdf_path_to_download_result(path)
        )
        if processed:
            doc = await index_document(processed)
            if doc:
                result.documents = [doc]

    async def _do_ask(self, req: AgentRequest, result: AgentResult) -> None:
        cache_key = f"qa:{req.query}"
        cached = self._cache.get(cache_key)
        if cached:
            result.answer = cached
            return

        kb = await self._ensure_kb()
        search_result = await kb.search_text(
            req.query,
            top_k=10,
            score_threshold=req.score_threshold,
        )
        result.search_result = search_result

        chunks_data = []
        for item in search_result.items:
            chunks_data.append({
                "document_id": item.chunk.document_id,
                "text": item.chunk.text,
                "score": item.score,
            })

        if not chunks_data:
            result.answer = Answer(
                answer="No relevant documents found to answer the question.",
                sources=[],
            )
            return

        system_prompt = QA_SYSTEM_PROMPT
        user_prompt = build_qa_prompt(req.query, chunks_data)

        provider_name = req.llm_provider or self._settings.llm.provider
        model = self._settings.llm.model
        api_key = self._settings.llm.api_key
        base_url = self._settings.llm.base_url

        provider = get_llm_provider(
            provider=provider_name,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

        llm_start = time.perf_counter()
        response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        llm_elapsed = round((time.perf_counter() - llm_start) * 1000, 1)

        doc_ids = list({c["document_id"] for c in chunks_data})
        avg_confidence = (
            sum(c["score"] for c in chunks_data) / len(chunks_data)
            if chunks_data else 0.0
        )
        answer = Answer(
            answer=response,
            chunks=[item.chunk for item in search_result.items],
            sources=doc_ids,
            elapsed_ms=llm_elapsed,
            llm_model=provider.model_name,
            llm_provider=provider_name,
            confidence=avg_confidence,
        )
        result.answer = answer
        self._cache.set(cache_key, answer)

    async def _do_summarize(self, req: AgentRequest, result: AgentResult) -> None:
        kb = await self._ensure_kb()
        chunks = await kb.get_chunks(req.document_id)
        if not chunks:
            raise DocumentNotFoundError(f"Document '{req.document_id}' not found")

        chunks_data = [{"text": c.text, "heading": c.heading} for c in chunks]
        system_prompt = SUMMARIZE_SYSTEM_PROMPT
        user_prompt = build_summary_prompt(chunks_data)

        provider = get_llm_provider(
            provider=self._settings.llm.provider,
            api_key=self._settings.llm.api_key,
            model=self._settings.llm.model,
            base_url=self._settings.llm.base_url,
        )
        response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        result.answer = Answer(
            answer=response,
            chunks=chunks,
            sources=[req.document_id],
            llm_model=provider.model_name,
            llm_provider=self._settings.llm.provider,
        )

    async def _do_similar(self, req: AgentRequest, result: AgentResult) -> None:
        kb = await self._ensure_kb()
        chunks = await kb.get_chunks(req.document_id)
        if not chunks:
            raise DocumentNotFoundError(f"Document '{req.document_id}' not found")

        chunk_texts = [c.text for c in chunks if c.text]
        if not chunk_texts:
            raise DocumentNotFoundError(f"No text content for document '{req.document_id}'")

        query_text = " ".join(chunk_texts[:3])
        search_result = await kb.search_text(query_text, top_k=10)
        result.search_result = search_result

        candidate_chunks = [
            {"text": c.text, "document_id": c.document_id}
            for c in search_result.items
        ]
        source_text = "\n".join(chunk_texts[:5])

        system_prompt = SIMILAR_SYSTEM_PROMPT
        user_prompt = build_similar_prompt(source_text, candidate_chunks)

        provider = get_llm_provider(
            provider=self._settings.llm.provider,
            api_key=self._settings.llm.api_key,
            model=self._settings.llm.model,
            base_url=self._settings.llm.base_url,
        )
        response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        result.answer = Answer(
            answer=response,
            chunks=chunks,
            sources=list({c["document_id"] for c in candidate_chunks}),
            llm_model=provider.model_name,
            llm_provider=self._settings.llm.provider,
        )

    async def _do_search_chunks(self, req: AgentRequest, result: AgentResult) -> None:
        kb = await self._ensure_kb()
        search_result = await kb.search_text(
            req.query,
            top_k=req.max_results,
            score_threshold=req.score_threshold,
            metadata_filter=req.metadata_filter,
        )
        result.search_result = search_result

    async def _do_search_documents(self, req: AgentRequest, result: AgentResult) -> None:
        kb = await self._ensure_kb()
        docs = await kb.list_documents()
        if req.query:
            docs = [
                d for d in docs
                if req.query.lower() in (d.metadata.get("title", "") or "").lower()
            ]
        result.documents = docs

    async def _load_doc(self, document_id: str):
        kb = await self._ensure_kb()
        return await kb.get_document(document_id)