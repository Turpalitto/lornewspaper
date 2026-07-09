"""Tests for ResearchAgent — orchestrator, cache, providers, workflow, CLI."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings, default_settings
from research_agent.exceptions import (
    AgentBusyError,
    DocumentNotFoundError,
    UnknownProviderError,
)
from research_agent.models import AgentRequest, AgentResult, AgentStatus, Answer, Citation


class TestModels:
    def test_agent_request_defaults(self):
        req = AgentRequest(query="test")
        assert req.query == "test"
        assert req.max_results == 10
        assert req.temperature == 0.3
        assert req.created_at is not None

    def test_agent_result_defaults(self):
        result = AgentResult()
        assert result.status == AgentStatus.IDLE
        assert result.documents == []
        assert result.articles == []
        assert result.error == ""

    def test_answer_defaults(self):
        a = Answer()
        assert a.answer == ""
        assert a.citations == []
        assert a.confidence == 0.0

    def test_citation_fields(self):
        c = Citation(document_id="doc1", title="Test Paper")
        assert c.document_id == "doc1"
        assert c.authors == []


class TestResponseCache:
    def test_set_and_get(self):
        c = ResponseCache(ttl_seconds=3600, max_size=10)
        c.set("key1", {"answer": "hello"})
        assert c.get("key1") == {"answer": "hello"}

    def test_miss_returns_none(self):
        c = ResponseCache()
        assert c.get("nonexistent") is None

    def test_expiry(self):
        c = ResponseCache(ttl_seconds=0)
        c.set("key", "value")
        import time
        time.sleep(0.02)
        assert c.get("key") is None

    def test_max_size_evicts_oldest(self):
        c = ResponseCache(ttl_seconds=3600, max_size=3)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        c.set("d", 4)
        assert c.get("a") is None
        assert c.get("b") is not None

    def test_invalidate(self):
        c = ResponseCache()
        c.set("key1", "val")
        c.invalidate("key1")
        assert c.get("key1") is None

    def test_clear(self):
        c = ResponseCache()
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is None
        assert c.get("b") is None


class TestConfig:
    def test_default_settings(self):
        s = default_settings()
        assert s.llm.provider == "openai"
        assert s.llm.model == "gpt-4o"
        assert s.cache.ttl_seconds == 3600
        assert s.workflow.search_max_results == 10

    def test_custom_settings(self):
        s = Settings()
        s.llm.provider = "ollama"
        s.llm.model = "llama3"
        s.cache.enabled = False
        assert s.llm.provider == "ollama"
        assert s.cache.enabled is False

    def test_cache_config_dataclass(self):
        from research_agent.config import CacheConfig
        c = CacheConfig()
        assert c.max_size == 512


class TestExceptions:
    def test_base_exception(self):
        from research_agent.exceptions import ResearchAgentError
        with pytest.raises(ResearchAgentError):
            raise ResearchAgentError("base error")

    def test_unknown_provider(self):
        with pytest.raises(UnknownProviderError):
            raise UnknownProviderError("unknown")

    def test_document_not_found(self):
        with pytest.raises(DocumentNotFoundError):
            raise DocumentNotFoundError("missing")

    def test_exception_hierarchy(self):
        from research_agent.exceptions import (
            AgentBusyError,
            CacheError,
            ConfigurationError,
            LLMProviderError,
            WorkflowError,
        )
        assert issubclass(AgentBusyError, RuntimeError)
        assert issubclass(LLMProviderError, RuntimeError)
        assert issubclass(ConfigurationError, ValueError)
        assert issubclass(CacheError, RuntimeError)
        assert issubclass(WorkflowError, RuntimeError)


class TestProviderRegistry:
    def test_discover_providers(self):
        from research_agent.providers.registry import discover_providers, list_providers
        discover_providers()
        providers = list_providers()
        # At minimum ollama should be registered (no deps)
        assert len(providers) >= 1

    def test_get_provider_unknown_raises(self):
        from research_agent.providers.registry import discover_providers, get_llm_provider
        discover_providers()
        with pytest.raises(UnknownProviderError):
            get_llm_provider(provider="nonexistent")

    def test_get_provider_missing_api_key(self):
        from research_agent.providers.registry import discover_providers, get_llm_provider
        from research_agent.exceptions import ConfigurationError
        discover_providers()
        with pytest.raises((ConfigurationError, UnknownProviderError)):
            get_llm_provider(provider="openai", api_key="", model="gpt-4o")

    def test_ollama_no_api_key_required(self):
        from research_agent.providers.registry import discover_providers, get_llm_provider
        discover_providers()
        provider = get_llm_provider(provider="ollama", api_key="", model="llama3")
        assert provider is not None
        assert provider.model_name == "llama3"

    @pytest.mark.asyncio
    async def test_base_provider_interface(self):
        from research_agent.providers.base import BaseLLMProvider

        class MockProvider(BaseLLMProvider):
            provider_name = "mock"

            async def generate(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1024):
                return "mock response"

            async def generate_stream(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1024):
                yield "mock chunk"

            @property
            def model_name(self):
                return "mock-model"

        p = MockProvider()
        assert p.provider_name == "mock"
        assert p.model_name == "mock-model"
        result = await p.generate("sys", "user")
        assert result == "mock response"


class TestResearchAgent:
    @pytest.fixture
    def agent(self):
        return ResearchAgent(settings=Settings())

    @pytest.mark.asyncio
    async def test_search_returns_articles(self, agent):
        with patch("research_agent.agent.search_articles", new=AsyncMock(return_value=[{
            "id": "test:123",
            "title": "Test Article",
            "doi": "10.1234/test",
        }])):
            result = await agent.search("test query")
            assert result.status == AgentStatus.COMPLETED
            assert len(result.articles) == 1
            assert result.articles[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_search_no_results(self, agent):
        with patch("research_agent.agent.search_articles", new=AsyncMock(return_value=[])):
            result = await agent.search("nothing")
            assert result.status == AgentStatus.COMPLETED
            assert len(result.articles) == 0

    @pytest.mark.asyncio
    async def test_ask_no_context_returns_empty(self, agent):
        with patch.object(agent, "_ensure_kb", new=AsyncMock()) as mock_kb:
            kb = AsyncMock()
            kb.search_text = AsyncMock(return_value=type("SR", (), {"items": []})())
            mock_kb.return_value = kb
            result = await agent.ask("question?")
            assert result.status == AgentStatus.COMPLETED
            assert "No relevant documents found" in result.answer.answer

    @pytest.mark.asyncio
    async def test_ask_with_context(self, agent):
        from knowledge_base.models import Chunk

        chunk = Chunk(
            id="c1",
            document_id="doc1",
            text="Relevant content here.",
            chunk_index=0,
        )

        kb = AsyncMock()
        kb.search_text = AsyncMock(return_value=MagicMock(items=[
            MagicMock(chunk=chunk, score=0.95)
        ]))
        kb.get_document = AsyncMock(return_value=MagicMock())
        kb.list_documents = AsyncMock(return_value=[])

        with (
            patch.object(agent, "_ensure_kb", new=AsyncMock(return_value=kb)),
            patch("research_agent.agent.get_llm_provider") as mock_get,
        ):
            mock_provider = AsyncMock()
            mock_provider.generate = AsyncMock(return_value="Answer with citation [doc1]")
            mock_provider.model_name = "mock-model"
            mock_get.return_value = mock_provider

            result = await agent.ask("test question")
            assert result.status == AgentStatus.COMPLETED
            assert "Answer" in result.answer.answer
            assert result.answer.llm_model == "mock-model"

    @pytest.mark.asyncio
    async def test_summarize_missing_document(self, agent):
        kb = AsyncMock()
        kb.get_chunks = AsyncMock(return_value=[])

        with patch.object(agent, "_ensure_kb", new=AsyncMock(return_value=kb)):
            result = await agent.summarize("nonexistent")
            assert result.status == AgentStatus.FAILED
            assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_similar_missing_document(self, agent):
        kb = AsyncMock()
        kb.get_chunks = AsyncMock(return_value=[])

        with patch.object(agent, "_ensure_kb", new=AsyncMock(return_value=kb)):
            result = await agent.similar("nonexistent")
            assert result.status == AgentStatus.FAILED
            assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_agent_busy_raises(self, agent):
        agent._status = AgentStatus.RUNNING
        with pytest.raises(AgentBusyError):
            await agent.search("test")

    @pytest.mark.asyncio
    async def test_elapsed_ms_set(self, agent):
        with patch("research_agent.agent.search_articles", new=AsyncMock(return_value=[])):
            result = await agent.search("fast")
            assert result.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        s = Settings()
        async with ResearchAgent(settings=s) as agent:
            assert agent.status == AgentStatus.IDLE
            result = await agent.search("test ctx")
            assert result is not None
            assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_close(self):
        agent = ResearchAgent(settings=Settings())
        kb = AsyncMock()
        agent._kb = kb
        await agent.close()
        kb.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_chunks(self, agent):
        kb = AsyncMock()
        kb.search_text = AsyncMock(return_value=MagicMock(items=[], total_found=0, query=""))

        with patch.object(agent, "_ensure_kb", new=AsyncMock(return_value=kb)):
            result = await agent.search_chunks("test")
            assert result.status == AgentStatus.COMPLETED
            assert result.search_result is not None

    @pytest.mark.asyncio
    async def test_search_documents(self, agent):
        kb = AsyncMock()
        kb.list_documents = AsyncMock(return_value=[
            MagicMock(document_id="doc1", metadata={"title": "Alpha Paper"}),
            MagicMock(document_id="doc2", metadata={"title": "Beta Paper"}),
        ])

        with patch.object(agent, "_ensure_kb", new=AsyncMock(return_value=kb)):
            result = await agent.search_documents("alpha")
            assert result.status == AgentStatus.COMPLETED
            assert len(result.documents) == 1
            assert result.documents[0].document_id == "doc1"

    @pytest.mark.asyncio
    async def test_ingest(self, agent):
        with (
            patch("research_agent.agent.full_ingest_pipeline") as mock_pipe,
            patch.object(agent, "_load_doc", new=AsyncMock(return_value=MagicMock(document_id="ingested_doc"))),
        ):
            mock_pipe.return_value = [{"document_id": "ingested_doc"}]
            result = await agent.ingest("test query")
            assert result.status == AgentStatus.COMPLETED
            assert len(result.documents) == 1

    @pytest.mark.asyncio
    async def test_search_and_download(self, agent):
        mock_articles = [{"id": "art1", "title": "Art 1", "doi": "10.1"}]
        with (
            patch("research_agent.agent.search_articles", new=AsyncMock(return_value=mock_articles)),
            patch("research_agent.agent.download_article", new=AsyncMock(return_value="/tmp/test.pdf")),
        ):
            result = await agent.search_and_download("test query")
            assert result.status == AgentStatus.COMPLETED
            assert len(result.articles) == 1

    def test_status_property(self, agent):
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_cache_hit(self, agent):
        cached_answer = Answer(answer="cached response", sources=["doc1"])
        agent._cache.set("qa:test", cached_answer)

        with patch.object(agent, "_ensure_kb") as mock_kb:
            result = await agent.ask("test")
            assert result.status == AgentStatus.COMPLETED
            assert result.answer.answer == "cached response"
            mock_kb.assert_not_called()


class TestProviders:
    def test_openai_provider_instantiation(self):
        pytest.importorskip("openai")
        from research_agent.providers.openai import OpenAIProvider
        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        assert p.model_name == "gpt-4o"
        assert p.provider_name == "openai"

    def test_anthropic_provider_instantiation(self):
        pytest.importorskip("anthropic")
        from research_agent.providers.anthropic import AnthropicProvider
        p = AnthropicProvider(api_key="sk-ant-test", model="claude-3-opus-20240229")
        assert p.model_name == "claude-3-opus-20240229"
        assert p.provider_name == "anthropic"

    def test_gemini_provider_instantiation(self):
        pytest.importorskip("google.genai")
        from research_agent.providers.gemini import GeminiProvider
        p = GeminiProvider(api_key="gemini-test", model="gemini-1.5-pro")
        assert p.model_name == "gemini-1.5-pro"
        assert p.provider_name == "gemini"

    def test_ollama_provider_instantiation(self):
        from research_agent.providers.ollama import OllamaProvider
        p = OllamaProvider(api_key="", model="llama3", base_url="http://localhost:11434")
        assert p.model_name == "llama3"
        assert p.provider_name == "ollama"

    @pytest.mark.asyncio
    async def test_ollama_connect_fails_without_server(self):
        from research_agent.providers.ollama import OllamaProvider
        p = OllamaProvider(api_key="", model="llama3", base_url="http://localhost:1")
        with pytest.raises(Exception):
            await p.generate("sys", "user")

    @pytest.mark.asyncio
    async def test_openai_connect_fails_without_server(self):
        pytest.importorskip("openai")
        from research_agent.providers.openai import OpenAIProvider
        p = OpenAIProvider(api_key="sk-test-bad", model="gpt-4o", base_url="http://localhost:1/v1")
        with pytest.raises(Exception):
            await p.generate("sys", "user")


class TestCLI:
    def test_cli_imports(self):
        import research_agent.cli
        assert hasattr(research_agent.cli, "main")

    def test_cli_search_no_args(self):
        import sys
        from research_agent.cli import main
        test_args = ["research"]
        with pytest.raises(SystemExit):
            with patch.object(sys, "argv", test_args):
                main()

    def test_cli_search_help(self):
        import sys
        from research_agent.cli import main
        test_args = ["research", "search", "--help"]
        with pytest.raises(SystemExit):
            with patch.object(sys, "argv", test_args):
                main()


class TestWorkflow:
    @pytest.mark.asyncio
    async def test_search_articles_fails_gracefully(self):
        from research_agent.workflow import search_articles
        with patch(
            "search_service.service.SearchService"
        ) as MockSvc:
            MockSvc.return_value.search_all = AsyncMock(
                side_effect=Exception("network error")
            )
            with pytest.raises(Exception, match="Search failed"):
                await search_articles("test")

    @pytest.mark.asyncio
    async def test_download_article_fails_returns_none(self):
        from research_agent.workflow import download_article
        article = {"id": "test", "doi": "10.1234/test", "title": "Test"}
        with patch("download_service.service.DownloadService") as MockDl:
            mock_instance = MockDl.return_value
            mock_instance.download = AsyncMock(
                return_value=MagicMock(
                    status=MagicMock(value="failed"), file_path=None
                )
            )
            result = await download_article(article)
            assert result is None

    def test_dict_to_article(self):
        from research_agent.workflow import _dict_to_article
        article = {
            "id": "test",
            "title": "Test",
            "doi": "10.123",
            "authors": ["Alice", "Bob"],
        }
        result = _dict_to_article(article)
        assert result is not None
        assert result.title == "Test"
        assert result.doi == "10.123"

    def test_make_download_result(self):
        from research_agent.workflow import _make_download_result
        article = {"id": "test_article"}
        result = _make_download_result(article, "/tmp/test.pdf")
        assert result.article_id == "test_article"
        assert result.file_path == "/tmp/test.pdf"


class TestPrompts:
    def test_qa_prompt(self):
        from research_agent.prompts.qa import build_qa_prompt
        chunks = [{"document_id": "doc1", "text": "Important finding."}]
        prompt = build_qa_prompt("What is the finding?", chunks)
        assert "[doc1]" in prompt
        assert "Important finding" in prompt
        assert "What is the finding?" in prompt

    def test_summary_prompt(self):
        from research_agent.prompts.summarize import build_summary_prompt
        chunks = [{"text": "We studied X."}, {"text": "Conclusion: Y."}]
        prompt = build_summary_prompt(chunks)
        assert "We studied X." in prompt
        assert "Conclusion: Y." in prompt

    def test_similar_prompt(self):
        from research_agent.prompts.similar import build_similar_prompt
        source = "Original paper text."
        candidates = [{"text": "Related paper text."}]
        prompt = build_similar_prompt(source, candidates)
        assert "Original paper text." in prompt
        assert "Related paper text." in prompt