"""
Evidence-based answer generator.
Synthesizes answers grounded in retrieved RAG context using Ollama, with deterministic fallback.
Attaches clickable markdown source links and clearly marks unverified claims.
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional
from .retriever import RetrievedEvidence
from .llm_provider import BaseLLMProvider, get_llm_provider
from config import settings

logger = logging.getLogger("agent.rag.generator")


class AnswerGenerator:
    """Generates grounded final answers citing verified web evidence."""

    SYSTEM_PROMPT = """You are an objective, evidence-based research assistant.
Answer the user's question using ONLY the provided verified source evidence below.
CRITICAL RULES:
1. Every major fact, feature, price, or comparison point MUST be grounded in the provided evidence.
2. Cite your sources using markdown links: [Source Title](URL).
3. If specific information (e.g. price, specification, course detail) is not mentioned or missing in the sources, explicitly state: "Not specified in visited sources".
4. Do NOT hallucinate or assume facts not present in the sources.
5. Provide a well-structured response with clear headings or comparison tables where appropriate.
6. Clearly distinguish verified facts from unknowns."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        provider: Optional[BaseLLMProvider] = None
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout_seconds or settings.ollama_timeout_seconds
        self.provider = provider or get_llm_provider()

    def generate_answer(
        self,
        query: str,
        evidence: List[RetrievedEvidence],
        extra_structured_facts: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Synthesize answer from retrieved chunks using Ollama or fallback to deterministic synthesizer.
        """
        if not evidence:
            return (
                "### Incomplete Research\n\n"
                "No sufficiently relevant evidence could be retrieved from the inspected pages "
                "to answer the question reliably."
            )

        # Build context block
        context_blocks = []
        unique_sources = {}

        for i, ev in enumerate(evidence, 1):
            unique_sources[ev.url] = ev.title
            snippet = ev.text.replace("\n", " ").strip()
            if len(snippet) > 800:
                snippet = snippet[:800] + "..."
            context_blocks.append(
                f"[Source {i}: {ev.title}]\nURL: {ev.url}\nRelevance: {ev.score:.2f}\nContent: {snippet}\n"
            )

        context_str = "\n".join(context_blocks)
        observed_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        prompt = (
            f"Observation Timestamp: {observed_time}\n\n"
            f"User Question: {query}\n\n"
            f"VERIFIED EVIDENCE:\n{context_str}\n\n"
            f"Please synthesize a clear, comprehensive, and evidence-grounded answer based strictly on the above evidence."
        )

        # 1. Attempt Configured LLM Generation
        try:
            answer_text = self.provider.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            if answer_text:
                return self._append_source_footer(answer_text, unique_sources, observed_time)
        except Exception as e:
            logger.warning(f"Configured LLM provider failed ({e}); switching to deterministic fallback.")

        # 2. Deterministic Fallback Synthesizer
        return self._deterministic_synthesizer(query, evidence, unique_sources, observed_time)

    def _deterministic_synthesizer(
        self,
        query: str,
        evidence: List[RetrievedEvidence],
        sources: Dict[str, str],
        observed_time: str
    ) -> str:
        """
        Produce a structured deterministic synthesis when local LLM is offline.
        Transparently discloses the fallback mechanism.
        """
        lines = [
            f"### Research Findings for: *{query}*",
            "> **Note:** Synthesized using deterministic evidence extractor (Ollama local LLM was offline or timed out).\n",
            f"**Information Observed At:** `{observed_time}`\n",
            "#### Key Evidence Extracted:\n"
        ]

        for i, ev in enumerate(evidence[:4], 1):
            clean_snippet = ev.text.strip().replace("\n", "\n> ")
            if len(clean_snippet) > 400:
                clean_snippet = clean_snippet[:400] + "..."
            lines.append(f"**{i}. [{ev.title}]({ev.url})** (Relevance: {ev.score:.2f})")
            lines.append(f"> {clean_snippet}\n")

        lines.append("#### Verified Sources:")
        for url, title in sources.items():
            lines.append(f"- [{title}]({url})")

        return "\n".join(lines)

    def _append_source_footer(self, answer: str, sources: Dict[str, str], observed_time: str) -> str:
        """Ensure clean sources footer with clickable markdown links."""
        footer_lines = [
            "\n\n---\n#### Verified Source Citations:",
            f"*Observed at: {observed_time}*"
        ]
        for url, title in sources.items():
            # Only append if not already hyperlinked in text
            if f"({url})" not in answer:
                footer_lines.append(f"- [{title}]({url})")
            else:
                footer_lines.append(f"- Verified: [{title}]({url})")

        return answer + "\n" + "\n".join(footer_lines)
