"""
Persistent vector store implementation with ChromaDB and SQLite fallback.
Provides vector indexing, similarity queries, and metadata persistence.
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from config import settings
from .chunker import TextChunk

logger = logging.getLogger("agent.rag.vector_store")


class VectorStore:
    """Manages persistent document embeddings and similarity queries."""

    def __init__(self, db_path: Optional[Path] = None, collection_name: str = "agent_knowledge"):
        self.db_path = db_path or (settings.data_dir / "sqlite_vector_store.db")
        self.collection_name = collection_name
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite vector store schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    collection TEXT,
                    url TEXT,
                    title TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    metadata_json TEXT,
                    embedding_blob BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON document_chunks(collection)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON document_chunks(url)")
            conn.commit()

    def add_chunks(
        self,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
        collection_name: Optional[str] = None
    ) -> None:
        """Persist chunks and their embedding vectors."""
        if not chunks:
            return

        target_coll = collection_name or self.collection_name

        with sqlite3.connect(self.db_path) as conn:
            records = []
            for chunk, emb in zip(chunks, embeddings):
                emb_bytes = np.array(emb, dtype=np.float32).tobytes()
                meta_json = json.dumps(chunk.metadata)
                records.append((
                    chunk.id,
                    target_coll,
                    chunk.url,
                    chunk.title,
                    chunk.chunk_index,
                    chunk.text,
                    meta_json,
                    emb_bytes
                ))

            conn.executemany("""
                INSERT OR REPLACE INTO document_chunks 
                (id, collection, url, title, chunk_index, text, metadata_json, embedding_blob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

        logger.info(f"Indexed {len(chunks)} chunks into vector store '{target_coll}'")

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.20,
        collection_name: Optional[str] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Compute cosine similarity across all stored chunks in current collection.
        Returns sorted list of (chunk, similarity_score).
        """
        target_coll = collection_name or self.collection_name
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        candidates = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, title, chunk_index, text, metadata_json, embedding_blob
                FROM document_chunks
                WHERE collection = ?
            """, (target_coll,))

            for row in cursor.fetchall():
                cid, url, title, idx, text, meta_json, emb_bytes = row
                emb_arr = np.frombuffer(emb_bytes, dtype=np.float32)
                
                denom = q_norm * np.linalg.norm(emb_arr)
                if denom == 0:
                    sim = 0.0
                else:
                    sim = float(np.dot(q_vec, emb_arr) / denom)

                if sim >= min_similarity:
                    meta = json.loads(meta_json) if meta_json else {}
                    chunk = TextChunk(
                        id=cid,
                        url=url,
                        title=title,
                        chunk_index=idx,
                        text=text,
                        metadata=meta
                    )
                    candidates.append((chunk, round(sim, 4)))

        # Sort descending by similarity
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def clear(self, collection_name: Optional[str] = None) -> None:
        """Clear all records in the specified or current collection."""
        target_coll = collection_name or self.collection_name
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM document_chunks WHERE collection = ?", (target_coll,))
            conn.commit()

    def count(self, collection_name: Optional[str] = None) -> int:
        """Return number of chunks in current collection."""
        target_coll = collection_name or self.collection_name
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE collection = ?", (target_coll,))
            return cursor.fetchone()[0]
