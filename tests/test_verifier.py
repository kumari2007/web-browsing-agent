"""
Unit tests for TaskVerifier.
Tests task verification rules, detection of incomplete tasks, and distinction between search and content pages.
"""

from agent.verifier import TaskVerifier
from agent.task_state import TaskState, TaskType, TaskStatus, ExtractedEvidence


def test_verifier_complete_research_task():
    verifier = TaskVerifier()
    state = TaskState(
        original_query="Research Python tutorials",
        task_type=TaskType.RESEARCH,
        visited_urls=["https://duckduckgo.com/html/?q=python", "https://realpython.com/intro/"],
        search_results=[{"title": "Real Python", "url": "https://realpython.com/intro/"}],
        evidence_items=[
            ExtractedEvidence(
                url="https://realpython.com/intro/",
                title="Real Python Intro",
                content="Comprehensive Python guide covering variables, data types, control flow, functions, and modules in great detail. Python is dynamically typed and garbage-collected, designed for readability and elegance with significant indentation. Includes code examples and hands-on exercises for practical mastery.",
                observed_at="2026-10-09 10:00:00 UTC",
                relevance_score=0.9
            )
        ],
        final_answer="According to [Real Python Intro](https://realpython.com/intro/), Python is an accessible language."
    )

    report = verifier.verify_task(state)
    assert report.is_successful is True
    assert report.status_verdict == TaskStatus.COMPLETED
    assert report.confidence_score >= 0.8
    assert len(report.missing_information) == 0


def test_verifier_rejects_search_page_only():
    verifier = TaskVerifier()
    # Task where browser ONLY opened the search page
    state = TaskState(
        original_query="Research quantum computing",
        task_type=TaskType.RESEARCH,
        visited_urls=["https://duckduckgo.com/html/?q=quantum+computing"],
        search_results=[{"title": "Quantum Article", "url": "https://example.com/quantum"}],
        evidence_items=[],
        final_answer=None
    )

    report = verifier.verify_task(state)
    assert report.is_successful is False
    assert report.status_verdict in {TaskStatus.PARTIAL_COMPLETION, TaskStatus.FAILED}
    assert any("destination" in m.lower() for m in report.missing_information)


def test_verifier_comparison_requires_multiple_sources():
    verifier = TaskVerifier()
    # Comparison task with only 1 source visited
    state = TaskState(
        original_query="Compare laptop A and laptop B",
        task_type=TaskType.COMPARISON,
        visited_urls=["https://example.com/laptop-a"],
        search_results=[{"title": "Laptop A", "url": "https://example.com/laptop-a"}],
        evidence_items=[
            ExtractedEvidence(
                url="https://example.com/laptop-a",
                title="Laptop A Details",
                content="Laptop A specifications: 16GB RAM, 512GB SSD.",
                observed_at="2026-10-09 10:00:00 UTC"
            )
        ],
        final_answer="Laptop A has 16GB RAM."
    )

    report = verifier.verify_task(state)
    assert report.is_successful is False
    assert report.status_verdict == TaskStatus.PARTIAL_COMPLETION
    assert any("2 distinct" in m for m in report.missing_information)
