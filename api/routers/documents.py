from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from structlog import get_logger

from api.dependencies import get_agent
from api.schemas.documents import (
    ChunkListResponse,
    ChunkRecord,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentRecord,
    SimilarResponse,
    SummaryResponse,
)
from research_agent.agent import ResearchAgent

router = APIRouter(prefix="/documents", tags=["documents"])
_LOG = get_logger("api")


@router.get(
    "",
    response_model=DocumentListResponse,
    operation_id="list_documents",
    summary="List indexed documents",
    description="Returns paginated list of indexed documents with metadata.",
)
async def list_documents(
    query: str = Query(default="", description="Filter by title"),
    cursor: str | None = Query(default=None, description="Pagination cursor"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.search_documents(query=query)
    docs = result.documents or []
    total = len(docs)
    page = docs[:limit]
    has_more = total > limit
    return DocumentListResponse(
        items=[
            DocumentRecord(
                document_id=getattr(d, "document_id", ""),
                metadata=DocumentMetadata(
                    title=(getattr(d, "metadata", {}) or {}).get("title", ""),
                    authors=(getattr(d, "metadata", {}) or {}).get("authors", []),
                    source=(getattr(d, "metadata", {}) or {}).get("source", ""),
                ),
                chunk_count=len(getattr(d, "chunks", []) or []),
                created_at=str(getattr(d, "created_at", "")),
            )
            for d in page
        ],
        next_cursor=page[-1].document_id if has_more else None,
        has_more=has_more,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    operation_id="get_document",
    summary="Get document details",
    description="Returns document metadata and chunks by ID.",
)
async def get_document(
    document_id: str = Path(description="Document ID"),
    agent: ResearchAgent = Depends(get_agent),
):
    doc = await agent._load_doc(document_id)
    if doc is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    return DocumentDetailResponse(
        document_id=getattr(doc, "document_id", document_id),
        metadata=DocumentMetadata(
            title=(getattr(doc, "metadata", {}) or {}).get("title", ""),
            authors=(getattr(doc, "metadata", {}) or {}).get("authors", []),
            source=(getattr(doc, "metadata", {}) or {}).get("source", ""),
        ),
        chunks=[
            {
                "id": getattr(c, "id", ""),
                "text": getattr(c, "text", ""),
                "heading": getattr(c, "heading", ""),
                "chunk_index": getattr(c, "chunk_index", 0),
            }
            for c in (getattr(doc, "chunks", []) or [])
        ],
        created_at=str(getattr(doc, "created_at", "")),
    )


@router.get(
    "/{document_id}/chunks",
    response_model=ChunkListResponse,
    operation_id="get_document_chunks",
    summary="Get document chunks",
    description="Returns paginated chunks for a document.",
)
async def get_document_chunks(
    document_id: str = Path(description="Document ID"),
    cursor: str | None = Query(default=None, description="Pagination cursor"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    agent: ResearchAgent = Depends(get_agent),
):
    kb = await agent._ensure_kb()
    chunks = await kb.get_chunks(document_id)
    total = len(chunks)
    start = 0
    if cursor:
        for i, c in enumerate(chunks):
            if getattr(c, "id", "") == cursor:
                start = i + 1
                break
    page = chunks[start:start + limit]
    has_more = (start + limit) < total
    return ChunkListResponse(
        items=[
            ChunkRecord(
                chunk_id=getattr(c, "id", ""),
                text=getattr(c, "text", ""),
                heading=getattr(c, "heading", ""),
                chunk_index=getattr(c, "chunk_index", 0),
            )
            for c in page
        ],
        next_cursor=page[-1].id if has_more else None,
        has_more=has_more,
        limit=limit,
    )


@router.get(
    "/{document_id}/summary",
    response_model=SummaryResponse,
    operation_id="get_document_summary",
    summary="Summarize a document",
    description="Generate an LLM-powered summary of an indexed document.",
)
async def get_document_summary(
    document_id: str = Path(description="Document ID"),
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.summarize(document_id=document_id)
    return SummaryResponse(
        document_id=document_id,
        summary=result.answer.answer if result.answer else "",
        llm_model=result.answer.llm_model if result.answer else "",
        llm_provider=result.answer.llm_provider if result.answer else "",
        elapsed_ms=result.elapsed_ms,
    )


@router.get(
    "/{document_id}/similar",
    response_model=SimilarResponse,
    operation_id="get_similar_documents",
    summary="Find similar documents",
    description="Find and analyze documents similar to the specified document.",
)
async def get_similar_documents(
    document_id: str = Path(description="Document ID"),
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.similar(document_id=document_id)
    return SimilarResponse(
        document_id=document_id,
        analysis=result.answer.answer if result.answer else "",
        related_documents=result.answer.sources if result.answer else [],
        llm_model=result.answer.llm_model if result.answer else "",
        llm_provider=result.answer.llm_provider if result.answer else "",
        elapsed_ms=result.elapsed_ms,
    )
