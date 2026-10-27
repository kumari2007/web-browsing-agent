"""
Analytics and performance monitoring API endpoints.
Provides real-time aggregations of durations, success rates, recovery rates, and verification metrics.
"""

from fastapi import APIRouter
from memory.task_history import TaskHistoryRepository

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])
history_repo = TaskHistoryRepository()


@router.get("")
async def get_metrics():
    """Compute and retrieve comprehensive system analytics and execution trends."""
    return history_repo.get_metrics_summary()
