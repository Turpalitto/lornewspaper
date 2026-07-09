"""Tests for chunking strategies."""

import pytest

from knowledge_base.chunking.fixed import FixedChunker
from knowledge_base.chunking.section import SectionChunker
from knowledge_base.chunking.sentence import SentenceChunker
from knowledge_base.models import Chunk


def test_section_chunker_creates_chunks():
    text = "Abstract\nThis is test.\n\nIntroduction\nBody text here."
    meta = {"sections": [
        {"heading": "Abstract", "content": "This is test.", "level": 1},
        {"heading": "Introduction", "content": "Body text here.", "level": 1},
    ]}
    c = SectionChunker(min_chunk_length=5)
    chunks = c.chunk("doc1", text, metadata=meta)
    assert len(chunks) == 2
    assert chunks[0].heading == "Abstract"
    assert chunks[1].heading == "Introduction"
    assert chunks[0].document_id == "doc1"
    assert chunks[0].id.startswith("doc1_chunk_")
    assert chunks[1].chunk_index == 1


def test_section_chunker_fallback_no_sections():
    c = SectionChunker()
    chunks = c.chunk("doc2", "Some text without sections.")
    assert len(chunks) == 1
    assert chunks[0].heading == "Body"
    assert chunks[0].section == "Body"
    assert chunks[0].text == "Some text without sections."


def test_section_chunker_skips_short_sections():
    meta = {"sections": [
        {"heading": "Intro", "content": "Hi", "level": 1},
        {"heading": "Body", "content": "Longer content here.", "level": 1},
    ]}
    c = SectionChunker(min_chunk_length=10)
    chunks = c.chunk("doc3", "Hi\nLonger content here.", metadata=meta)
    assert len(chunks) == 1
    assert chunks[0].heading == "Body"


def test_sentence_chunker_splits_by_sentences():
    text = "First sentence. Second sentence here. Third one!"
    c = SentenceChunker(min_chunk_length=5)
    chunks = c.chunk("doc4", text)
    assert len(chunks) >= 2
    assert all(c.document_id == "doc4" for c in chunks)
    assert all(c.text for c in chunks)
    assert all(c.token_count > 0 for c in chunks)


def test_sentence_chunker_filters_short():
    c = SentenceChunker(min_chunk_length=100)
    chunks = c.chunk("doc5", "Short. Also short.")
    assert len(chunks) == 0


def test_fixed_chunker_creates_chunks():
    words = "word " * 100
    c = FixedChunker(chunk_size=20, chunk_overlap=5, min_chunk_length=5)
    chunks = c.chunk("doc6", words)
    assert len(chunks) >= 4
    assert all(c.document_id == "doc6" for c in chunks)
    assert all(c.word_count > 0 for c in chunks)


def test_fixed_chunker_links_adjacent():
    words = "word " * 50
    c = FixedChunker(chunk_size=20, chunk_overlap=5, min_chunk_length=5)
    chunks = c.chunk("doc7", words)
    if len(chunks) >= 2:
        assert chunks[0].next_chunk == chunks[1].id
        assert chunks[1].previous_chunk == chunks[0].id


def test_fixed_chunker_overlap_validation():
    with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
        FixedChunker(chunk_size=10, chunk_overlap=10)
    with pytest.raises(ValueError, match="min_chunk_length cannot exceed chunk_size"):
        FixedChunker(chunk_size=10, chunk_overlap=2, min_chunk_length=15)


def test_fixed_chunker_single_chunk():
    c = FixedChunker(chunk_size=1000, chunk_overlap=64, min_chunk_length=5)
    chunks = c.chunk("doc8", "short text")
    assert len(chunks) == 1
    assert chunks[0].text == "short text"


def test_chunk_ids_unique_per_strategy():
    text = "A B C. D E F."
    c1 = SectionChunker()
    c2 = SentenceChunker()
    c3 = FixedChunker(chunk_size=5, chunk_overlap=0, min_chunk_length=1)
    ids1 = [ch.id for ch in c1.chunk("doc", text)]
    ids2 = [ch.id for ch in c2.chunk("doc", text)]
    ids3 = [ch.id for ch in c3.chunk("doc", text)]
    # IDs should be unique within each strategy (each starts at 0000)
    assert len(ids1) == len(set(ids1))
    assert len(ids2) == len(set(ids2))
    assert len(ids3) == len(set(ids3))


def test_section_chunker_token_count_matches_words():
    text = "Five words here now"
    c = SectionChunker()
    chunks = c.chunk("doc", text)
    assert chunks[0].word_count == 4
    assert chunks[0].token_count == 4