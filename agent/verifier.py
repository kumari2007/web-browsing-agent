"""
Task verification engine.
Validates completion criteria, distinguishes search pages from actual destination pages,
verifies evidence sufficiency, and flags partial completions with honest limitations.
"""

from typing import List, Dict, Any, Optional
from .task_state import TaskState, TaskType, TaskStatus, VerificationReport


class TaskVerifier:
    """Verifies whether an autonomous task successfully satisfied its completion criteria."""

    def verify_task(self, state: TaskState) -> VerificationReport:
        """Evaluate task state and produce an evidence-based completion audit."""
        reasons: List[str] = []
        missing: List[str] = []
        limitations: List[str] = []

        task_type = state.task_type
        visited_pages = state.visited_urls
        evidence_items = state.evidence_items
        has_final_answer = bool(state.final_answer and len(state.final_answer.strip()) > 50)

        # 1. Search Results Check
        if not state.search_results and task_type != TaskType.NAVIGATION:
            missing.append("No search results were discovered.")

        # 2. Page Navigation Verification (Must visit destination beyond search page)
        non_search_visited = [
            u for u in visited_pages
            if not self._is_search_page_url(u)
        ]

        if task_type in {TaskType.RESEARCH, TaskType.COMPARISON, TaskType.EXTRACTION}:
            if not non_search_visited:
                missing.append("Failed to visit any actual destination web page (remained on search page).")
            else:
                reasons.append(f"Successfully visited {len(non_search_visited)} destination web pages.")

        # 3. Task-specific Evidence Depth
        if task_type == TaskType.COMPARISON:
            if len(non_search_visited) < 2 and len(evidence_items) < 2:
                missing.append("Comparison task requires inspecting at least 2 distinct sources/products.")
                limitations.append("Only partial comparative data was collected.")

        # 4. Content Volume Check
        total_evidence_chars = sum(len(e.content) for e in evidence_items)
        if task_type in {TaskType.RESEARCH, TaskType.COMPARISON} and total_evidence_chars < 120:
            missing.append("Insufficient textual evidence extracted from destination pages.")

        # 5. Final Answer Check
        if not has_final_answer and task_type != TaskType.SEARCH_ONLY:
            missing.append("No evidence-based final answer was synthesized.")

        # Compute Evidence Coverage & Confidence Score
        score = 0.0
        if state.search_results:
            score += 0.25
        if non_search_visited:
            score += 0.35
        if evidence_items and total_evidence_chars >= 100:
            score += 0.25
        if has_final_answer:
            score += 0.15

        confidence_score = round(min(1.0, score), 2)
        coverage_score = round(min(1.0, len(evidence_items) / max(1, len(non_search_visited) or 1)), 2)

        # Decide Verdict
        if not missing:
            reasons.append("All primary completion criteria satisfied.")
            return VerificationReport(
                is_successful=True,
                confidence_score=confidence_score,
                evidence_coverage=coverage_score,
                reasons=reasons,
                missing_information=[],
                limitations=limitations,
                status_verdict=TaskStatus.COMPLETED
            )
        elif non_search_visited or evidence_items or state.search_results:
            limitations.append("Task partially completed within available browser/network constraints.")
            return VerificationReport(
                is_successful=False,
                confidence_score=confidence_score,
                evidence_coverage=coverage_score,
                reasons=reasons,
                missing_information=missing,
                limitations=limitations,
                status_verdict=TaskStatus.PARTIAL_COMPLETION
            )
        else:
            return VerificationReport(
                is_successful=False,
                confidence_score=0.0,
                evidence_coverage=0.0,
                reasons=[],
                missing_information=missing,
                limitations=["No meaningful research progress could be achieved."],
                status_verdict=TaskStatus.FAILED
            )

    def _is_search_page_url(self, url: str) -> bool:
        """Check if URL points to a search engine query page."""
        u = url.lower()
        return any(k in u for k in [
            "duckduckgo.com", "google.com/search", "bing.com/search",
            "special:search", "amazon.in/s?", "amazon.com/s?"
        ])
