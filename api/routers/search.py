from __future__ import annotations

from fastapi import APIRouter, Depends
from structlog import get_logger

from api.dependencies import get_agent
from api.schemas.search import ArticleResponse, SearchRequest, SearchResponse
from research_agent.agent import ResearchAgent

router = APIRouter(prefix="/search", tags=["search"])
_LOG = get_logger("api")


@router.post(
    "",
    response_model=SearchResponse,
    operation_id="search_articles",
    summary="Search academic literature",
    description="Search across configured academic literature databases.",
)
async def search_articles(
    body: SearchRequest,
    agent: ResearchAgent = Depends(get_agent),
):
    result = await agent.search(query=body.query, max_results=body.max_results)
    articles = [
        ArticleResponse(
            id=a.get("id", ""),
            title=a.get("title", ""),
            doi=a.get("doi", ""),
            pmid=a.get("pmid", ""),
            pmcid=a.get("pmcid", ""),
            authors=a.get("authors", []),
            year=a.get("year"),
            journal=a.get("journal", ""),
            abstract=a.get("abstract", ""),
        )
        for a in result.articles
    ]
    return SearchResponse(
        articles=articles,
        total=len(articles),
        elapsed_ms=result.elapsed_ms,
    )
