"""OpenAI LLM provider."""

from __future__ import annotations

from typing import Any

import structlog
from openai import AsyncOpenAI

from research_agent.providers.base import BaseLLMProvider

_LOG = structlog.get_logger("research_agent")

DEFAULT_TIMEOUT = 60.0


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    @property
    def model_name(self) -> str:
        return self._model