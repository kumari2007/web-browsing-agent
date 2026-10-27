"""
Master Autonomous Web Browsing Agent orchestrator.
Sequences the complete lifecycle: planning, search, navigation, extraction, RAG, verification, and recovery.
"""

import time
import logging
from typing import Optional, Callable, Dict, Any
from .task_state import TaskState, TaskStatus, Action, StepResult
from .planner import TaskPlanner
from .executor import ActionExecutor
from .observer import Observer
from .verifier import TaskVerifier
from .self_correction import SelfCorrectionEngine
from browser.playwright_browser import PlaywrightBrowserManager
from memory.task_history import TaskHistoryRepository
from memory.experience_memory import ExperienceMemory
from safety.human_intervention import HumanInterventionManager, ObstacleType
from config import settings

logger = logging.getLogger("agent.core")


class AutonomousWebAgent:
    """End-to-end autonomous research and browser automation agent."""

    def __init__(
        self,
        headless: Optional[bool] = None,
        max_steps: Optional[int] = None,
        planner: Optional[TaskPlanner] = None,
        executor: Optional[ActionExecutor] = None,
        observer: Optional[Observer] = None,
        verifier: Optional[TaskVerifier] = None,
        self_correction: Optional[SelfCorrectionEngine] = None,
        browser_manager: Optional[PlaywrightBrowserManager] = None
    ):
        self.headless = headless if headless is not None else settings.browser_headless
        self.max_steps = max_steps or settings.max_task_steps

        self.browser_manager = browser_manager or PlaywrightBrowserManager(headless=self.headless)
        self.planner = planner or TaskPlanner()
        self.executor = executor or ActionExecutor()
        self.observer = observer or Observer()
        self.verifier = verifier or TaskVerifier()
        self.self_correction = self_correction or SelfCorrectionEngine()
        self.history = TaskHistoryRepository()
        self.memory = ExperienceMemory()
        self.intervention = HumanInterventionManager()

        self.state: Optional[TaskState] = None
        self._is_stopped = False
        self._is_paused = False

    def pause(self) -> None:
        """Pause agent execution loop."""
        self._is_paused = True
        if self.state:
            self.state.log("Task paused by user.")

    def resume(self) -> None:
        """Resume agent execution loop."""
        self._is_paused = False
        if self.state:
            self.state.log("Task resumed.")

    def run_task(
        self,
        query: str,
        max_inspect_pages: int = 3,
        start_url: Optional[str] = None,
        max_depth: int = 2,
        step_callback: Optional[Callable[[TaskState], None]] = None
    ) -> TaskState:
        """
        Execute an autonomous task from natural-language instructions to verified conclusion.
        """
        start_time = time.time()
        self._is_stopped = False
        self._is_paused = False

        # 1. Initialize State and Plan
        self.state = TaskState(
            original_query=query,
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_inspect_pages,
            status=TaskStatus.RUNNING
        )
        self.state.log(f"Received user task: '{query}'")
        if start_url:
            self.state.log(f"Starting destination URL provided: '{start_url}' (max depth {max_depth})")

        if step_callback:
            step_callback(self.state)

        # 2. Formulate Plan
        self.state.log("Formulating execution plan...")
        plan = self.planner.create_plan(
            query=query,
            max_inspect_pages=max_inspect_pages,
            start_url=start_url,
            max_depth=max_depth
        )
        self.state.plan = plan
        self.state.task_type = plan.task_type
        self.state.log(f"Classified task as {plan.task_type.value}. Formulated {len(plan.actions)} actions.")

        if step_callback:
            step_callback(self.state)

        # 3. Launch or Connect Browser
        page = None
        try:
            page = self.browser_manager.start()
        except Exception as e:
            self.state.log(f"Browser initialization error: {e}")
            self.state.status = TaskStatus.FAILED
            return self._finalize_task(start_time, step_callback)

        # 4. Action Execution Loop
        action_index = 0
        while action_index < len(plan.actions) and not self._is_stopped:
            # Handle user pause
            while self._is_paused and not self._is_stopped:
                time.sleep(0.5)

            if self._is_stopped:
                break

            if self.state.metrics.step_count >= self.max_steps:
                self.state.log("Reached maximum task step ceiling. Transitioning to verification.")
                break

            action = plan.actions[action_index]
            self.state.current_step_index = action_index
            self.state.metrics.step_count += 1
            action.status = "RUNNING"
            self.state.log(f"Step {self.state.metrics.step_count}: {action.description}")

            if step_callback:
                step_callback(self.state)

            # Execute Action
            result = self.executor.execute_action(action, page, self.state)
            action.result = result

            # Capture diagnostic screenshot if page is alive
            try:
                if page and not page.is_closed():
                    ss_name = f"task_{self.state.task_id[:8]}_step_{action_index+1}.png"
                    ss_path = self.browser_manager.screenshots_dir / ss_name
                    page.screenshot(path=str(ss_path), full_page=False)
                    self.state.screenshot_path = ss_name
            except Exception:
                pass

            if result.success:
                action.status = "SUCCESS"
                self.state.action_history.append(action)
                action_index += 1
            else:
                action.status = "FAILED"
                self.state.log(f"Action failed: {result.error}")
                # Trigger Self-Correction
                recovery_action = self.self_correction.handle_failure(
                    failed_action=action,
                    error_message=result.error or "Unknown failure",
                    state=self.state
                )

                if recovery_action:
                    self.state.log(f"Self-correction triggered: {recovery_action.description}")
                    # Insert recovery action into plan immediately following current action
                    plan.actions.insert(action_index + 1, recovery_action)
                    action_index += 1
                else:
                    self.state.log(f"No further self-correction available for action {action.id}; advancing.")
                    action_index += 1

            if step_callback:
                step_callback(self.state)

        # 5. Verification Phase
        if not self._is_stopped:
            self.state.status = TaskStatus.VERIFYING
            self.state.log("Verifying task completion against criteria...")
            verification = self.verifier.verify_task(self.state)
            self.state.verification_report = verification
            self.state.status = verification.status_verdict
            self.state.log(f"Verification complete: {verification.status_verdict.value} (Confidence: {verification.confidence_score})")

        return self._finalize_task(start_time, step_callback)

    def stop(self) -> None:
        """Signal the agent to gracefully cancel execution."""
        self._is_stopped = True
        if self.state:
            self.state.status = TaskStatus.CANCELLED
            self.state.log("Task cancellation requested by user.")

    def close(self) -> None:
        """Tear down browser resources."""
        self.browser_manager.close()

    def _finalize_task(
        self,
        start_time: float,
        step_callback: Optional[Callable[[TaskState], None]]
    ) -> TaskState:
        """Finalize metrics, persist trajectory, and invoke callback."""
        if self.state:
            self.state.metrics.total_duration_seconds = round(time.time() - start_time, 2)
            self.state.updated_at = time.time()
            # Persist in SQLite history
            try:
                self.history.save_task(self.state)
            except Exception as e:
                logger.warning(f"Could not save task history: {e}")

            if step_callback:
                step_callback(self.state)

        return self.state
