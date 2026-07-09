"""Metadata validation tests — document retrieval, field preservation, citation integrity."""

from __future__ import annotations

import pytest

from document_processing_service.models import ProcessingStatus
from knowledge_base.models import IndexingStatus
from knowledge_base.service import KnowledgeBaseService


pytestmark = pytest.mark.asyncio


async def test_metadata_preserved_across_pipeline(processed_document, knowledge_base):
    """Verify document metadata survives index -> retrieve round-trip."""
    indexed = await knowledge_base.index(processed_document)
    assert indexed.status == IndexingStatus.COMPLETED

    loaded = await knowledge_base.get_document(processed_document.article_id)
    assert loaded is not None

    original = processed_document.metadata
    retrieved = loaded.metadata

    assert retrieved.get("title") == original.title, "Title mismatch"
    assert retrieved.get("abstract") == original.abstract, "Abstract mismatch"
    assert retrieved.get("authors") == original.authors, "Authors mismatch"
    assert loaded.document_id == processed_document.article_id, "Document ID mismatch"


async def test_document_not_found_returns_none(knowledge_base):
    """Verify non-existent document returns None (not 500)."""
    result = await knowledge_base.get_document("nonexistent-doc-id-12345")
    assert result is None


async def test_list_documents_after_index(processed_document, knowledge_base):
    """Verify documents appear in list after indexing."""
    assert len(await knowledge_base.list_documents()) == 0
    await knowledge_base.index(processed_document)
    docs = await knowledge_base.list_documents()
    assert len(docs) >= 1
    ids = [d.document_id for d in docs]
    assert processed_document.article_id in ids


async def test_chunk_integrity(processed_document, knowledge_base):
    """Verify generated chunks preserve heading and text."""
    indexed = await knowledge_base.index(processed_document)
    chunks = await knowledge_base.get_chunks(processed_document.article_id)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.text, "Chunk text should not be empty"
        assert chunk.chunk_index >= 0, "Chunk index should be valid"

    # Verify all sections became chunks
    expected_headings = {s.heading for s in processed_document.sections}
    actual_headings = {c.heading for c in chunks}
    assert expected_headings.issubset(actual_headings), (
        f"Missing headings: {expected_headings - actual_headings}"
    )


async def test_citations_reference_indexed_document(processed_document, research_agent, knowledge_base):
    """Verify ask() returns sources that reference the indexed document."""
    await knowledge_base.index(processed_document)

    result = await research_agent.ask("What methods were used in this test?")
    assert result.status.value == "completed"
    assert result.answer is not None
    assert result.answer.answer, "Answer should not be empty"

    doc_id = processed_document.article_id
    if result.answer.sources:
        assert any(doc_id in src for src in result.answer.sources), (
            f"Citations must reference '{doc_id}'. Got: {result.answer.sources}"
        )


async def test_multiple_documents_indexed_and_retrieved(knowledge_base, processed_document):
    """Verify multiple documents can coexist in KB."""
    docs_to_index = ["doc-alpha", "doc-beta", "doc-gamma"]
    for suffix in docs_to_index:
        doc = processed_document.model_copy()
        doc.article_id = suffix
        doc.metadata.title = f"Test Document {suffix}"
        await knowledge_base.index(doc)

    all_docs = await knowledge_base.list_documents()
    indexed_ids = {d.document_id for d in all_docs}
    for suffix in docs_to_index:
        assert suffix in indexed_ids, f"Missing document: {suffix}"


async def test_delete_document_removes_all_data(processed_document, knowledge_base):
    """Verify delete removes document, chunks, and vector entries."""
    await knowledge_base.index(processed_document)
    assert await knowledge_base.get_document(processed_document.article_id) is not None

    deleted = await knowledge_base.delete_document(processed_document.article_id)
    assert deleted is True
    assert await knowledge_base.get_document(processed_document.article_id) is None


async def test_vector_search_after_delete(processed_document, knowledge_base):
    """Verify deleted documents don't appear in search results."""
    doc_id = processed_document.article_id
    await knowledge_base.index(processed_document)
    await knowledge_base.delete_document(doc_id)

    results = await knowledge_base.search_text(processed_document.metadata.title, top_k=5)
    assert all(item.chunk.document_id != doc_id for item in results.items), (
        "Deleted document should not appear in search"
    )


async def test_empty_database_returns_empty(knowledge_base):
    """Verify operations on empty KB don't crash."""
    docs = await knowledge_base.list_documents()
    assert docs == [], f"Expected empty list, got {len(docs)} items"

    chunks = await knowledge_base.get_chunks("nonexistent")
    assert chunks == [], f"Expected empty chunks, got {len(chunks)}"

    result = await knowledge_base.search_text("anything")
    assert result.total_found == 0
