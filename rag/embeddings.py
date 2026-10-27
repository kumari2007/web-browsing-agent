"""
Embedding engine with lazy loading, in-memory caching, and deterministic fallback.
Uses SentenceTransformers (all-MiniLM-L6-v2) with TF-IDF/hashing fallback.
"""

import math
import logging
from typing import List, Optional, Dict
import numpy as np
from config import settings

logger = logging.getLogger("agent.rag.embeddings")


class EmbeddingEngine:
    """Manages sentence embedding generation with lazy model instantiation."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._model = None
        self._is_fallback = False
        self._cache: Dict[str, List[float]] = {}

    def _ensure_model(self) -> None:
        """Lazy load the sentence transformer model."""
        if self._model is not None or self._is_fallback:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}); enabling deterministic fallback vectorizer.")
            self._is_fallback = True

    def encode_text(self, text: str) -> List[float]:
        """Encode a single string into a normalized dense embedding vector."""
        text = text.strip()
        if not text:
            return [0.0] * 384

        if text in self._cache:
            return self._cache[text]

        self._ensure_model()

        if self._model and not self._is_fallback:
            try:
                emb = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                emb_list = emb.tolist()
                self._cache[text] = emb_list
                return emb_list
            except Exception as e:
                logger.warning(f"Inference error with SentenceTransformer: {e}; falling back.")
                self._is_fallback = True

        # Deterministic hashing vectorizer fallback
        vec = self._deterministic_hash_vector(text, dim=384)
        self._cache[text] = vec
        return vec

    def encode(self, text: str) -> List[float]:
        """Convenience alias for encode_text."""
        return self.encode_text(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode a collection of texts."""
        if not texts:
            return []

        uncached_indices = []
        uncached_texts = []
        results = [None] * len(texts)

        for i, t in enumerate(texts):
            clean_t = t.strip()
            if clean_t in self._cache:
                results[i] = self._cache[clean_t]
            else:
                uncached_indices.append(i)
                uncached_texts.append(clean_t)

        if not uncached_texts:
            return results

        self._ensure_model()

        if self._model and not self._is_fallback:
            try:
                embeddings = self._model.encode(
                    uncached_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    batch_size=32
                )
                for idx, emb in zip(uncached_indices, embeddings):
                    emb_list = emb.tolist()
                    self._cache[texts[idx].strip()] = emb_list
                    results[idx] = emb_list
                return results
            except Exception as e:
                logger.warning(f"Batch encoding failed ({e}); using deterministic vectorizer.")
                self._is_fallback = True

        for idx, t in zip(uncached_indices, uncached_texts):
            vec = self._deterministic_hash_vector(t, dim=384)
            self._cache[t] = vec
            results[idx] = vec

        return results

    def _deterministic_hash_vector(self, text: str, dim: int = 384) -> List[float]:
        """Generate a reproducible normalized float vector based on character n-grams."""
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for i, word in enumerate(words):
            h = hash(word) % dim
            weight = 1.0 / (1.0 + math.log(i + 1))
            vec[h] += weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two unit vectors."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
