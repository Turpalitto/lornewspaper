"""Clinical guideline API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from clinical_assistant.dependencies import get_guideline_service
from clinical_assistant.models.guideline import GuidelineSource
from clinical_assistant.schemas.guidelines import (
    GuidelineListResponse,
    GuidelineResponse,
    SearchRequest,
    SearchResponse,
    AskRequest,
    AskResponse,
    IngestResponse,
)
from clinical_assistant.services.guideline_service import GuidelineService

router = APIRouter(prefix="/guidelines", tags=["guidelines"])


@router.post("/search", response_model=SearchResponse, operation_id="search_guidelines")
async def search_guidelines(
    body: SearchRequest,
    svc: GuidelineService = Depends(get_guideline_service),
):
    guidelines = await svc.search(body.query, top_k=body.top_k or 10)
    return SearchResponse(
        items=[GuidelineResponse.from_guideline(g) for g in guidelines],
        total=len(guidelines),
    )


@router.get("/{guideline_id}", response_model=GuidelineResponse, operation_id="get_guideline")
async def get_guideline(
    guideline_id: str,
    svc: GuidelineService = Depends(get_guideline_service),
):
    guideline = svc.get_guideline(guideline_id)
    if guideline is None:
        raise HTTPException(status_code=404, detail=f"Guideline '{guideline_id}' not found")
    return GuidelineResponse.from_guideline(guideline)


@router.get("", response_model=GuidelineListResponse, operation_id="list_guidelines")
async def list_guidelines(
    svc: GuidelineService = Depends(get_guideline_service),
):
    guidelines = svc.list_guidelines()
    return GuidelineListResponse(
        items=[GuidelineResponse.from_guideline(g) for g in guidelines],
        total=len(guidelines),
    )


@router.post("/ask", response_model=AskResponse, operation_id="ask_guideline")
async def ask_guideline(
    body: AskRequest,
    svc: GuidelineService = Depends(get_guideline_service),
):
    result = await svc.ask(body.question, guideline_ids=body.guideline_ids)
    return AskResponse(
        answer=result.get("answer", ""),
        recommendations=result.get("recommendations", []),
        sources=result.get("sources", []),
        confidence=result.get("confidence", 0.0),
    )


@router.post("/ingest", response_model=IngestResponse, operation_id="ingest_guideline")
async def ingest_guideline(
    file: UploadFile,
    source: str = "local",
    svc: GuidelineService = Depends(get_guideline_service),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    import tempfile
    from pathlib import Path

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        guideline = await svc.ingest_pdf(tmp_path, GuidelineSource(source))
        return IngestResponse(
            guideline_id=guideline.id,
            title=guideline.title_ru or guideline.title_en,
            sections=len(guideline.sections),
            recommendations=len(guideline.recommendations),
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
