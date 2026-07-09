"""Sentence-based chunker — splits text by sentence boundaries.

Uses regex-based sentence splitting. Each sentence becomes a chunk.
"""

from __future__ import annotations

import re

from knowledge_base.chunking.base import BaseChunker
from knowledge_base.models import Chunk

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


class SentenceChunker(BaseChunker):
    name = "sentence"

    def __init__(self, min_chunk_length: int = 20):
        self._min = min_chunk_length

    def chunk(self, document_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
        sentences = _SENTENCE_SPLIT.split(text.strip())
        chunks: list[Chunk] = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < self._min:
                continue
            words = sent.split()
            chunks.append(
                Chunk(
                    id=f"{document_id}_chunk_{len(chunks):04d}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    text=sent,
                    word_count=len(words),
                    token_count=len(words),
                )
            )
        return chunks