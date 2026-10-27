"""
Structured domain models and state tracking for autonomous task execution.
Preserves goals, execution trajectories, visited states, extracted evidence, and metrics.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import time
import uuid
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SEARCH_ONLY = "SEARCH_ONLY"
    RESEARCH = "RESEARCH"
    COMPARISON = "COMPARISON"
    NAVIGATION = "NAVIGATION"
    EXTRACTION = "EXTRACTION"
    GENERAL = "GENERAL"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED_FOR_INTERVENTION = "PAUSED_FOR_INTERVENTION"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    PARTIAL_COMPLETION = "PARTIAL_COMPLETION"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActionType(str, Enum):
    SEARCH = "SEARCH"
    NAVIGATE = "NAVIGATE"
    EXTRACT = "EXTRACT"
    CLICK = "CLICK"
    FILL = "FILL"
    WAIT = "WAIT"
    SCREENSHOT = "SCREENSHOT"
    SUMMARIZE = "SUMMARIZE"
    SELF_CORRECT = "SELF_CORRECT"


class StepResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    notes: str = ""
    timestamp: float = Field(default_factory=time.time)


class Action(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: ActionType
    description: str
    params: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, RETRIED
    result: Optional[StepResult] = None
    retry_count: int = 0
    max_retries: int = 2


class Plan(BaseModel):
    goal: str
    task_type: TaskType
    target_websites: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)
    notes: str = ""


class ExtractedEvidence(BaseModel):
    url: str
    title: str
    content: str
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    observed_at: str
    relevance_score: float = 0.0
    source_quality: str = "web"


class VerificationReport(BaseModel):
    is_successful: bool
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    status_verdict: TaskStatus = TaskStatus.COMPLETED


class PerformanceMetrics(BaseModel):
    total_duration_seconds: float = 0.0
    search_duration_seconds: float = 0.0
    navigation_duration_seconds: float = 0.0
    extraction_duration_seconds: float = 0.0
    rag_duration_seconds: float = 0.0
    llm_duration_seconds: float = 0.0
    step_count: int = 0
    pages_visited: int = 0
    actions_retried: int = 0


class TaskState(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str
    start_url: Optional[str] = None
    max_depth: int = 2
    max_pages: int = 5
    plan: Optional[Plan] = None
    task_type: TaskType = TaskType.RESEARCH
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    visited_urls: List[str] = Field(default_factory=list)
    search_results: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[ExtractedEvidence] = Field(default_factory=list)
    extracted_records: List[Dict[str, Any]] = Field(default_factory=list)
    navigation_graph: List[Dict[str, Any]] = Field(default_factory=list)
    interventions: List[Dict[str, Any]] = Field(default_factory=list)
    action_history: List[Action] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    final_answer: Optional[str] = None
    verification_report: Optional[VerificationReport] = None
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    screenshot_path: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def log(self, message: str) -> None:
        """Append a timestamped log entry."""
        timestamp_str = time.strftime("%H:%M:%S")
        entry = f"[{timestamp_str}] {message}"
        self.logs.append(entry)
        self.updated_at = time.time()

    def add_visited_url(self, url: str) -> None:
        if url and url not in self.visited_urls:
            self.visited_urls.append(url)
            self.metrics.pages_visited = len(self.visited_urls)

    def add_nav_edge(self, from_url: str, to_url: str, depth: int, reason: str = "") -> None:
        self.navigation_graph.append({
            "from_url": from_url,
            "to_url": to_url,
            "depth": depth,
            "reason": reason,
            "timestamp": time.time()
        })

    def is_finished(self) -> bool:
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.PARTIAL_COMPLETION,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        }
