"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base for LLM providers."""

    provider_name: str

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Send prompt, return complete response text."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        """Send prompt, yield response text chunks."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of model this provider uses."""
        ...