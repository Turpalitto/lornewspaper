"""Ollama LLM provider."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from research_agent.providers.base import BaseLLMProvider

_LOG = structlog.get_logger("research_agent")

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 120.0


class OllamaProvider(BaseLLMProvider):
    provider_name = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        api_key: str = "",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout, base_url=self._base_url)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }
        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                import json as json_mod
                try:
                    data = json_mod.loads(line)
                except json_mod.JSONDecodeError:
                    continue
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content

    @property
    def model_name(self) -> str:
        return self._model

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()