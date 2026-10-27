"""
Asynchronous background task runner and WebSocket event broadcaster for NEXUS.
Executes autonomous agent tasks in non-blocking worker threads,
streams real-time telemetry events, and coordinates pause, resume, and cancellation.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from agent.agent import AutonomousWebAgent
from agent.task_state import TaskState, TaskStatus
from memory.task_history import TaskHistoryRepository
from config import settings

logger = logging.getLogger("server.task_manager")


class TaskManager:
    """Coordinates background execution of autonomous web browsing tasks."""

    _instance: Optional["TaskManager"] = None

    @classmethod
    def get_instance(cls) -> "TaskManager":
        if cls._instance is None:
            cls._instance = TaskManager()
        return cls._instance

    def __init__(self):
        self.history = TaskHistoryRepository()
        self._active_agents: Dict[str, AutonomousWebAgent] = {}
        self._active_states: Dict[str, TaskState] = {}
        self._listeners: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def register_listener(self, task_id: str) -> asyncio.Queue:
        """Register a new subscriber queue for real-time WebSocket events."""
        async with self._lock:
            if task_id not in self._listeners:
                self._listeners[task_id] = []
            queue = asyncio.Queue(maxsize=100)
            self._listeners[task_id].append(queue)
            return queue

    async def unregister_listener(self, task_id: str, queue: asyncio.Queue) -> None:
        """Remove a subscriber queue when client disconnects."""
        async with self._lock:
            if task_id in self._listeners:
                if queue in self._listeners[task_id]:
                    self._listeners[task_id].remove(queue)
                if not self._listeners[task_id]:
                    del self._listeners[task_id]

    def _broadcast_event(self, task_id: str, event_data: Dict[str, Any]) -> None:
        """Enqueue state update into all active subscriber queues."""
        queues = self._listeners.get(task_id, [])
        for q in list(queues):
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(event_data)
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"Error broadcasting event: {e}")

    async def start_task(
        self,
        query: str,
        start_url: Optional[str] = None,
        max_inspect_pages: int = 3,
        max_depth: int = 2,
        headless: Optional[bool] = None,
        timeout_seconds: Optional[int] = None
    ) -> str:
        """Initialize and launch an agent task in a non-blocking background thread."""
        agent = AutonomousWebAgent(headless=headless if headless is not None else settings.browser_headless)
        
        # Temporary state initialization so task_id is known immediately
        temp_state = TaskState(
            original_query=query,
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_inspect_pages,
            status=TaskStatus.RUNNING
        )
        task_id = temp_state.task_id
        agent.state = temp_state

        async with self._lock:
            self._active_agents[task_id] = agent
            self._active_states[task_id] = temp_state

        # Persist initial state
        try:
            self.history.save_task(temp_state)
        except Exception as e:
            logger.warning(f"Error saving initial task record: {e}")

        # Capture loop for thread-safe event dispatch
        loop = asyncio.get_running_loop()

        def step_callback(state: TaskState):
            # Update memory state
            self._active_states[task_id] = state
            # Save periodic progress
            try:
                self.history.save_task(state)
            except Exception:
                pass

            # Serialize snapshot for WebSocket
            event = {
                "type": "state_update",
                "task_id": state.task_id,
                "status": state.status.value,
                "step_index": state.current_step_index,
                "step_count": state.metrics.step_count,
                "visited_urls": state.visited_urls,
                "evidence_count": len(state.evidence_items),
                "latest_log": state.logs[-1] if state.logs else "",
                "screenshot": state.screenshot_path,
                "timestamp": time.time(),
                "duration": round(state.metrics.total_duration_seconds or (time.time() - state.created_at), 1)
            }
            loop.call_soon_threadsafe(self._broadcast_event, task_id, event)

        def runner():
            try:
                final_state = agent.run_task(
                    query=query,
                    max_inspect_pages=max_inspect_pages,
                    start_url=start_url,
                    max_depth=max_depth,
                    step_callback=step_callback
                )
                return final_state
            except Exception as e:
                logger.error(f"Task {task_id} execution error: {e}", exc_info=True)
                if agent.state:
                    agent.state.status = TaskStatus.FAILED
                    agent.state.log(f"Execution terminated with error: {e}")
                    step_callback(agent.state)
                return agent.state
            finally:
                agent.close()

        # Fire and forget execution in thread pool
        async def background_worker():
            try:
                await asyncio.to_thread(runner)
            finally:
                async with self._lock:
                    if task_id in self._active_agents:
                        del self._active_agents[task_id]
                # Send completion event
                self._broadcast_event(task_id, {"type": "completed", "task_id": task_id})

        asyncio.create_task(background_worker())
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task state from active memory or persistent SQLite."""
        # 1. Check active states first for freshest live telemetry
        if task_id in self._active_states:
            state = self._active_states[task_id]
            data = state.model_dump()
            data["evidence"] = [e.model_dump() for e in state.evidence_items]
            data["verification_report"] = state.verification_report.model_dump() if state.verification_report else None
            data["plan"] = state.plan.model_dump() if state.plan else None
            data["metrics"] = state.metrics.model_dump()
            return data

        # 2. Check SQLite
        return self.history.get_task(task_id)

    def pause_task(self, task_id: str) -> bool:
        """Pause a running agent."""
        agent = self._active_agents.get(task_id)
        if agent:
            agent.pause()
            self._broadcast_event(task_id, {"type": "paused", "task_id": task_id})
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused agent."""
        agent = self._active_agents.get(task_id)
        if agent:
            agent.resume()
            self._broadcast_event(task_id, {"type": "resumed", "task_id": task_id})
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running agent."""
        agent = self._active_agents.get(task_id)
        if agent:
            agent.stop()
            self._broadcast_event(task_id, {"type": "cancelled", "task_id": task_id})
            return True
        return False
