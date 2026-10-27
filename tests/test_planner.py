"""
Unit tests for TaskPlanner.
Tests natural language parsing, task classification, query decomposition, and criteria generation.
"""

from agent.planner import TaskPlanner
from agent.task_state import TaskType, ActionType


def test_planner_comparison_task():
    planner = TaskPlanner()
    query = "Search Google for the best beginner Python courses, compare features and prices, and recommend one"
    plan = planner.create_plan(query, max_inspect_pages=3)

    assert plan.goal == query
    assert plan.task_type == TaskType.COMPARISON
    assert len(plan.actions) >= 3
    assert plan.actions[0].action_type == ActionType.SEARCH
    assert plan.actions[1].action_type == ActionType.NAVIGATE
    assert plan.actions[-1].action_type == ActionType.SUMMARIZE
    assert any("compare" in c.lower() or "comparison" in c.lower() for c in plan.completion_criteria)


def test_planner_search_only_task():
    planner = TaskPlanner()
    query = "Just search duckduckgo for recent AI news and show links"
    plan = planner.create_plan(query)

    assert plan.task_type == TaskType.SEARCH_ONLY
    # Search only does not require deep navigation actions
    assert len(plan.actions) == 2
    assert plan.actions[0].action_type == ActionType.SEARCH
    assert plan.actions[1].action_type == ActionType.SUMMARIZE


def test_planner_domain_detection_amazon():
    planner = TaskPlanner()
    query = "Search Amazon India for laptops under ₹50,000 and compare RAM"
    plan = planner.create_plan(query)

    assert "amazon.in" in plan.target_websites
    assert plan.actions[0].params["provider"] == "amazon_in"


def test_planner_domain_detection_wikipedia():
    planner = TaskPlanner()
    query = "Search Wikipedia for Quantum Computing and summarize"
    plan = planner.create_plan(query)

    assert "wikipedia.org" in plan.target_websites
    assert plan.actions[0].params["provider"] == "wikipedia"
