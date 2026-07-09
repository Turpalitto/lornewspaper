"""Markdown generator.

Produces structured Markdown from a ProcessedDocument's sections, tables,
figures, and references.
"""

from __future__ import annotations

from document_processing_service.models import (
    ProcessedDocument,
)


def generate_markdown(doc: ProcessedDocument) -> str:
    parts: list[str] = []

    # Title
    if doc.metadata.title:
        parts.append(f"# {doc.metadata.title}\n")

    # Authors
    if doc.metadata.authors:
        parts.append(f"**Authors:** {', '.join(doc.metadata.authors)}\n")

    # Abstract
    if doc.metadata.abstract:
        parts.append("## Abstract\n")
        parts.append(doc.metadata.abstract.strip() + "\n")

    # Sections
    for section in doc.sections:
        prefix = "#" * min(section.level + 1, 6)
        parts.append(f"{prefix} {section.heading}\n")
        parts.append(section.content.strip() + "\n")

    # Tables
    if doc.tables:
        parts.append("## Tables\n")
        for table in doc.tables:
            if table.markdown:
                parts.append(table.markdown + "\n")

    # Figures
    if doc.figures:
        parts.append("## Figures\n")
        for fig in doc.figures:
            caption = fig.caption or "(untitled)"
            parts.append(f"![{caption}](figure_{fig.page_number}_{fig.image_index}.png)")
            if fig.caption:
                parts.append(f"\n\n*{fig.caption}*")
            parts.append("\n")

    # References
    if doc.references:
        parts.append("## References\n")
        for i, ref in enumerate(doc.references, 1):
            idx = ref.index or str(i)
            parts.append(f"[{idx}] {ref.raw_text}\n")

    return "\n".join(parts)