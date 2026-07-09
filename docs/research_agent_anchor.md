# ResearchAgent — Architecture Anchor

## Purpose

Orchestration layer over SearchService → DownloadService → DocumentProcessingService → KnowledgeBaseService. Single high-level API for complete research workflows.

## Files

```
research_agent/
├── __init__.py          — Public exports: ResearchAgent, AgentRequest, AgentResult, Answer
├── agent.py             — ResearchAgent orchestrator (DI, 11 public methods, _run lifecycle)
├── workflow.py          — Pipeline functions: search→download→process→index
├── models.py            — Pydantic v2: AgentRequest, AgentResult, Answer, Citation, AgentStatus
├── config.py            — Dataclass Settings: LLMConfig, CacheConfig, WorkflowConfig
├── exceptions.py        — ResearchAgentError base + LLMProviderError, UnknownProviderError, etc.
├── cache.py             — TTL ResponseCache with LRU eviction (OrderedDict)
├── cli.py               — argparse CLI: research search/ingest/ask/summarize/similar
├── prompts/
│   ├── __init__.py      — empty
│   ├── qa.py            — QA prompt builder with [doc_id] citations
│   ├── summarize.py     — Structured summary prompt
│   └── similar.py       — Document comparison prompt
└── providers/
    ├── __init__.py      — empty
    ├── base.py          — BaseLLMProvider ABC
    ├── openai.py        — OpenAI provider (AsyncOpenAI)
    ├── anthropic.py     — Anthropic provider (AsyncAnthropic)
    ├── gemini.py        — Gemini provider (google.genai)
    ├── ollama.py        — Ollama provider (httpx SSE)
    └── registry.py      — Dict registry + discover_providers() (skips missing packages)
```

## Public API

| Method | Wires |
|--------|-------|
| `search(query)` | SearchService → articles |
| `search_and_download(query)` | SearchService → DownloadService |
| `ingest(query)` | SearchService → DownloadService → DPS → KBService |
| `ingest_article(article)` | DownloadService → DPS → KBService |
| `ingest_pdf(path)` | DPS → KBService |
| `ask(question)` | KB search → chunks → LLM → Answer |
| `summarize(document_id)` | KB chunks → LLM → summary |
| `similar(document_id)` | KB chunks → vector search → LLM → comparison |
| `search_chunks(query)` | KB hybrid search |
| `search_documents(query)` | KB list + filter |

## Patterns

- DI constructor: `ResearchAgent(settings=None, *, knowledge_base=None, cache=None)`
- Async context manager: `async with ResearchAgent() as agent:`
- structlog throughout
- Pydantic v2 models, dataclass config, empty sub-package `__init__.py`
- Provider registry with `discover_providers()` — skips missing packages gracefully

## Quality

- ruff: clean
- mypy: clean (research_agent/ only; pre-existing errors in KB)
- Tests: 50 passed, 4 skipped (missing openai/anthropic/google packages)
- Full suite: 214 passed, 7 skipped
