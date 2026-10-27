"""
Self-correction and failure recovery engine.
Diagnoses action failures, formulates alternative recovery strategies,
and manages bounded retries.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from .task_state import Action, ActionType, StepResult, TaskState
from memory.experience_memory import ExperienceMemory
from config import settings

logger = logging.getLogger("agent.self_correction")


class SelfCorrectionEngine:
    """Diagnoses failures and suggests concrete alternative actions."""

    def __init__(self, memory: Optional[ExperienceMemory] = None):
        self.memory = memory or ExperienceMemory()

    def handle_failure(
        self,
        failed_action: Action,
        error_message: str,
        state: TaskState
    ) -> Optional[Action]:
        """
        Evaluate a failed action and return an alternative recovery action if retries remain.
        """
        failed_action.retry_count += 1
        state.metrics.actions_retried += 1

        logger.warning(
            f"Action '{failed_action.description}' failed (Attempt {failed_action.retry_count}/{failed_action.max_retries}): {error_message}"
        )

        # Record failure in experience memory to avoid repetition
        target_domain = failed_action.params.get("url", failed_action.params.get("provider", "general"))
        self.memory.record_experience(
            domain_or_topic=target_domain,
            strategy_type=failed_action.action_type.value,
            outcome="failure",
            details={"error": error_message, "params": failed_action.params}
        )

        if failed_action.retry_count > failed_action.max_retries:
            logger.info(f"Max retries reached for action {failed_action.id}; aborting retry.")
            return None

        # 1. Recovery for SEARCH failure
        if failed_action.action_type == ActionType.SEARCH:
            curr_provider = failed_action.params.get("provider", "duckduckgo")
            query = failed_action.params.get("query", state.original_query)

            # Switch provider fallback
            fallback_provider = "bing" if curr_provider == "duckduckgo" else "duckduckgo"
            # Simplify query
            simplified_query = self._simplify_query(query)

            return Action(
                action_type=ActionType.SEARCH,
                description=f"Retry search with alternative provider '{fallback_provider}' and broadened query",
                params={"query": simplified_query, "provider": fallback_provider, "max_results": 5},
                retry_count=failed_action.retry_count
            )

        # 2. Recovery for NAVIGATE failure
        if failed_action.action_type == ActionType.NAVIGATE:
            failed_url = failed_action.params.get("url", "")
            # Pick next candidate link from search results
            candidate_urls = [
                r["url"] for r in state.search_results
                if r.get("url") and r["url"] not in state.visited_urls and r["url"] != failed_url
            ]

            if candidate_urls:
                next_url = candidate_urls[0]
                return Action(
                    action_type=ActionType.NAVIGATE,
                    description=f"Fallback to alternative candidate URL: {next_url}",
                    params={"url": next_url, "candidate_index": 1},
                    retry_count=failed_action.retry_count
                )
            else:
                # If no more candidates, trigger a broader search
                return Action(
                    action_type=ActionType.SEARCH,
                    description="Expand search query to discover more candidates",
                    params={"query": self._simplify_query(state.original_query), "provider": "duckduckgo"},
                    retry_count=failed_action.retry_count
                )

        # 3. Recovery for EXTRACT failure
        if failed_action.action_type == ActionType.EXTRACT:
            return Action(
                action_type=ActionType.EXTRACT,
                description="Retry extraction with relaxed container selectors",
                params={"fallback_mode": True, "max_chars": settings.max_page_chars_to_extract},
                retry_count=failed_action.retry_count
            )

        return None

    def _simplify_query(self, query: str) -> str:
        """Strip overly specific constraints to broaden search recall."""
        # Remove punctuation
        clean = re.sub(r"[^\w\s]", " ", query)
        words = clean.split()
        # Drop common query verbs
        drop = {"search", "find", "google", "for", "the", "best", "compare", "recommend", "please"}
        core_words = [w for w in words if w.lower() not in drop]
        return " ".join(core_words[:6]) if core_words else query
