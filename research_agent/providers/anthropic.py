"""Anthropic LLM provider."""

from __future__ import annotations

import structlog
from anthropic import AsyncAnthropic

from research_agent.providers.base import BaseLLMProvider

_LOG = structlog.get_logger("research_agent")

DEFAULT_TIMEOUT = 60.0


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)
        self._model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        response = await self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        async with self._client.messages.stream(
            model=self._model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    @property
    def model_name(self) -> str:
        return self._model