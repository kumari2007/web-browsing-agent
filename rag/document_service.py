"""
Document Ingestion Service for Knowledge Base management.
Handles ingestion of local documents (TXT, MD, PDF) and web pages into the RAG vector store,
tracks document provenance (local_document, webpage, experience), chunking, and search.
"""

import os
import io
import time
import uuid
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import settings
from .chunker import TextChunker, TextChunk
from .embeddings import EmbeddingEngine
from .vector_store import VectorStore
from .retriever import HybridRetriever

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

logger = logging.getLogger("agent.rag.knowledge")

COLLECTION_KNOWLEDGE = "knowledge_base"


class DocumentItem:
    def __init__(
        self,
        doc_id: str,
        title: str,
        source_type: str,
        chunk_count: int,
        source_path_or_url: str,
        created_at: str
    ):
        self.doc_id = doc_id
        self.title = title
        self.source_type = source_type
        self.chunk_count = chunk_count
        self.source_path_or_url = source_path_or_url
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source_type": self.source_type,
            "chunk_count": self.chunk_count,
            "source_path_or_url": self.source_path_or_url,
            "created_at": self.created_at
        }


class KnowledgeBaseService:
    """Manages the indexing, query, and lifecycle of knowledge documents."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunker: Optional[TextChunker] = None,
        embeddings: Optional[EmbeddingEngine] = None
    ):
        self.vector_store = vector_store or VectorStore()
        self.chunker = chunker or TextChunker(chunk_size=500, chunk_overlap=100)
        self.embeddings = embeddings or EmbeddingEngine()

    def ingest_text(
        self,
        content: str,
        title: str,
        source_type: str = "local_document",
        source_path: str = "",
        collection: str = COLLECTION_KNOWLEDGE
    ) -> Dict[str, Any]:
        """Chunk, embed, and store raw text content."""
        if not content.strip():
            raise ValueError("Document content cannot be empty.")

        doc_id = str(uuid.uuid4())[:8]
        url = source_path or f"doc://{doc_id}/{title}"
        metadata = {
            "doc_id": doc_id,
            "source_type": source_type,
            "source_path": source_path,
            "title": title,
            "ingested_at": time.time()
        }

        chunks = self.chunker.chunk_document(
            text=content,
            url=url,
            title=title,
            extra_metadata=metadata
        )

        if not chunks:
            return {"doc_id": doc_id, "chunk_count": 0, "status": "empty"}

        texts = [c.text for c in chunks]
        embeddings = self.embeddings.encode_batch(texts)

        self.vector_store.add_chunks(chunks, embeddings, collection_name=collection)
        logger.info(f"Ingested '{title}' ({len(chunks)} chunks) into collection '{collection}'")

        return {
            "doc_id": doc_id,
            "title": title,
            "source_type": source_type,
            "chunk_count": len(chunks),
            "status": "indexed"
        }

    def ingest_file_bytes(
        self,
        filename: str,
        file_bytes: bytes,
        collection: str = COLLECTION_KNOWLEDGE
    ) -> Dict[str, Any]:
        """Extract text from uploaded file bytes (TXT, MD, PDF) and index."""
        ext = os.path.splitext(filename)[1].lower()
        title = filename

        if ext in {".txt", ".md", ".markdown", ".csv", ".json"}:
            try:
                content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = file_bytes.decode("latin-1", errors="ignore")
        elif ext == ".pdf":
            if not PYPDF_AVAILABLE:
                raise RuntimeError("pypdf is not installed. PDF parsing unavailable.")
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    pages_text.append(f"--- Page {i+1} ---\n{txt}")
            content = "\n\n".join(pages_text)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: .txt, .md, .pdf, .json, .csv")

        return self.ingest_text(
            content=content,
            title=title,
            source_type="local_document",
            source_path=filename,
            collection=collection
        )

    def list_documents(self, collection: str = COLLECTION_KNOWLEDGE) -> List[Dict[str, Any]]:
        """List all indexed documents with chunk counts and provenance."""
        docs = {}
        with sqlite3.connect(self.vector_store.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, title, metadata_json, created_at
                FROM document_chunks
                WHERE collection = ?
                ORDER BY created_at DESC
            """, (collection,))
            for url, title, meta_json, created_at in cursor.fetchall():
                meta = json.loads(meta_json) if meta_json else {}
                doc_id = meta.get("doc_id", url)
                source_type = meta.get("source_type", "webpage" if url.startswith("http") else "local_document")

                if doc_id not in docs:
                    docs[doc_id] = {
                        "doc_id": doc_id,
                        "title": title or "Untitled Document",
                        "source_type": source_type,
                        "chunk_count": 0,
                        "source_path_or_url": meta.get("source_path") or url,
                        "created_at": created_at
                    }
                docs[doc_id]["chunk_count"] += 1

        return list(docs.values())

    def delete_document(self, doc_id_or_url: str, collection: str = COLLECTION_KNOWLEDGE) -> bool:
        """Remove all chunks associated with a document or URL."""
        with sqlite3.connect(self.vector_store.db_path) as conn:
            # Delete where url = doc_id_or_url OR metadata contains doc_id
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM document_chunks
                WHERE collection = ? AND (
                    url = ? OR
                    id LIKE (? || '%') OR
                    metadata_json LIKE ('%"doc_id": "' || ? || '"%')
                )
            """, (collection, doc_id_or_url, doc_id_or_url, doc_id_or_url))
            conn.commit()
            return cursor.rowcount > 0

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.15,
        collection: str = COLLECTION_KNOWLEDGE
    ) -> List[Dict[str, Any]]:
        """Search indexed knowledge chunks with similarity scoring and provenance."""
        query_emb = self.embeddings.encode_text(query)
        results = self.vector_store.search_similar(
            query_embedding=query_emb,
            top_k=top_k,
            min_similarity=min_similarity,
            collection_name=collection
        )

        formatted = []
        for chunk, score in results:
            meta = chunk.metadata or {}
            source_type = meta.get("source_type")
            if not source_type:
                if chunk.url.startswith("http"):
                    source_type = "webpage"
                elif "memory" in chunk.url or "experience" in chunk.url:
                    source_type = "experience"
                else:
                    source_type = "local_document"

            formatted.append({
                "chunk_id": chunk.id,
                "title": chunk.title,
                "url": chunk.url,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "relevance_score": score,
                "source_type": source_type,
                "metadata": meta
            })

        return formatted
