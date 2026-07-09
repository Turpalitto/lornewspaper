"""Chunking strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from knowledge_base.models import Chunk


class BaseChunker(ABC):
    name: str

    @abstractmethod
    def chunk(self, document_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
        ...