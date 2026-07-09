import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import AsyncMock

import pytest

from api.dependencies import get_agent
from research_agent.models import AgentResult, AgentStatus


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.search = AsyncMock()
    agent.search_and_download = AsyncMock()
    agent.ingest = AsyncMock()
    agent.ask = AsyncMock()
    agent.summarize = AsyncMock()
    agent.similar = AsyncMock()
    agent.search_documents = AsyncMock()
    agent._load_doc = AsyncMock()
    agent._ensure_kb = AsyncMock()
    agent._cache = AsyncMock()
    return agent


@pytest.fixture
def app(mock_agent):
    from api.app import create_app
    application = create_app()
    application.dependency_overrides[get_agent] = lambda: mock_agent
    return application


@pytest.fixture
async def client(app):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_result(status=AgentStatus.COMPLETED, articles=None, documents=None, answer=None, error="", elapsed_ms=10.0):
    result = AgentResult(status=status, error=error, elapsed_ms=elapsed_ms)
    if articles:
        result.articles = articles
    if documents:
        result.documents = documents
    if answer:
        result.answer = answer
    return result
