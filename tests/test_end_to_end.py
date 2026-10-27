"""
End-to-end integration and resilience tests.
Runs autonomous agent flow on the local test server, tests self-correction on induced failures,
and verifies maximum step and retry ceilings.
"""

from unittest.mock import patch, MagicMock
from agent.agent import AutonomousWebAgent
from agent.planner import TaskPlanner
from agent.executor import ActionExecutor
from agent.task_state import TaskState, TaskType, TaskStatus, Action, ActionType, StepResult
from agent.self_correction import SelfCorrectionEngine
from browser.playwright_browser import PlaywrightBrowserManager
from browser.navigation import Navigator
from search.search_manager import SearchManager
from search.result_parser import SearchResult
from extraction.page_extractor import PageExtractor
from extraction.structured_extractor import StructuredExtractor
from rag.document_processor import DocumentProcessor
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from safety.url_validator import URLValidator


def test_streamlit_app_import():
    """Verify that app.py imports cleanly without syntax or dependency errors."""
    import app
    assert hasattr(app, "render_header")


def test_self_correction_after_induced_failure():
    """Verify that self-correction recovers by trying next candidate when navigation fails."""
    correction_engine = SelfCorrectionEngine()
    state = TaskState(
        original_query="Find Python courses",
        search_results=[
            {"title": "Broken Course Link", "url": "http://broken.example.com/bad"},
            {"title": "Working Course Link", "url": "http://working.example.com/good"}
        ],
        visited_urls=[]
    )

    failed_action = Action(
        action_type=ActionType.NAVIGATE,
        description="Navigate to broken link",
        params={"url": "http://broken.example.com/bad"}
    )

    # Induce failure
    recovery = correction_engine.handle_failure(
        failed_action=failed_action,
        error_message="DNS lookup failed",
        state=state
    )

    assert recovery is not None
    assert recovery.action_type == ActionType.NAVIGATE
    # Strategy should switch to the alternative candidate link
    assert recovery.params["url"] == "http://working.example.com/good"


def test_maximum_step_ceiling():
    """Verify agent respects step limits and avoids infinite loops."""
    agent = AutonomousWebAgent(headless=True, max_steps=2)

    # Mock planner with 5 actions
    mock_plan = MagicMock()
    mock_plan.task_type = TaskType.SEARCH_ONLY
    mock_plan.actions = [
        Action(action_type=ActionType.SEARCH, description="Step 1"),
        Action(action_type=ActionType.NAVIGATE, description="Step 2"),
        Action(action_type=ActionType.EXTRACT, description="Step 3"),
    ]

    with patch.object(agent.planner, "create_plan", return_value=mock_plan):
        with patch.object(agent.executor, "execute_action", return_value=StepResult(success=True)):
            final_state = agent.run_task(query="Test step ceiling", max_inspect_pages=1)
            assert final_state.metrics.step_count <= 2
            agent.close()


def test_end_to_end_autonomous_flow(test_server, test_url_validator, tmp_path):
    """
    Complete end-to-end test on the local test fixture server:
    Search -> Multi-page Navigation -> Content & Spec Extraction -> Vector Store RAG -> Grounded Answer.
    """
    # 1. Setup local-aware components
    nav = Navigator(url_validator=test_url_validator)
    search_mgr = SearchManager(url_validator=test_url_validator)

    # Mock search_manager.search to return local test server links
    mock_search_results = [
        SearchResult(
            title="Python for Beginners - Free Course",
            url=f"{test_server}/course1",
            snippet="Free interactive tutorials.",
            relevance_score=0.95
        ),
        SearchResult(
            title="Complete Python Bootcamp - Pro",
            url=f"{test_server}/course2",
            snippet="Python bootcamp for ₹3,499.",
            relevance_score=0.90
        )
    ]

    with patch.object(search_mgr, "search", return_value=mock_search_results):
        executor = ActionExecutor(
            navigator=nav,
            search_manager=search_mgr,
            page_extractor=PageExtractor(),
            structured_extractor=StructuredExtractor()
        )

        agent = AutonomousWebAgent(
            headless=True,
            executor=executor
        )

        try:
            state = agent.run_task(
                query="Compare beginner Python courses and prices",
                max_inspect_pages=2
            )

            # Assert complete lifecycle execution
            assert state.status in {TaskStatus.COMPLETED, TaskStatus.PARTIAL_COMPLETION}
            assert len(state.visited_urls) >= 2
            assert len(state.evidence_items) >= 2

            # Assert structured extraction caught prices and specs
            all_prices = [p for e in state.evidence_items for p in e.structured_data.get("prices_found", [])]
            assert any("free" in p.lower() or "0" in p for p in all_prices)
            assert any("3,499" in p for p in all_prices)

            # Assert final answer exists and cites the verified sources
            assert state.final_answer is not None
            assert (f"{test_server}/course1" in state.final_answer) or ("/course1" in state.final_answer)
            assert (f"{test_server}/course2" in state.final_answer) or ("/course2" in state.final_answer)

            # Assert verification audit
            assert state.verification_report is not None
            assert state.verification_report.confidence_score > 0.6
        finally:
            agent.close()
