"""Gemini LLM provider."""

from __future__ import annotations

import structlog
from google import genai
from google.genai import types

from research_agent.providers.base import BaseLLMProvider

_LOG = structlog.get_logger("research_agent")

DEFAULT_TIMEOUT = 60.0


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._timeout = timeout

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        ):
            if chunk.text:
                yield chunk.text

    @property
    def model_name(self) -> str:
        return self._model