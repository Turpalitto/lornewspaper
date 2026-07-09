"""Tests for SQLite storage backend."""

from datetime import UTC, datetime

import pytest

from knowledge_base.models import Chunk, ChunkEmbedding, DocumentStatistics, IndexingStatus, KnowledgeDocument
from knowledge_base.storage.sqlite import SQLiteStorage


@pytest.fixture
async def store():
    s = SQLiteStorage(database_path=":memory:")
    yield s
    await s.close()


@pytest.mark.asyncio
async def test_save_and_get_document(store):
    doc = KnowledgeDocument(
        document_id="test1",
        status=IndexingStatus.COMPLETED,
        metadata={"title": "Test Doc"},
        source_file="/path/to/doc.pdf",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await store.save_document(doc)
    loaded = await store.get_document("test1")
    assert loaded is not None
    assert loaded.document_id == "test1"
    assert loaded.status == IndexingStatus.COMPLETED
    assert loaded.metadata.get("title") == "Test Doc"
    assert loaded.source_file == "/path/to/doc.pdf"


@pytest.mark.asyncio
async def test_get_nonexistent_document(store):
    doc = await store.get_document("nonexistent")
    assert doc is None


@pytest.mark.asyncio
async def test_delete_document(store):
    doc = KnowledgeDocument(document_id="delete_me")
    await store.save_document(doc)
    assert await store.get_document("delete_me") is not None
    deleted = await store.delete_document("delete_me")
    assert deleted is True
    assert await store.get_document("delete_me") is None


@pytest.mark.asyncio
async def test_list_documents(store):
    await store.save_document(KnowledgeDocument(document_id="a"))
    await store.save_document(KnowledgeDocument(document_id="b"))
    docs = await store.list_documents()
    assert len(docs) >= 2
    ids = [d.document_id for d in docs]
    assert "a" in ids
    assert "b" in ids


@pytest.mark.asyncio
async def test_save_and_get_chunks(store):
    chunks = [
        Chunk(id="c1", document_id="doc_x", chunk_index=0, text="Chunk one", word_count=2, token_count=2),
        Chunk(id="c2", document_id="doc_x", chunk_index=1, text="Chunk two", word_count=2, token_count=2),
    ]
    await store.save_chunks(chunks)
    loaded = await store.get_chunks("doc_x")
    assert len(loaded) == 2
    assert loaded[0].id == "c1"
    assert loaded[1].id == "c2"


@pytest.mark.asyncio
async def test_save_and_get_embeddings(store):
    embs = [
        ChunkEmbedding(chunk_id="c1", document_id="doc_y", embedding=[0.1, 0.2], model="test", dimensions=2),
        ChunkEmbedding(chunk_id="c2", document_id="doc_y", embedding=[0.3, 0.4], model="test", dimensions=2),
    ]
    await store.save_embeddings(embs)
    loaded = await store.get_embeddings("doc_y")
    assert len(loaded) == 2
    assert loaded[0].embedding == [0.1, 0.2]
    assert loaded[1].dimensions == 2


@pytest.mark.asyncio
async def test_delete_cascades_to_chunks_and_embeddings(store):
    doc = KnowledgeDocument(document_id="delete_all")
    await store.save_document(doc)
    await store.save_chunks([Chunk(id="del_c1", document_id="delete_all")])
    await store.save_embeddings([ChunkEmbedding(chunk_id="del_c1", document_id="delete_all")])
    await store.delete_document("delete_all")
    assert await store.get_chunks("delete_all") == []
    assert await store.get_embeddings("delete_all") == []


@pytest.mark.asyncio
async def test_list_documents_empty(store):
    docs = await store.list_documents()
    assert isinstance(docs, list)