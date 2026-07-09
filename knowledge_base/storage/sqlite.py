"""SQLite storage backend — persists documents, chunks, embeddings."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from knowledge_base.exceptions import StorageError
from knowledge_base.models import Chunk, ChunkEmbedding, KnowledgeDocument
from knowledge_base.storage.base import BaseStorage


class SQLiteStorage(BaseStorage):
    def __init__(self, database_path: str = "./knowledge_base.db"):
        if database_path == ":memory:":
            self._path = ":memory:"
        else:
            self._path = str(Path(database_path).resolve())
        self._conn: sqlite3.Connection | None = None

    async def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._path)
            self._conn.row_factory = sqlite3.Row
            self._init_db()
        return self._conn

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                metadata TEXT NOT NULL DEFAULT '{}',
                statistics TEXT NOT NULL DEFAULT '{}',
                source_file TEXT NOT NULL DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL DEFAULT 0,
                section TEXT NOT NULL DEFAULT '',
                heading TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                markdown TEXT NOT NULL DEFAULT '',
                page_start INTEGER NOT NULL DEFAULT 0,
                page_end INTEGER NOT NULL DEFAULT 0,
                token_count INTEGER NOT NULL DEFAULT 0,
                word_count INTEGER NOT NULL DEFAULT 0,
                citations TEXT NOT NULL DEFAULT '[]',
                tables TEXT NOT NULL DEFAULT '[]',
                figures TEXT NOT NULL DEFAULT '[]',
                previous_chunk TEXT NOT NULL DEFAULT '',
                next_chunk TEXT NOT NULL DEFAULT '',
                metadata TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                embedding BLOB,
                model TEXT NOT NULL DEFAULT '',
                dimensions INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_embeddings_doc ON embeddings(document_id)"
        )
        self._conn.commit()

    # ---- documents ---------------------------------------------------------
    async def save_document(self, doc: KnowledgeDocument) -> None:
        conn = await self._connect()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (document_id, status, metadata, statistics, source_file, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc.document_id,
                    doc.status.value,
                    json.dumps(doc.metadata),
                    json.dumps(doc.statistics.model_dump() if hasattr(doc.statistics, 'model_dump') else {}),
                    doc.source_file,
                    doc.created_at.isoformat() if doc.created_at else None,
                    doc.updated_at.isoformat() if doc.updated_at else None,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to save document {doc.document_id}: {exc}") from exc

    async def get_document(self, document_id: str) -> KnowledgeDocument | None:
        conn = await self._connect()
        row = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_doc(row)

    async def delete_document(self, document_id: str) -> bool:
        conn = await self._connect()
        conn.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        cur = conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        conn.commit()
        return cur.rowcount > 0

    async def list_documents(self) -> list[KnowledgeDocument]:
        conn = await self._connect()
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [self._row_to_doc(r) for r in rows]

    # ---- chunks ------------------------------------------------------------
    async def save_chunks(self, chunks: list[Chunk]) -> None:
        conn = await self._connect()
        try:
            for c in chunks:
                conn.execute(
                    """INSERT OR REPLACE INTO chunks
                       (id, document_id, chunk_index, section, heading, text, markdown,
                        page_start, page_end, token_count, word_count,
                        citations, tables, figures,
                        previous_chunk, next_chunk, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        c.id, c.document_id, c.chunk_index, c.section, c.heading,
                        c.text, c.markdown, c.page_start, c.page_end,
                        c.token_count, c.word_count,
                        json.dumps(c.citations), json.dumps(c.tables), json.dumps(c.figures),
                        c.previous_chunk, c.next_chunk, json.dumps(c.metadata),
                    ),
                )
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to save chunks: {exc}") from exc

    async def get_chunks(self, document_id: str) -> list[Chunk]:
        conn = await self._connect()
        rows = conn.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
        return [self._row_to_chunk(r) for r in rows]

    # ---- embeddings --------------------------------------------------------
    async def save_embeddings(self, embeddings: list[ChunkEmbedding]) -> None:
        conn = await self._connect()
        try:
            for e in embeddings:
                blob = json.dumps(e.embedding).encode()
                conn.execute(
                    """INSERT OR REPLACE INTO embeddings
                       (chunk_id, document_id, embedding, model, dimensions)
                       VALUES (?, ?, ?, ?, ?)""",
                    (e.chunk_id, e.document_id, blob, e.model, e.dimensions),
                )
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to save embeddings: {exc}") from exc

    async def get_embeddings(self, document_id: str) -> list[ChunkEmbedding]:
        conn = await self._connect()
        rows = conn.execute(
            "SELECT * FROM embeddings WHERE document_id = ?", (document_id,)
        ).fetchall()
        return [self._row_to_embedding(r) for r in rows]

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ---- helpers -----------------------------------------------------------
    @staticmethod
    def _row_to_doc(row) -> KnowledgeDocument:
        from datetime import datetime
        from knowledge_base.models import DocumentStatistics, IndexingStatus

        return KnowledgeDocument(
            document_id=row["document_id"],
            status=IndexingStatus(row["status"]),
            metadata=json.loads(row["metadata"]),
            statistics=DocumentStatistics(**json.loads(row["statistics"])) if row["statistics"] else DocumentStatistics(),
            source_file=row["source_file"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    @staticmethod
    def _row_to_chunk(row) -> Chunk:
        return Chunk(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            section=row["section"],
            heading=row["heading"],
            text=row["text"],
            markdown=row["markdown"],
            page_start=row["page_start"],
            page_end=row["page_end"],
            token_count=row["token_count"],
            word_count=row["word_count"],
            citations=json.loads(row["citations"]),
            tables=json.loads(row["tables"]),
            figures=json.loads(row["figures"]),
            previous_chunk=row["previous_chunk"],
            next_chunk=row["next_chunk"],
            metadata=json.loads(row["metadata"]),
        )

    @staticmethod
    def _row_to_embedding(row) -> ChunkEmbedding:
        return ChunkEmbedding(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            embedding=json.loads(row["embedding"].decode()) if row["embedding"] else [],
            model=row["model"],
            dimensions=row["dimensions"],
        )


def _parse_dt(value: str | None) -> object:
    if not value:
        return None
    from datetime import datetime
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None