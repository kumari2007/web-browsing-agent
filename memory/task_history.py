"""
Persistent task history repository in SQLite.
Records complete trajectory details, metrics, and outcomes for observability and post-task audit.
Computes system-level analytics and performance summaries.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from agent.task_state import TaskState
from config import settings

logger = logging.getLogger("agent.memory.history")


class TaskHistoryRepository:
    """Stores full task trajectories and analytics in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize task history table schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    task_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    start_url TEXT,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    final_answer TEXT,
                    visited_urls_json TEXT,
                    metrics_json TEXT,
                    plan_json TEXT,
                    evidence_json TEXT,
                    extracted_records_json TEXT,
                    navigation_graph_json TEXT,
                    interventions_json TEXT,
                    logs_json TEXT,
                    verification_report_json TEXT,
                    screenshot_path TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_created ON task_history(created_at DESC)")
            conn.commit()

            # Ensure any new columns exist for existing databases
            self._ensure_columns(conn)

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(task_history)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        new_cols = {
            "start_url": "TEXT",
            "plan_json": "TEXT",
            "evidence_json": "TEXT",
            "extracted_records_json": "TEXT",
            "navigation_graph_json": "TEXT",
            "interventions_json": "TEXT",
            "logs_json": "TEXT",
            "verification_report_json": "TEXT",
            "screenshot_path": "TEXT"
        }
        for col, col_type in new_cols.items():
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE task_history ADD COLUMN {col} {col_type}")
                except Exception as e:
                    logger.debug(f"Column {col} already present or error: {e}")
        conn.commit()

    def save_task(self, state: TaskState) -> None:
        """Persist or update full task execution state."""
        visited_json = json.dumps(state.visited_urls)
        metrics_json = json.dumps(state.metrics.model_dump())
        plan_json = json.dumps(state.plan.model_dump()) if state.plan else "{}"
        evidence_json = json.dumps([e.model_dump() for e in state.evidence_items])
        extracted_records_json = json.dumps(state.extracted_records)
        navigation_graph_json = json.dumps(state.navigation_graph)
        interventions_json = json.dumps(state.interventions)
        logs_json = json.dumps(state.logs)
        verification_report_json = (
            json.dumps(state.verification_report.model_dump())
            if state.verification_report
            else "{}"
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO task_history
                (task_id, query, start_url, task_type, status, final_answer,
                 visited_urls_json, metrics_json, plan_json, evidence_json,
                 extracted_records_json, navigation_graph_json, interventions_json,
                 logs_json, verification_report_json, screenshot_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state.task_id,
                state.original_query,
                state.start_url or "",
                state.task_type.value,
                state.status.value,
                state.final_answer or "",
                visited_json,
                metrics_json,
                plan_json,
                evidence_json,
                extracted_records_json,
                navigation_graph_json,
                interventions_json,
                logs_json,
                verification_report_json,
                state.screenshot_path or "",
                state.created_at,
                state.updated_at
            ))
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details for a single task."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_history WHERE task_id = ?
            """, (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._format_row(row)

    def list_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch list of recent tasks for UI rendering."""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            for row in cursor.fetchall():
                results.append(self._format_row(row))
        return results

    def delete_task(self, task_id: str) -> bool:
        """Delete a single task record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_history(self) -> None:
        """Clear all stored task history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM task_history")
            conn.commit()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Compute aggregated metrics across all recorded tasks."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_history ORDER BY created_at DESC")
            rows = cursor.fetchall()

        total = len(rows)
        if total == 0:
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "partial_tasks": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "total_pages_visited": 0,
                "avg_pages_per_task": 0.0,
                "total_retries": 0,
                "recovery_rate": 0.0,
                "evidence_coverage_avg": 0.0,
                "verification_pass_rate": 0.0,
                "captcha_count": 0,
                "recent_trends": [],
                "task_types": {}
            }

        successful = 0
        failed = 0
        partial = 0
        total_duration = 0.0
        total_pages = 0
        total_retries = 0
        total_evidence_coverage = 0.0
        verification_passed = 0
        captcha_count = 0
        task_types = {}
        daily_trends = {}

        for row in rows:
            data = self._format_row(row)
            status = data.get("status")
            ttype = data.get("task_type", "RESEARCH")
            task_types[ttype] = task_types.get(ttype, 0) + 1

            if status == "COMPLETED":
                successful += 1
            elif status == "FAILED":
                failed += 1
            elif status == "PARTIAL_COMPLETION":
                partial += 1

            metrics = data.get("metrics") or {}
            duration = metrics.get("total_duration_seconds", 0.0)
            total_duration += duration
            pages = metrics.get("pages_visited", len(data.get("visited_urls", [])))
            total_pages += pages
            retries = metrics.get("actions_retried", 0)
            total_retries += retries

            # Interventions
            interventions = data.get("interventions", [])
            for iv in interventions:
                if iv.get("obstacle") in {"CAPTCHA", "CLOUDFLARE_CHALLENGE", "BOT_DETECTED"}:
                    captcha_count += 1

            # Verification
            verif = data.get("verification_report") or {}
            if verif.get("is_successful"):
                verification_passed += 1
            cov = verif.get("evidence_coverage", 0.0)
            total_evidence_coverage += cov

            # Daily bucket
            created = data.get("created_at", 0)
            import datetime
            day = datetime.datetime.fromtimestamp(created).strftime("%Y-%m-%d")
            if day not in daily_trends:
                daily_trends[day] = {"date": day, "total": 0, "success": 0, "failed": 0, "avg_duration": 0.0, "durations": []}
            daily_trends[day]["total"] += 1
            if status == "COMPLETED":
                daily_trends[day]["success"] += 1
            elif status == "FAILED":
                daily_trends[day]["failed"] += 1
            daily_trends[day]["durations"].append(duration)

        trend_list = []
        for d in sorted(daily_trends.keys()):
            item = daily_trends[d]
            dur_avg = sum(item["durations"]) / len(item["durations"]) if item["durations"] else 0
            trend_list.append({
                "date": item["date"],
                "total": item["total"],
                "success": item["success"],
                "failed": item["failed"],
                "avg_duration": round(dur_avg, 1)
            })

        success_rate = round((successful / total) * 100, 1) if total > 0 else 0.0
        failure_rate = round((failed / total) * 100, 1) if total > 0 else 0.0
        avg_dur = round(total_duration / total, 1) if total > 0 else 0.0
        avg_pages = round(total_pages / total, 1) if total > 0 else 0.0
        avg_cov = round((total_evidence_coverage / total) * 100, 1) if total > 0 else 0.0
        verif_rate = round((verification_passed / total) * 100, 1) if total > 0 else 0.0
        recovery_rate = round(((successful + partial) / (successful + partial + total_retries)) * 100, 1) if (successful + partial + total_retries) > 0 else 100.0

        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": failed,
            "partial_tasks": partial,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "avg_duration_seconds": avg_dur,
            "total_pages_visited": total_pages,
            "avg_pages_per_task": avg_pages,
            "total_retries": total_retries,
            "recovery_rate": min(100.0, recovery_rate),
            "evidence_coverage_avg": avg_cov,
            "verification_pass_rate": verif_rate,
            "captcha_count": captcha_count,
            "recent_trends": trend_list[-14:],  # Last 14 days
            "task_types": task_types
        }

    def _format_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        for key in [
            "visited_urls", "metrics", "plan", "evidence",
            "extracted_records", "navigation_graph", "interventions",
            "logs", "verification_report"
        ]:
            json_col = f"{key}_json"
            if json_col in item:
                raw = item.pop(json_col, None)
                try:
                    item[key] = json.loads(raw) if raw else ([] if "s" in key or key in {"evidence", "logs"} else {})
                except Exception:
                    item[key] = [] if "s" in key or key in {"evidence", "logs"} else {}
        return item
