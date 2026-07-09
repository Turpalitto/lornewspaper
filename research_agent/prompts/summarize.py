"""Summarization prompt templates."""

from __future__ import annotations

SUMMARIZE_SYSTEM_PROMPT = """You are a research assistant summarizing academic literature.
Provide a concise, structured summary covering:
1. Main objective
2. Key findings
3. Methodology
4. Conclusions
Use plain language suitable for researchers."""


def build_summary_prompt(chunks: list[dict]) -> str:
    """Build summarization prompt from document chunks."""
    lines = ["Summarize the following research document:\n"]
    for chunk in chunks:
        lines.append(chunk.get("text", ""))
        lines.append("")
    return "\n".join(lines)