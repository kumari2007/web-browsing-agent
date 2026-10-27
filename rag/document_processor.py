"""
Document processor bridging raw extracted web pages and vector storage.
Coordinates chunking, batch embedding, and indexing.
"""

from typing import List, Optional
from extraction.page_extractor import ExtractedPage
from .chunker import TextChunker, TextChunk
from .embeddings import EmbeddingEngine
from .vector_store import VectorStore
import time


class DocumentProcessor:
    """Processes extracted web content into embedded chunks within the vector store."""

    def __init__(
        self,
        chunker: Optional[TextChunker] = None,
        embeddings: Optional[EmbeddingEngine] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.chunker = chunker or TextChunker()
        self.embeddings = embeddings or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore()

    def process_and_index_page(
        self,
        page: ExtractedPage,
        collection_name: Optional[str] = None
    ) -> List[TextChunk]:
        """Split page into chunks, generate embeddings, and store persistently."""
        if not page.clean_text:
            return []

        extra_meta = {
            "title": page.title,
            "url": page.url,
            "indexed_at": time.time(),
        }

        chunks = self.chunker.chunk_document(
            text=page.clean_text,
            url=page.url,
            title=page.title,
            extra_metadata=extra_meta
        )

        if not chunks:
            return []

        # Batch compute embeddings
        texts = [c.text for c in chunks]
        embeddings = self.embeddings.encode_batch(texts)

        # Store in vector store
        self.vector_store.add_chunks(chunks, embeddings, collection_name=collection_name)

        return chunks
