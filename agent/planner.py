"""
Task planning and query decomposition engine.
Parses natural-language user queries into structured execution plans,
classifying task types and setting completion criteria.
"""

import re
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from .task_state import Plan, TaskType, Action, ActionType
from config import settings

logger = logging.getLogger("agent.planner")


class TaskPlanner:
    """Creates structured multi-step execution plans from natural-language instructions."""

    def __init__(self, ollama_url: Optional[str] = None, model: Optional[str] = None):
        self.ollama_url = ollama_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    def create_plan(
        self,
        query: str,
        max_inspect_pages: int = 3,
        start_url: Optional[str] = None,
        max_depth: int = 2
    ) -> Plan:
        """Formulate execution plan with deterministic rules and LLM refinement."""
        task_type = self._classify_task_type(query)
        target_domains = self._extract_target_domains(query)
        completion_criteria = self._generate_completion_criteria(query, task_type)

        actions: List[Action] = []

        if start_url and start_url.strip():
            # Direct starting URL workflow
            clean_start = start_url.strip()
            actions.append(Action(
                action_type=ActionType.NAVIGATE,
                description=f"Directly navigate to starting URL: {clean_start}",
                params={"url": clean_start, "count": 1, "depth": 0}
            ))
            actions.append(Action(
                action_type=ActionType.EXTRACT,
                description="Extract page content, metadata, and structured facts from starting URL",
                params={"max_chars": settings.max_page_chars_to_extract, "deep_links": max_depth > 1}
            ))
            if max_inspect_pages > 1:
                actions.append(Action(
                    action_type=ActionType.NAVIGATE,
                    description=f"Explore up to {max_inspect_pages - 1} related links up to depth {max_depth}",
                    params={"count": max_inspect_pages - 1, "depth": max_depth, "use_discovered_links": True}
                ))
        else:
            # 1. Search action
            search_provider = self._select_search_provider(target_domains, query)
            actions.append(Action(
                action_type=ActionType.SEARCH,
                description=f"Search for '{query}' using {search_provider}",
                params={"query": query, "provider": search_provider, "max_results": max(5, max_inspect_pages + 2)}
            ))

            # 2. For non-search-only tasks, add page navigation and extraction actions
            if task_type != TaskType.SEARCH_ONLY:
                actions.append(Action(
                    action_type=ActionType.NAVIGATE,
                    description=f"Inspect top {max_inspect_pages} relevant candidate pages",
                    params={"count": max_inspect_pages}
                ))

                actions.append(Action(
                    action_type=ActionType.EXTRACT,
                    description="Extract structured page content, tables, and specifications",
                    params={"max_chars": settings.max_page_chars_to_extract}
                ))

        # Grounded summary & answer generation
        actions.append(Action(
            action_type=ActionType.SUMMARIZE,
            description="Synthesize evidence-grounded final answer with citations",
            params={"task_type": task_type.value}
        ))

        return Plan(
            goal=query,
            task_type=task_type,
            target_websites=target_domains,
            completion_criteria=completion_criteria,
            actions=actions,
            notes=f"Generated plan with {len(actions)} stages for task type: {task_type.value}"
        )

    def _classify_task_type(self, query: str) -> TaskType:
        """Classify user intent into one of the core task types."""
        q = query.lower()
        if any(w in q for w in ["compare", "comparison", "versus", "vs", "which is better"]):
            return TaskType.COMPARISON
        if any(w in q for w in ["extract only", "scrape", "pull data", "dump"]):
            return TaskType.EXTRACTION
        if any(w in q for w in ["just search", "only search", "show links", "find links"]):
            return TaskType.SEARCH_ONLY
        if any(w in q for w in ["navigate to", "open url", "go to"]):
            return TaskType.NAVIGATION
        return TaskType.RESEARCH

    def _extract_target_domains(self, query: str) -> List[str]:
        """Detect any specific target websites referenced in the query."""
        q = query.lower()
        domains = []
        if "amazon" in q:
            domains.append("amazon.in" if "india" in q or "in" in q else "amazon.com")
        if "wikipedia" in q:
            domains.append("wikipedia.org")
        if "google" in q and "search" not in q:
            domains.append("google.com")
        if "bing" in q:
            domains.append("bing.com")

        # Explicit domain patterns (e.g. example.com)
        explicit = re.findall(r"\b([a-z0-9-]+\.(?:com|org|in|edu|gov|net|io))\b", q)
        for dom in explicit:
            if dom not in domains:
                domains.append(dom)

        return domains

    def _select_search_provider(self, target_domains: List[str], query: str) -> str:
        """Choose the optimal search provider for the task."""
        if "amazon.in" in target_domains:
            return "amazon_in"
        if "wikipedia.org" in target_domains:
            return "wikipedia"
        if "bing.com" in target_domains or "bing" in query.lower():
            return "bing"
        if "google.com" in target_domains or "google" in query.lower():
            return "google"
        return settings.default_search_provider

    def _generate_completion_criteria(self, query: str, task_type: TaskType) -> List[str]:
        """Produce concrete verification conditions."""
        criteria = ["Search executed with candidate results returned"]

        if task_type == TaskType.SEARCH_ONLY:
            criteria.append("Search results extracted and ranked")
        elif task_type == TaskType.COMPARISON:
            criteria.extend([
                "At least 2 distinct destination web pages visited",
                "Target features, specifications, or prices extracted",
                "Comparison table or side-by-side contrast produced",
                "Verified sources cited"
            ])
        else:  # RESEARCH
            criteria.extend([
                "At least 1 destination web page visited beyond search results",
                "Substantive article or documentation content extracted",
                "Evidence stored in RAG knowledge store",
                "Answer grounded in retrieved evidence with clickable citations"
            ])

        return criteria
