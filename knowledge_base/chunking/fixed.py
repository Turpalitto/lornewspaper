"""Fixed-size chunker — splits text into configurable token windows.

Uses word-count approximation (each word ≈ 1.3 tokens). Chunks can overlap.
"""

from __future__ import annotations

from knowledge_base.chunking.base import BaseChunker
from knowledge_base.models import Chunk


class FixedChunker(BaseChunker):
    name = "fixed"

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64, min_chunk_length: int = 20):
        self._size = chunk_size
        self._overlap = chunk_overlap
        self._min = min_chunk_length
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if min_chunk_length > chunk_size:
            raise ValueError("min_chunk_length cannot exceed chunk_size")

    def chunk(self, document_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
        words = text.split()
        step = self._size - self._overlap
        chunks: list[Chunk] = []

        for start in range(0, max(len(words), 1), step):
            end = start + self._size
            segment = words[start:end]
            chunk_text = " ".join(segment).strip()
            if len(chunk_text) < self._min:
                continue
            idx = len(chunks)
            prev_id = f"{document_id}_chunk_{idx - 1:04d}" if idx > 0 else ""
            next_id = f"{document_id}_chunk_{idx + 1:04d}" if end < len(words) else ""
            chunks.append(
                Chunk(
                    id=f"{document_id}_chunk_{idx:04d}",
                    document_id=document_id,
                    chunk_index=idx,
                    text=chunk_text,
                    word_count=len(segment),
                    token_count=int(len(segment) * 1.3),
                    previous_chunk=prev_id,
                    next_chunk=next_id,
                )
            )
        return chunks