"""
Text chunking engine with metadata preservation and sliding window overlap.
Splits documents along paragraph and sentence boundaries.
"""

import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class TextChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    text: str
    url: str
    title: str
    chunk_index: int
    char_start: int = 0
    char_end: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TextChunker:
    """Splits long text documents into semantically coherent overlapping chunks."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        text: str,
        url: str,
        title: str,
        extra_metadata: Dict[str, Any] = None
    ) -> List[TextChunk]:
        """
        Split document text into chunks while preserving paragraph and sentence continuity.
        """
        if not text or not text.strip():
            return []

        extra_metadata = extra_metadata or {}
        # Normalize double newlines to split paragraphs
        paragraphs = re.split(r"\n\s*\n", text.strip())

        chunks: List[TextChunk] = []
        current_chunk_text = ""
        chunk_idx = 0
        char_counter = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size and we already have content
            if len(current_chunk_text) + len(para) > self.chunk_size and current_chunk_text:
                chunk_obj = TextChunk(
                    text=current_chunk_text.strip(),
                    url=url,
                    title=title,
                    chunk_index=chunk_idx,
                    char_start=char_counter,
                    char_end=char_counter + len(current_chunk_text),
                    metadata=dict(extra_metadata)
                )
                chunks.append(chunk_obj)
                chunk_idx += 1
                char_counter += len(current_chunk_text) - self.chunk_overlap

                # Retain overlap from end of previous chunk
                overlap_text = current_chunk_text[-self.chunk_overlap:] if len(current_chunk_text) > self.chunk_overlap else ""
                current_chunk_text = overlap_text + "\n" + para
            else:
                if current_chunk_text:
                    current_chunk_text += "\n" + para
                else:
                    current_chunk_text = para

        # Append final chunk
        if current_chunk_text.strip():
            chunks.append(TextChunk(
                text=current_chunk_text.strip(),
                url=url,
                title=title,
                chunk_index=chunk_idx,
                char_start=char_counter,
                char_end=char_counter + len(current_chunk_text),
                metadata=dict(extra_metadata)
            ))

        return chunks
