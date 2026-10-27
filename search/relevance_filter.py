"""
Relevance filtering and multi-criteria ranking engine.
Scores candidates using token overlap, title weighting, domain authority, semantic embeddings, and negative heuristics.
"""

import re
import math
from typing import List, Optional, Set
from urllib.parse import urlparse
from .result_parser import SearchResult


class RelevanceFilter:
    """Filters, deduplicates, and ranks candidate search results."""

    # Utility pages that provide no research or article value
    DISQUALIFYING_PATH_KEYWORDS = {
        "login", "signin", "signup", "register", "cart", "checkout",
        "privacy-policy", "terms-of-service", "terms-of-use", "contact-us",
        "cookie-policy", "feedback", "help/customer", "settings"
    }

    # High quality authoritative domains
    AUTHORITATIVE_DOMAINS = {
        "wikipedia.org", "github.com", "docs.python.org", "stackoverflow.com",
        "w3schools.com", "realpython.com", "geeksforgeeks.org", "coursera.org",
        "edx.org", "udemy.com", "amazon.in", "amazon.com", "arxiv.org"
    }

    def __init__(self, embedding_function=None):
        """
        embedding_function: Optional callable(query, texts) returning cosine similarities.
        If None, deterministic lexical scoring is used.
        """
        self.embedding_function = embedding_function

    def filter_and_rank(
        self,
        query: str,
        results: List[SearchResult],
        max_results: int = 5,
        min_relevance_score: float = 0.15
    ) -> List[SearchResult]:
        """
        Deduplicate, score, explain, and sort candidate results.
        """
        if not results:
            return []

        # 1. Deduplication by normalized URL
        unique_results = self._deduplicate(results)

        # 2. Extract query keywords
        query_tokens = self._tokenize(query)

        # 3. Score each candidate
        scored_results: List[SearchResult] = []
        texts_for_embeddings: List[str] = []

        for item in unique_results:
            # Check for utility/disqualifying pages
            if self._is_utility_url(item.url):
                continue

            lexical_score, explanation_parts = self._compute_lexical_score(query_tokens, item)
            domain_bonus, domain_reason = self._compute_domain_bonus(item.url)

            total_score = lexical_score + domain_bonus
            if domain_reason:
                explanation_parts.append(domain_reason)

            item.relevance_score = round(total_score, 3)
            item.rank_explanation = "; ".join(explanation_parts)

            scored_results.append(item)
            texts_for_embeddings.append(f"{item.title} {item.snippet}")

        # 4. Semantic similarity adjustment if embedding model is available
        if self.embedding_function and scored_results:
            try:
                semantic_scores = self.embedding_function(query, texts_for_embeddings)
                for item, sem_score in zip(scored_results, semantic_scores):
                    # Blend 50% lexical + 50% semantic
                    blended = (0.5 * item.relevance_score) + (0.5 * sem_score)
                    item.relevance_score = round(blended, 3)
                    item.rank_explanation += f"; Semantic similarity: {sem_score:.2f}"
            except Exception:
                # Graceful fallback to pure lexical scoring
                pass

        # 5. Filter out low relevance candidates
        filtered = [r for r in scored_results if r.relevance_score >= min_relevance_score]

        # 6. Sort descending by relevance
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)

        return filtered[:max_results]

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        seen_urls: Set[str] = set()
        unique: List[SearchResult] = []
        for r in results:
            norm = r.url.rstrip("/")
            if norm not in seen_urls:
                seen_urls.add(norm)
                unique.append(r)
        return unique

    def _tokenize(self, text: str) -> Set[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        # Filter out trivial stop words
        stops = {"the", "a", "an", "for", "and", "in", "of", "to", "on", "with", "is", "at", "by"}
        return {w for w in words if w not in stops}

    def _is_utility_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return any(keyword in path for keyword in self.DISQUALIFYING_PATH_KEYWORDS)

    def _compute_lexical_score(self, query_tokens: Set[str], item: SearchResult) -> (float, List[str]):
        if not query_tokens:
            return 0.5, ["Generic baseline match"]

        title_tokens = self._tokenize(item.title)
        snippet_tokens = self._tokenize(item.snippet)

        title_overlap = len(query_tokens.intersection(title_tokens))
        snippet_overlap = len(query_tokens.intersection(snippet_tokens))

        title_ratio = title_overlap / len(query_tokens)
        snippet_ratio = snippet_overlap / len(query_tokens)

        # Title match has 2.5x higher weight than snippet
        score = (title_ratio * 0.70) + (snippet_ratio * 0.30)

        # Exact phrase match bonus
        query_str = " ".join(query_tokens)
        if query_str in item.title.lower():
            score += 0.20

        explanations = []
        if title_overlap > 0:
            explanations.append(f"Title matched {title_overlap}/{len(query_tokens)} query terms")
        if snippet_overlap > 0:
            explanations.append(f"Snippet matched {snippet_overlap}/{len(query_tokens)} terms")

        return score, explanations

    def _compute_domain_bonus(self, url: str) -> (float, str):
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        for auth in self.AUTHORITATIVE_DOMAINS:
            if auth in netloc:
                return 0.15, f"Domain authority bonus ({auth})"

        if netloc.endswith(".edu") or netloc.endswith(".gov") or netloc.endswith(".org"):
            return 0.10, "Authoritative TLD bonus (.edu/.org/.gov)"

        return 0.0, ""
