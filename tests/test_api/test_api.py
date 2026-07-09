from unittest.mock import AsyncMock, MagicMock

import pytest

from research_agent.exceptions import AgentBusyError, DocumentNotFoundError
from research_agent.models import AgentResult, AgentStatus, Answer


def make_result(status=AgentStatus.COMPLETED, articles=None, documents=None, answer=None, error="", elapsed_ms=10.0):
    result = AgentResult(status=status, error=error, elapsed_ms=elapsed_ms)
    if articles:
        result.articles = articles
    if documents:
        result.documents = documents
    if answer:
        result.answer = answer
    return result


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
    from api.dependencies import get_agent
    application = create_app()
    application.dependency_overrides[get_agent] = lambda: mock_agent
    return application


@pytest.fixture
async def client(app):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    async def test_health(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "uptime_seconds" in body
        assert "version" in body

    async def test_liveness(self, client):
        resp = await client.get("/api/v1/liveness")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "alive"

    async def test_readiness(self, client, mock_agent):
        mock_agent._kb = MagicMock()
        mock_agent._cache = MagicMock()
        resp = await client.get("/api/v1/readiness")
        assert resp.status_code == 200
        body = resp.json()
        assert "agent_ready" in body
        assert "knowledge_base_ready" in body
        assert "cache_ready" in body


class TestSearch:
    async def test_search_returns_articles(self, client, mock_agent):
        mock_agent.search.return_value = make_result(articles=[
            {"id": "pmc:123", "title": "Test Paper", "doi": "10.1234/test",
             "authors": ["Alice"], "year": 2024, "journal": "Test Journal",
             "abstract": "Test abstract."},
        ])
        resp = await client.post("/api/v1/search", json={"query": "test", "max_results": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["articles"]) == 1
        assert body["articles"][0]["title"] == "Test Paper"
        assert body["total"] == 1

    async def test_search_empty_query(self, client):
        resp = await client.post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 422

    async def test_search_validation_max_results(self, client):
        resp = await client.post("/api/v1/search", json={"query": "test", "max_results": 0})
        assert resp.status_code == 422

    async def test_agent_busy_returns_409(self, client, mock_agent):
        mock_agent.search.side_effect = AgentBusyError("Agent is busy")
        resp = await client.post("/api/v1/search", json={"query": "test"})
        assert resp.status_code == 409
        body = resp.json()
        assert body["code"] == "AGENT_BUSY"

    async def test_agent_unexpected_error_returns_500(self, client, mock_agent):
        mock_agent.search.side_effect = RuntimeError("connection failed")
        resp = await client.post("/api/v1/search", json={"query": "test"})
        assert resp.status_code == 500

    async def test_search_max_results_capped(self, client):
        resp = await client.post("/api/v1/search", json={"query": "test", "max_results": 200})
        assert resp.status_code == 422


class TestIngest:
    async def test_ingest_returns_documents(self, client, mock_agent):
        doc = MagicMock()
        doc.document_id = "doc1"
        doc.status = "completed"
        doc.chunks = [MagicMock(), MagicMock()]
        mock_agent.ingest.return_value = make_result(documents=[doc])

        resp = await client.post("/api/v1/ingest", json={"query": "test", "max_results": 3})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["documents"]) == 1
        assert body["documents"][0]["document_id"] == "doc1"
        assert body["documents"][0]["chunks"] == 2

    async def test_download_returns_articles(self, client, mock_agent):
        mock_agent.search_and_download.return_value = make_result(articles=[
            {"id": "art1", "title": "Art 1"},
        ])
        resp = await client.post("/api/v1/ingest/download", json={"query": "test"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["articles"]) == 1

    async def test_ingest_empty_query(self, client):
        resp = await client.post("/api/v1/ingest", json={"query": ""})
        assert resp.status_code == 422

    async def test_ingest_validation(self, client):
        resp = await client.post("/api/v1/ingest", json={"query": "test", "max_results": 0})
        assert resp.status_code == 422


class TestAsk:
    async def test_ask_returns_answer(self, client, mock_agent):
        answer = Answer(answer="The answer is 42.", sources=["doc1"], confidence=0.95)
        mock_agent.ask.return_value = make_result(answer=answer)

        resp = await client.post("/api/v1/ask", json={"question": "what is the answer?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"]["answer"] == "The answer is 42."
        assert body["answer"]["confidence"] == 0.95
        assert body["answer"]["sources"] == ["doc1"]

    async def test_ask_empty_question(self, client):
        resp = await client.post("/api/v1/ask", json={"question": ""})
        assert resp.status_code == 422

    async def test_ask_with_provider_override(self, client, mock_agent):
        answer = Answer(answer="From Ollama", llm_provider="ollama", llm_model="llama3")
        mock_agent.ask.return_value = make_result(answer=answer)
        resp = await client.post("/api/v1/ask", json={
            "question": "test", "llm_provider": "ollama", "temperature": 0.5
        })
        assert resp.status_code == 200
        assert resp.json()["answer"]["llm_provider"] == "ollama"

    async def test_ask_temperature_validation(self, client):
        resp = await client.post("/api/v1/ask", json={"question": "test", "temperature": 3.0})
        assert resp.status_code == 422


class TestDocuments:
    async def test_list_documents(self, client, mock_agent):
        doc = MagicMock()
        doc.document_id = "doc1"
        doc.metadata = {"title": "Test Paper", "authors": ["Alice"], "source": "PubMed"}
        doc.chunks = [MagicMock()]
        doc.created_at = "2024-01-01T00:00:00"
        mock_agent.search_documents.return_value = make_result(documents=[doc])

        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["document_id"] == "doc1"
        assert body["items"][0]["metadata"]["title"] == "Test Paper"

    async def test_list_documents_empty(self, client, mock_agent):
        mock_agent.search_documents.return_value = make_result(documents=[])
        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    async def test_list_documents_pagination(self, client, mock_agent):
        docs = []
        for i in range(25):
            doc = MagicMock()
            doc.document_id = f"doc{i}"
            doc.metadata = {"title": f"Paper {i}", "authors": [], "source": ""}
            doc.chunks = []
            doc.created_at = ""
            docs.append(doc)
        mock_agent.search_documents.return_value = make_result(documents=docs)

        resp = await client.get("/api/v1/documents", params={"limit": 10})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 10
        assert body["has_more"] is True
        assert body["next_cursor"] is not None

    async def test_list_documents_respects_limit(self, client, mock_agent):
        doc = MagicMock()
        doc.document_id = "doc1"
        doc.metadata = {"title": "Test", "authors": [], "source": ""}
        doc.chunks = []
        doc.created_at = ""
        mock_agent.search_documents.return_value = make_result(documents=[doc])

        resp = await client.get("/api/v1/documents", params={"limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    async def test_get_document_found(self, client, mock_agent):
        doc = MagicMock()
        doc.document_id = "doc1"
        doc.metadata = {"title": "Test", "authors": []}
        doc.chunks = []
        doc.created_at = ""
        mock_agent._load_doc.return_value = doc

        resp = await client.get("/api/v1/documents/doc1")
        assert resp.status_code == 200
        assert resp.json()["document_id"] == "doc1"

    async def test_get_document_not_found(self, client, mock_agent):
        mock_agent._load_doc.return_value = None
        resp = await client.get("/api/v1/documents/nonexistent")
        assert resp.status_code == 404

    async def test_get_chunks(self, client, mock_agent):
        kb = AsyncMock()
        chunk = MagicMock()
        chunk.id = "c1"
        chunk.text = "Chunk text"
        chunk.heading = "Introduction"
        chunk.chunk_index = 0
        kb.get_chunks = AsyncMock(return_value=[chunk])
        mock_agent._ensure_kb.return_value = kb

        resp = await client.get("/api/v1/documents/doc1/chunks")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["chunk_id"] == "c1"

    async def test_get_chunks_with_cursor(self, client, mock_agent):
        kb = AsyncMock()
        chunk = MagicMock()
        chunk.id = "c2"
        chunk.text = "Second chunk"
        chunk.heading = ""
        chunk.chunk_index = 1
        kb.get_chunks = AsyncMock(return_value=[MagicMock(id="c1"), chunk])
        mock_agent._ensure_kb.return_value = kb

        resp = await client.get("/api/v1/documents/doc1/chunks", params={"cursor": "c1"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["chunk_id"] == "c2"

    async def test_summary(self, client, mock_agent):
        answer = Answer(answer="Summary of paper.")
        mock_agent.summarize.return_value = make_result(answer=answer)

        resp = await client.get("/api/v1/documents/doc1/summary")
        assert resp.status_code == 200
        assert resp.json()["summary"] == "Summary of paper."

    async def test_similar(self, client, mock_agent):
        answer = Answer(answer="These papers are related.", sources=["doc2", "doc3"])
        mock_agent.similar.return_value = make_result(answer=answer)

        resp = await client.get("/api/v1/documents/doc1/similar")
        assert resp.status_code == 200
        assert resp.json()["analysis"] == "These papers are related."
        assert len(resp.json()["related_documents"]) == 2


class TestCommon:
    async def test_request_id_in_response(self, client):
        resp = await client.get("/api/v1/health")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

    async def test_cors_headers(self, client):
        resp = await client.options(
            "/api/v1/health",
            headers={"Origin": "http://example.com", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" in resp.headers

    async def test_404_returns_error_response(self, client):
        resp = await client.get("/api/v1/nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "request_id" in body

    async def test_openapi_spec(self, client):
        resp = await client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["info"]["title"] == "Research Agent API"
        paths = spec["paths"]
        assert "/api/v1/health" in paths
        assert "/api/v1/liveness" in paths
        assert "/api/v1/readiness" in paths
        assert "/api/v1/search" in str(paths)
        assert "/api/v1/ask" in str(paths)
        assert "/api/v1/ingest" in str(paths)
        assert "/api/v1/documents" in str(paths)

    async def test_error_response_format(self, client):
        resp = await client.post("/api/v1/search", json={"query": ""})
        assert resp.status_code == 422
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "details" in body
        assert "request_id" in body
        assert "timestamp" in body

    async def test_document_not_found_returns_404_error_response(self, client, mock_agent):
        mock_agent.summarize.side_effect = DocumentNotFoundError("not found")
        resp = await client.get("/api/v1/documents/bad/summary")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "DOCUMENT_NOT_FOUND"
