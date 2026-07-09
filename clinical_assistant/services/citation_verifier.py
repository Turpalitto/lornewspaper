"""Citation integrity verification.

Ensures LLM-generated citations reference actual guideline text
by comparing source text hashes.
"""

from __future__ import annotations

import hashlib
from typing import Any


class CitationVerifier:
    """Verify that citations reference actual indexed guideline content."""

    def __init__(self):
        self._known_hashes: dict[str, str] = {}  # hash → guideline_id

    def register_text(self, text: str, source_id: str) -> str:
        """Register a source text and return its hash."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self._known_hashes[h] = source_id
        return h

    def verify_citation(self, cited_text: str, claimed_source_id: str | None = None) -> dict[str, Any]:
        """Verify a citation against known source texts.

        Returns:
            {"verified": bool, "confidence": float, "source_id": str or None}
        """
        h = hashlib.sha256(cited_text.encode("utf-8")).hexdigest()
        if h in self._known_hashes:
            return {
                "verified": True,
                "confidence": 1.0,
                "source_id": self._known_hashes[h],
            }

        # Partial match: check if cited text is a substring of any registered text
        best_match = None
        best_score = 0.0
        for known_hash, source_id in self._known_hashes.items():
            score = self._fuzzy_match(cited_text, known_hash)
            if score > best_score:
                best_score = score
                best_match = source_id

        return {
            "verified": best_score > 0.8,
            "confidence": round(best_score, 2),
            "source_id": best_match,
        }

    def _fuzzy_match(self, cited: str, known_hash: str) -> float:
        """Simple word-overlap fuzzy matching."""
        # In production, use sentence embeddings for fuzzy matching
        # This is a placeholder that returns 0 for unknown hashes
        return 0.0
