"""Section-based chunker — splits using document section boundaries.

Each section from the ProcessedDocument's sections list becomes a chunk.
"""

from __future__ import annotations

from knowledge_base.chunking.base import BaseChunker
from knowledge_base.models import Chunk


class SectionChunker(BaseChunker):
    name = "section"

    def __init__(self, min_chunk_length: int = 20):
        self._min = min_chunk_length

    def chunk(self, document_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
        meta = metadata or {}
        sections = meta.get("sections", [])
        if not sections:
            return [self._make_chunk(document_id, 0, "Body", "Body", text)]

        chunks: list[Chunk] = []
        for i, sec in enumerate(sections):
            heading = sec.get("heading", "")
            content = sec.get("content", "")
            if len(content.strip()) < self._min:
                continue
            chunks.append(
                self._make_chunk(document_id, len(chunks), heading, heading, content)
            )
        return chunks or [self._make_chunk(document_id, 0, "", "Body", text)]

    def _make_chunk(
        self, doc_id: str, idx: int, heading: str, section: str, text: str
    ) -> Chunk:
        words = text.split()
        chunk = Chunk(
            id=f"{doc_id}_chunk_{idx:04d}",
            document_id=doc_id,
            chunk_index=idx,
            heading=heading,
            section=section,
            text=text.strip(),
            word_count=len(words),
            token_count=len(words),
        )
        return chunk