from __future__ import annotations

from fastapi import APIRouter, Depends
from structlog import get_logger

from api.dependencies import get_agent
from api.schemas.ingest import (
    DownloadRequest,
    DownloadResponse,
    IngestDocumentResponse,
    IngestRequest,
    IngestResponse,
)
from research_agent.agent import ResearchAgent

router = APIRouter(prefix="/ingest", tags=["ingest"])
_LOG = get_logger("api")


@router.post(
    "",
    response_model=IngestResponse,
    operation_id="ingest_articles",
    summary="Search, download, process, and index articles",
    description="Runs the full ingest pipeline: search → download → process → index.",
)
async def ingest_articles(
    body: IngestRequest,
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.ingest(query=body.query, max_results=body.max_results)
    documents = [
        IngestDocumentResponse(
            document_id=getattr(d, "document_id", ""),
            status=str(getattr(d, "status", "")),
            chunks=len(getattr(d, "chunks", []) or []),
        )
        for d in result.documents
    ]
    return IngestResponse(
        documents=documents,
        total=len(documents),
        elapsed_ms=result.elapsed_ms,
    )


@router.post(
    "/download",
    response_model=DownloadResponse,
    operation_id="search_and_download",
    summary="Search and download articles without indexing",
    description="Search for articles and download PDFs without processing or indexing.",
)
async def search_and_download(
    body: DownloadRequest,
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.search_and_download(
        query=body.query, max_results=body.max_results
    )
    return DownloadResponse(
        articles=result.articles,
        total=len(result.articles),
        elapsed_ms=result.elapsed_ms,
    )
