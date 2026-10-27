"""
Task management API endpoints.
Provides task creation, listing, status inspection, pause/resume/cancel controls,
result retrieval, evidence inspection, structured export (JSON/CSV), and WebSocket streaming.
"""

import csv
import io
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Query
from pydantic import BaseModel, Field
from server.task_manager import TaskManager
from memory.task_history import TaskHistoryRepository

logger = logging.getLogger("server.routes.tasks")

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
task_manager = TaskManager.get_instance()
history_repo = TaskHistoryRepository()


class CreateTaskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Natural-language task or research goal")
    start_url: Optional[str] = Field(None, description="Optional starting URL")
    max_inspect_pages: int = Field(default=3, ge=1, le=15, description="Maximum pages to visit")
    max_depth: int = Field(default=2, ge=1, le=5, description="Maximum link crawl depth")
    headless: Optional[bool] = Field(default=None, description="Run browser in headless mode")
    risk_preference: Optional[str] = Field(default="READ_ONLY", description="READ_ONLY or CONFIRM_CONSEQUENTIAL")
    extraction_fields: Optional[List[str]] = Field(default=None, description="Optional custom extraction keys")


@router.post("", status_code=201)
async def create_task(req: CreateTaskRequest):
    """Create and immediately dispatch an autonomous web browsing task."""
    try:
        task_id = await task_manager.start_task(
            query=req.query,
            start_url=req.start_url,
            max_inspect_pages=req.max_inspect_pages,
            max_depth=req.max_depth,
            headless=req.headless
        )
        return {
            "task_id": task_id,
            "status": "RUNNING",
            "message": "Task launched successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_tasks(limit: int = Query(default=50, ge=1, le=200)):
    """List recent tasks with execution metrics."""
    return history_repo.list_recent_tasks(limit=limit)


@router.get("/{task_id}")
async def get_task_details(task_id: str):
    """Retrieve complete execution trajectory and state for a single task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@router.post("/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause an active agent."""
    success = task_manager.pause_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause: task is not active or already finished")
    return {"status": "PAUSED", "task_id": task_id}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused agent."""
    success = task_manager.resume_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume: task is not paused or not found")
    return {"status": "RUNNING", "task_id": task_id}


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Gracefully cancel a running agent task."""
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel: task is not currently active")
    return {"status": "CANCELLED", "task_id": task_id}


@router.get("/{task_id}/events")
async def get_task_events(task_id: str):
    """Retrieve logs and action event history for a task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task_id,
        "status": task.get("status"),
        "logs": task.get("logs", []),
        "actions": task.get("action_history", []),
        "interventions": task.get("interventions", [])
    }


@router.get("/{task_id}/results")
async def get_task_results(task_id: str):
    """Retrieve final grounded answer, verification checklist, and structured records."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task_id,
        "query": task.get("query") or task.get("original_query"),
        "status": task.get("status"),
        "final_answer": task.get("final_answer"),
        "verification_report": task.get("verification_report"),
        "extracted_records": task.get("extracted_records", []),
        "evidence_count": len(task.get("evidence", [])),
        "visited_urls": task.get("visited_urls", [])
    }


@router.get("/{task_id}/evidence")
async def get_task_evidence(task_id: str):
    """Retrieve extracted snippets and citation provenance."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task_id,
        "evidence": task.get("evidence", []),
        "navigation_graph": task.get("navigation_graph", [])
    }


@router.get("/{task_id}/export/{export_format}")
async def export_task_data(task_id: str, export_format: str):
    """Export task results and extracted data in JSON or CSV format."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    fmt = export_format.lower().strip()
    if fmt == "json":
        export_payload = {
            "task_id": task_id,
            "query": task.get("query") or task.get("original_query"),
            "status": task.get("status"),
            "final_answer": task.get("final_answer"),
            "verification_report": task.get("verification_report"),
            "metrics": task.get("metrics"),
            "visited_urls": task.get("visited_urls"),
            "extracted_records": task.get("extracted_records", []),
            "evidence": task.get("evidence", [])
        }
        content = json.dumps(export_payload, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=nexus_task_{task_id[:8]}.json"}
        )

    elif fmt == "csv":
        records = task.get("extracted_records", [])
        if not records:
            # Fallback to evidence rows if no custom records
            evidence = task.get("evidence", [])
            records = [{"url": e.get("url"), "title": e.get("title"), "relevance": e.get("relevance_score")} for e in evidence]

        if not records:
            records = [{"info": "No structured records extracted for this task"}]

        # Collect union of all headers
        headers = []
        for r in records:
            for k in r.keys():
                if k not in headers:
                    headers.append(k)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=nexus_task_{task_id[:8]}.csv"}
        )

    else:
        raise HTTPException(status_code=400, detail="Unsupported export format. Use 'json' or 'csv'")


@router.websocket("/{task_id}/ws")
async def task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for high-frequency live agent telemetry and screenshots."""
    await websocket.accept()
    queue = await task_manager.register_listener(task_id)

    # Send initial snapshot immediately upon connect
    initial = task_manager.get_task(task_id)
    if initial:
        await websocket.send_json({
            "type": "initial_state",
            "task_id": task_id,
            "status": initial.get("status"),
            "visited_urls": initial.get("visited_urls", []),
            "step_count": initial.get("metrics", {}).get("step_count", 0),
            "logs": initial.get("logs", [])
        })

    try:
        while True:
            # Wait for next broadcast event
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("type") in {"completed", "cancelled"}:
                break
    except WebSocketDisconnect:
        logger.debug(f"Client disconnected from WebSocket for task {task_id}")
    except Exception as e:
        logger.debug(f"WebSocket connection error on task {task_id}: {e}")
    finally:
        await task_manager.unregister_listener(task_id, queue)
