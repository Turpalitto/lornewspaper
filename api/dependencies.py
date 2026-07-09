from __future__ import annotations

import asyncio
import os

import structlog

from research_agent.agent import ResearchAgent
from research_agent.cache import ResponseCache
from research_agent.config import Settings as AgentSettings

_LOG = structlog.get_logger("api")

_agent: ResearchAgent | None = None
_ready: bool = False

_KB_INIT_TIMEOUT = 30.0


def get_agent() -> ResearchAgent:
    if _agent is None:
        raise RuntimeError("ResearchAgent not initialized")
    return _agent


def is_ready() -> bool:
    return _ready


def set_ready(value: bool) -> None:
    global _ready
    _ready = value


async def init_agent() -> None:
    from research_agent.providers.registry import discover_providers

    global _agent
    discover_providers()

    settings = AgentSettings()
    if api_key := os.environ.get("LLM_API_KEY"):
        settings.llm.api_key = api_key
    if provider := os.environ.get("LLM_PROVIDER"):
        settings.llm.provider = provider
    if model := os.environ.get("LLM_MODEL"):
        settings.llm.model = model
    if base_url := os.environ.get("LLM_BASE_URL"):
        settings.llm.base_url = base_url

    cache = ResponseCache(
        ttl_seconds=settings.cache.ttl_seconds,
        max_size=settings.cache.max_size,
    )
    _agent = ResearchAgent(settings=settings, cache=cache)
    try:
        await asyncio.wait_for(_agent._ensure_kb(), timeout=_KB_INIT_TIMEOUT)
    except asyncio.TimeoutError:
        _LOG.error("kb_init_timeout", timeout=_KB_INIT_TIMEOUT)
        raise RuntimeError(f"KnowledgeBase initialization timed out after {_KB_INIT_TIMEOUT}s")
    _LOG.info("agent_initialized")


async def shutdown_agent() -> None:
    global _agent, _ready
    if _agent is not None:
        await _agent.close()
        _agent = None
    _ready = False
    _LOG.info("agent_shutdown")


async def health_check_deps() -> dict[str, bool]:
    results = {"agent": _agent is not None}
    if _agent is not None:
        kb = getattr(_agent, "_kb", None)
        results["knowledge_base"] = kb is not None
        results["cache"] = _agent._cache is not None
    else:
        results["knowledge_base"] = False
        results["cache"] = False
    return results
