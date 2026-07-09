"""Research workflow pipelines — orchestrate search→download→process→index."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from download_service.models import DownloadResult, DownloadStatus
from research_agent.exceptions import WorkflowError

_LOG = structlog.get_logger("research_agent")


async def search_articles(query: str, max_results: int = 10) -> list[dict]:
    """Search academic literature. Returns list of article dicts."""
    from search_service.service import SearchService

    svc = SearchService()
    try:
        result = await svc.search_all(query, limit=max_results)
        articles = []
        for article in result if isinstance(result, list) else getattr(result, "articles", result):
            articles.append({
                "id": getattr(article, "id", ""),
                "title": (
                    getattr(article, "title", "")
                    or getattr(article, "article_title", "")
                ),
                "doi": getattr(article, "doi", ""),
                "pmid": getattr(article, "pmid", ""),
                "pmcid": getattr(article, "pmcid", ""),
                "authors": getattr(article, "authors", []),
                "year": getattr(article, "year", None),
                "journal": getattr(article, "journal", ""),
                "abstract": getattr(article, "abstract", ""),
            })
        _LOG.info("search_complete", query=query, count=len(articles))
        return articles
    except Exception as exc:
        raise WorkflowError(f"Search failed: {exc}") from exc


async def download_article(
    article: dict,
    download_dir: str = "./downloads",
) -> str | None:
    """Download an article PDF via DownloadService.

    Builds an Article object from dict, downloads, returns file path or None.
    """
    from download_service.config import Settings as DownloadSettings
    from download_service.service import DownloadService

    dl_settings = DownloadSettings(cache_dir=download_dir)
    svc = DownloadService(settings=dl_settings)
    try:
        article_obj = _dict_to_article(article)
        if not article_obj:
            return None
        result = await svc.download(article=article_obj)
        if result and result.status and result.status.value in ("completed", "partial"):
            path = result.file_path
            _LOG.info("download_complete", path=path)
            return path
        status_str = str(result.status) if result else "none"
        _LOG.warning("download_failed", article=article.get("id"), status=status_str)
        return None
    except Exception as exc:
        _LOG.error("download_error", article=article.get("id"), error=str(exc))
        return None


async def process_document(download_result) -> Any:
    """Process a download result into a ProcessedDocument."""
    from document_processing_service.service import DocumentProcessingService

    svc = DocumentProcessingService()
    try:
        result = await svc.process(download_result)
        if result:
            _LOG.info("processing_complete", article=result.article_id)
            return result
        _LOG.warning("processing_returned_none")
        return None
    except Exception as exc:
        _LOG.error("processing_error", error=str(exc))
        return None


async def index_document(processed_doc) -> Any:
    """Index a processed document into KnowledgeBase.

    Returns KnowledgeDocument or None.
    """
    from knowledge_base.config import Settings as KBSettings
    from knowledge_base.service import KnowledgeBaseService

    s = KBSettings()
    s.storage.database_path = ":memory:"
    kb = KnowledgeBaseService(settings=s)
    try:
        doc = await kb.index(processed_doc)
        chunk_count = len(doc.chunks) if doc.chunks else 0
        _LOG.info("indexing_complete", article=processed_doc.article_id, chunks=chunk_count)
        return doc
    except Exception as exc:
        doc_id = getattr(processed_doc, "article_id", "?")
        _LOG.error("indexing_error", article=doc_id, error=str(exc))
        return None
    finally:
        await kb.close()


async def full_ingest_pipeline(
    query: str,
    max_results: int = 5,
    download_dir: str = "./downloads",
) -> list[dict]:
    """Run full search->download->process->index pipeline.

    Returns list of indexed document info dicts.
    """
    articles = await search_articles(query, max_results=max_results)
    results = []
    for article in articles:
        path = await download_article(article, download_dir=download_dir)
        if not path:
            continue
        download_result = _make_download_result(article, path)
        processed = await process_document(download_result)
        if not processed:
            continue
        doc = await index_document(processed)
        if doc:
            results.append({
                "document_id": getattr(doc, "document_id", ""),
                "status": (
                    doc.status.value
                    if hasattr(doc.status, "value")
                    else str(getattr(doc, "status", ""))
                ),
                "chunks": len(getattr(doc, "chunks", []) or []),
            })
    return results


def _dict_to_article(article: dict):
    """Convert dict to Article object matching search_service.models.Article."""
    from search_service.models import Article

    authors_raw = article.get("authors", [])
    authors = []
    for a in authors_raw:
        if isinstance(a, str):
            authors.append(a)
        elif isinstance(a, dict):
            authors.append(
                str(a.get("name", a.get("full_name", a.get("id", ""))))
            )
        else:
            authors.append(str(a))

    return Article(
        id=article.get("id", ""),
        title=article.get("title", ""),
        doi=article.get("doi", ""),
        pmid=article.get("pmid", ""),
        pmcid=article.get("pmcid", ""),
        authors=authors,
        year=article.get("year"),
        journal=article.get("journal", ""),
        abstract=article.get("abstract", ""),
        source="research_agent",
        retrieved_at=datetime.now(),
    )


def _make_download_result(article: dict, file_path: str) -> DownloadResult:
    """Build a DownloadResult for DocumentProcessingService."""
    return DownloadResult(
        article_id=article.get("id", article.get("pmid", file_path)),
        source=article.get("journal", "unknown"),
        download_type="pdf",
        status=DownloadStatus.COMPLETED,
        file_path=file_path,
        mime_type="application/pdf",
    )
