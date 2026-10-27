"""
Hybrid retrieval engine combining semantic embeddings and keyword overlap.
Applies deduplication, minimum thresholding, and provenance preservation.
"""

import re
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
from .embeddings import EmbeddingEngine
from .vector_store import VectorStore
from .chunker import TextChunk
from config import settings


class RetrievedEvidence(BaseModel):
    chunk_id: str
    url: str
    title: str
    text: str
    score: float
    semantic_score: float = 0.0
    keyword_score: float = 0.0


class HybridRetriever:
    """Retrieves relevant evidence using dense vector similarity and lexical matching."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embeddings: Optional[EmbeddingEngine] = None,
        relevance_threshold: float = 0.25
    ):
        self.vector_store = vector_store or VectorStore()
        self.embeddings = embeddings or EmbeddingEngine()
        self.relevance_threshold = relevance_threshold

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_threshold: Optional[float] = None,
        collection_name: Optional[str] = None
    ) -> List[RetrievedEvidence]:
        """
        Retrieve and rank the most relevant evidence chunks for a query.
        """
        threshold = min_threshold if min_threshold is not None else self.relevance_threshold

        # 1. Semantic dense search
        query_emb = self.embeddings.encode_text(query)
        dense_results = self.vector_store.search_similar(
            query_embedding=query_emb,
            top_k=top_k * 2,
            min_similarity=0.10,
            collection_name=collection_name
        )

        query_tokens = self._tokenize(query)
        scored_candidates: List[RetrievedEvidence] = []
        seen_texts = set()

        for chunk, sem_sim in dense_results:
            # Deduplicate similar text chunks
            clean_sub = chunk.text[:80].lower()
            if clean_sub in seen_texts:
                continue
            seen_texts.add(clean_sub)

            # Keyword lexical match
            kw_score = self._compute_keyword_score(query_tokens, chunk.text)

            # Hybrid blend: 70% semantic + 30% lexical
            blended_score = round((0.70 * sem_sim) + (0.30 * kw_score), 4)

            if blended_score >= threshold:
                scored_candidates.append(RetrievedEvidence(
                    chunk_id=chunk.id,
                    url=chunk.url,
                    title=chunk.title,
                    text=chunk.text,
                    score=blended_score,
                    semantic_score=round(sem_sim, 4),
                    keyword_score=round(kw_score, 4)
                ))

        # Sort descending by blended score
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        return scored_candidates[:top_k]

    def _tokenize(self, text: str) -> set:
        words = re.findall(r"[a-z0-9]+", text.lower())
        stops = {"what", "is", "the", "for", "and", "in", "of", "to", "how", "a", "an", "on", "with"}
        return {w for w in words if w not in stops}

    def _compute_keyword_score(self, query_tokens: set, text: str) -> float:
        if not query_tokens:
            return 0.5
        text_tokens = self._tokenize(text)
        overlap = len(query_tokens.intersection(text_tokens))
        return min(1.0, overlap / max(1, len(query_tokens)))
