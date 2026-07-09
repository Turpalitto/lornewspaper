"""OpenAI embedding provider."""

from __future__ import annotations

from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.exceptions import EmbeddingError


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "openai"

    def __init__(self, api_key: str = "", model: str = "text-embedding-3-small", base_url: str = "https://api.openai.com/v1"):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = None

    async def _ensure_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=self._api_key or "sk-placeholder",
                base_url=self._base_url,
            )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        await self._ensure_client()
        try:
            resp = await self._client.embeddings.create(
                model=self._model, input=texts
            )
            return [d.embedding for d in resp.data]
        except Exception as exc:
            raise EmbeddingError(f"OpenAI embedding failed: {exc}") from exc

    @property
    def dimensions(self) -> int:
        dims = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}
        return dims.get(self._model, 1536)

    @property
    def model_name(self) -> str:
        return self._model