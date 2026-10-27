"""
Action execution engine.
Executes individual planned actions against browser, search, extraction, and RAG subsystems.
Enforces safety gates and records execution telemetry.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page
from .task_state import Action, ActionType, StepResult, TaskState, ExtractedEvidence
from browser.navigation import Navigator, NavigationResult
from search.search_manager import SearchManager
from extraction.page_extractor import PageExtractor, ExtractedPage
from extraction.structured_extractor import StructuredExtractor
from rag.document_processor import DocumentProcessor
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from safety.risk_assessor import RiskAssessor, RiskLevel
from memory.experience_memory import ExperienceMemory
from config import settings

logger = logging.getLogger("agent.executor")


class ActionExecutor:
    """Dispatches and executes actions against system subsystems."""

    def __init__(
        self,
        navigator: Optional[Navigator] = None,
        search_manager: Optional[SearchManager] = None,
        page_extractor: Optional[PageExtractor] = None,
        structured_extractor: Optional[StructuredExtractor] = None,
        doc_processor: Optional[DocumentProcessor] = None,
        retriever: Optional[HybridRetriever] = None,
        answer_generator: Optional[AnswerGenerator] = None,
        risk_assessor: Optional[RiskAssessor] = None,
        experience_memory: Optional[ExperienceMemory] = None
    ):
        self.navigator = navigator or Navigator()
        self.search_manager = search_manager or SearchManager()
        self.page_extractor = page_extractor or PageExtractor()
        self.structured_extractor = structured_extractor or StructuredExtractor()
        self.doc_processor = doc_processor or DocumentProcessor()
        self.retriever = retriever or HybridRetriever()
        self.answer_generator = answer_generator or AnswerGenerator()
        self.risk_assessor = risk_assessor or RiskAssessor(
            read_only_mode=settings.read_only_mode,
            require_confirmation_for_high=settings.require_human_confirmation_on_high_risk
        )
        self.memory = experience_memory or ExperienceMemory()

    def execute_action(self, action: Action, page: Page, state: TaskState) -> StepResult:
        """Execute a single planned action and update task state."""
        start_time = time.time()
        action_type = action.action_type
        params = action.params

        # 1. Safety & Risk Assessment
        risk = self.risk_assessor.assess_action(action_type.value, params)
        if risk.level == RiskLevel.HIGH and risk.requires_confirmation:
            return StepResult(
                success=False,
                error=f"Safety policy requires confirmation for high-risk action: {risk.reason}",
                duration_seconds=time.time() - start_time
            )

        try:
            if action_type == ActionType.SEARCH:
                return self._execute_search(action, page, state, start_time)
            elif action_type == ActionType.NAVIGATE:
                return self._execute_navigate(action, page, state, start_time)
            elif action_type == ActionType.EXTRACT:
                return self._execute_extract(action, page, state, start_time)
            elif action_type == ActionType.SUMMARIZE:
                return self._execute_summarize(action, state, start_time)
            else:
                return StepResult(
                    success=False,
                    error=f"Unsupported action type: {action_type}",
                    duration_seconds=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"Execution error on action '{action.description}': {e}", exc_info=True)
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def _execute_search(self, action: Action, page: Page, state: TaskState, start_time: float) -> StepResult:
        query = action.params.get("query", state.original_query)
        provider = action.params.get("provider", "duckduckgo")
        max_results = action.params.get("max_results", 5)

        state.log(f"Executing search: '{query}' via {provider}")
        results = self.search_manager.search(
            query=query,
            provider_name=provider,
            max_results=max_results,
            page=page
        )

        state.metrics.search_duration_seconds += (time.time() - start_time)

        if not results:
            return StepResult(
                success=False,
                error=f"No results returned for query '{query}' by provider '{provider}'",
                duration_seconds=time.time() - start_time
            )

        # Store candidate results
        state.search_results = [r.model_dump() for r in results]
        state.log(f"Retrieved {len(results)} candidate results.")

        return StepResult(
            success=True,
            data={"count": len(results), "top_url": results[0].url},
            duration_seconds=time.time() - start_time,
            notes=f"Found {len(results)} ranked links"
        )

    def _execute_navigate(self, action: Action, page: Page, state: TaskState, start_time: float) -> StepResult:
        target_count = action.params.get("count", 2)
        explicit_url = action.params.get("url")
        use_discovered = action.params.get("use_discovered_links", False)
        depth = action.params.get("depth", 1)

        urls_to_visit = []
        if explicit_url:
            urls_to_visit.append(explicit_url)
        elif use_discovered and page:
            # Discover links on current page for deep navigation
            discovered = self.navigator.extract_candidate_links(page, page.url or "")
            for item in discovered:
                link_url = item["url"]
                if link_url not in state.visited_urls:
                    urls_to_visit.append(link_url)
                if len(urls_to_visit) >= target_count:
                    break
        else:
            for item in state.search_results:
                candidate = item.get("url")
                if candidate and candidate not in state.visited_urls:
                    urls_to_visit.append(candidate)
                if len(urls_to_visit) >= target_count:
                    break

        # Fallback to discovered links if no search results left
        if not urls_to_visit and page:
            discovered = self.navigator.extract_candidate_links(page, page.url or "")
            for item in discovered:
                link_url = item["url"]
                if link_url not in state.visited_urls:
                    urls_to_visit.append(link_url)
                if len(urls_to_visit) >= target_count:
                    break

        if not urls_to_visit:
            return StepResult(
                success=False,
                error="No valid unvisited URLs available to navigate to",
                duration_seconds=time.time() - start_time
            )

        visited_count = 0
        from_url = page.url if page else "entry"

        for url in urls_to_visit:
            state.log(f"Navigating to destination: {url}")
            nav_result = self.navigator.navigate_to(page, url)
            state.metrics.navigation_duration_seconds += nav_result.elapsed_seconds

            state.add_nav_edge(
                from_url=from_url,
                to_url=url,
                depth=depth,
                reason="Candidate page inspection"
            )

            # Check obstacle
            if nav_result.obstacle and nav_result.obstacle.value != "NONE":
                state.interventions.append({
                    "obstacle": nav_result.obstacle.value,
                    "url": nav_result.url,
                    "timestamp": time.time(),
                    "resolved": False
                })

            if nav_result.success:
                state.add_visited_url(nav_result.url)
                visited_count += 1
                from_url = nav_result.url

                # Automatically extract content upon page load
                ext_start = time.time()
                extracted = self.page_extractor.extract(
                    html_content=nav_result.html_content,
                    url=nav_result.url,
                    fallback_title=nav_result.title
                )
                structured = self.structured_extractor.extract_structured_facts(
                    text=extracted.clean_text,
                    html_content=nav_result.html_content
                )
                state.metrics.extraction_duration_seconds += (time.time() - ext_start)

                if structured:
                    record_item = {
                        "url": nav_result.url,
                        "title": extracted.title or nav_result.title,
                        **structured
                    }
                    state.extracted_records.append(record_item)

                if extracted.clean_text:
                    evidence_obj = ExtractedEvidence(
                        url=nav_result.url,
                        title=extracted.title or nav_result.title,
                        content=extracted.clean_text,
                        structured_data=structured,
                        observed_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                        relevance_score=0.85
                    )
                    state.evidence_items.append(evidence_obj)

                    # Index into RAG vector store
                    rag_start = time.time()
                    task_coll = f"task_{state.task_id}"
                    chunks = self.doc_processor.process_and_index_page(extracted, collection_name=task_coll)
                    state.metrics.rag_duration_seconds += (time.time() - rag_start)
                    state.log(f"Extracted {len(extracted.clean_text)} chars and indexed {len(chunks)} chunks from {url}")

                    # Record success in memory
                    self.memory.record_experience(
                        domain_or_topic=url,
                        strategy_type="navigation_extraction",
                        outcome="success",
                        details={"chars": len(extracted.clean_text), "chunks": len(chunks)}
                    )
            else:
                state.log(f"Failed to navigate to {url}: {nav_result.error_message}")
                self.memory.record_experience(
                    domain_or_topic=url,
                    strategy_type="navigation_failure",
                    outcome="failure",
                    details={"error": nav_result.error_message}
                )

        if visited_count > 0:
            return StepResult(
                success=True,
                data={"visited": visited_count},
                duration_seconds=time.time() - start_time,
                notes=f"Successfully visited and extracted from {visited_count} pages"
            )
        else:
            return StepResult(
                success=False,
                error="Could not visit any of the target candidate pages",
                duration_seconds=time.time() - start_time
            )

    def _execute_extract(self, action: Action, page: Page, state: TaskState, start_time: float) -> StepResult:
        # Check if already extracted during navigation
        if state.evidence_items:
            return StepResult(
                success=True,
                data={"evidence_items_count": len(state.evidence_items)},
                duration_seconds=time.time() - start_time,
                notes="Content already extracted and indexed"
            )

        html = page.content()
        extracted = self.page_extractor.extract(html, page.url, page.title())
        structured = self.structured_extractor.extract_structured_facts(extracted.clean_text, html)

        evidence_obj = ExtractedEvidence(
            url=page.url,
            title=extracted.title,
            content=extracted.clean_text,
            structured_data=structured,
            observed_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            relevance_score=0.8
        )
        state.evidence_items.append(evidence_obj)
        self.doc_processor.process_and_index_page(extracted, collection_name=f"task_{state.task_id}")

        return StepResult(
            success=True,
            data={"chars": len(extracted.clean_text)},
            duration_seconds=time.time() - start_time
        )

    def _execute_summarize(self, action: Action, state: TaskState, start_time: float) -> StepResult:
        state.log("Synthesizing final evidence-grounded answer...")
        ret_start = time.time()
        task_coll = f"task_{state.task_id}"
        retrieved_chunks = self.retriever.retrieve(
            query=state.original_query,
            top_k=settings.rag_top_k,
            collection_name=task_coll
        )
        # Fallback to default if task collection had no hits
        if not retrieved_chunks:
            retrieved_chunks = self.retriever.retrieve(query=state.original_query, top_k=settings.rag_top_k)

        state.metrics.rag_duration_seconds += (time.time() - ret_start)

        llm_start = time.time()
        answer = self.answer_generator.generate_answer(
            query=state.original_query,
            evidence=retrieved_chunks
        )
        state.metrics.llm_duration_seconds += (time.time() - llm_start)
        state.final_answer = answer
        state.log("Completed grounded answer synthesis.")

        return StepResult(
            success=True,
            data={"answer_length": len(answer), "chunks_used": len(retrieved_chunks)},
            duration_seconds=time.time() - start_time
        )
