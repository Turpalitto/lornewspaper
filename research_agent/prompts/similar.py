"""Similarity analysis prompt templates."""

from __future__ import annotations

SIMILAR_SYSTEM_PROMPT = """You are a research assistant comparing academic papers.
Analyze how these documents relate to each other.
Focus on shared topics, methodology similarities, and complementary findings."""


def build_similar_prompt(source_text: str, candidate_chunks: list[dict]) -> str:
    """Build similarity analysis prompt from source and candidates."""
    lines = [f"Source document:\n{source_text}\n", "Compare with these related documents:\n"]
    for chunk in candidate_chunks:
        lines.append(f"- {chunk.get('text', '')[:500]}")
    lines.append("\nExplain how they are similar or different.")
    return "\n".join(lines)