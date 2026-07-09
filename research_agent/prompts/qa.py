"""QA prompt templates."""

from __future__ import annotations

QA_SYSTEM_PROMPT = """You are a research assistant analyzing academic literature.
Answer the user's question based ONLY on the provided context chunks.
If the context does not contain enough information, say so clearly.
Always cite sources using [doc_id] notation."""


def build_qa_prompt(question: str, context_chunks: list[dict]) -> str:
    """Build QA prompt from question and context chunks."""
    lines = ["Answer the following question based on these research papers:\n"]
    for _, chunk in enumerate(context_chunks):
        doc_id = chunk.get("document_id", "?")
        text = chunk.get("text", "")
        lines.append(f"[{doc_id}] {text}\n")
    lines.append(f"\nQuestion: {question}\n")
    lines.append("Provide a detailed answer with citations.")
    return "\n".join(lines)