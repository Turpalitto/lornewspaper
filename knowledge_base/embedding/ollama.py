"""Ollama embedding provider — local embeddings via Ollama API."""

from __future__ import annotations

import httpx

from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.exceptions import EmbeddingError


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dims = self._default_dims(model)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                for text in texts:
                    payload = {"model": self._model, "prompt": text}
                    resp = await client.post(
                        f"{self._base_url}/api/embeddings",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results.append(data["embedding"])
            return results
        except Exception as exc:
            raise EmbeddingError(f"Ollama embedding failed: {exc}") from exc

    @property
    def dimensions(self) -> int:
        return self._dims

    @property
    def model_name(self) -> str:
        return self._model

    @staticmethod
    def _default_dims(model: str) -> int:
        dims = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
            "snowflake-arctic-embed": 768,
        }
        return dims.get(model, 768)