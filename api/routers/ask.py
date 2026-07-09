from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from structlog import get_logger

from api.dependencies import get_agent
from api.schemas.ask import AnswerResponse, AskRequest, AskResponse, ChunkInfo
from research_agent.agent import ResearchAgent

router = APIRouter(prefix="/ask", tags=["ask"])
_LOG = get_logger("api")


@router.post(
    "",
    response_model=AskResponse,
    operation_id="ask_question",
    summary="Ask a research question",
    description="Query indexed documents with a natural language question. Uses RAG (retrieval-augmented generation) to answer from your document corpus.",
    responses={
        409: {"description": "Agent is busy processing another request"},
    },
)
async def ask_question(
    body: AskRequest,
    agent: ResearchAgent = Depends(get_agent),
):
    kwargs: dict[str, Any] = {}
    if body.llm_provider:
        kwargs["llm_provider"] = body.llm_provider
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    result = await agent.ask(question=body.question, **kwargs)

    chunks = []
    if result.answer and result.answer.chunks:
        for c in result.answer.chunks:
            chunks.append(ChunkInfo(
                document_id=getattr(c, "document_id", ""),
                text=getattr(c, "text", "")[:500],
                score=0.0,
                heading=getattr(c, "heading", ""),
            ))

    return AskResponse(
        answer=AnswerResponse(
            answer=result.answer.answer,
            sources=result.answer.sources,
            citations=[c.model_dump() for c in result.answer.citations],
            confidence=result.answer.confidence,
            llm_model=result.answer.llm_model,
            llm_provider=result.answer.llm_provider,
            llm_elapsed_ms=result.answer.elapsed_ms,
        ),
        chunks=chunks,
        elapsed_ms=result.elapsed_ms,
    )
