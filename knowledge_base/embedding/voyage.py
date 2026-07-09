"""Voyage AI embedding provider."""

from __future__ import annotations

import httpx

from knowledge_base.embedding.base import BaseEmbeddingProvider
from knowledge_base.exceptions import EmbeddingError


class VoyageEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "voyage"

    def __init__(self, api_key: str = "", model: str = "voyage-2", base_url: str = "https://api.voyageai.com/v1"):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": texts}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                return [d["embedding"] for d in data["data"]]
        except Exception as exc:
            raise EmbeddingError(f"Voyage embedding failed: {exc}") from exc

    @property
    def dimensions(self) -> int:
        return 1024

    @property
    def model_name(self) -> str:
        return self._model