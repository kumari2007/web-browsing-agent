"""
Persistent experience memory in SQLite.
Records successful search strategies, locator adjustments, and known site failure modes.
Prevents repeating known failed actions and guides future planner decisions.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger("agent.memory.experience")


class ExperienceMemory:
    """Manages persistent lessons and operational insights across tasks."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()

    def _init_db(self) -> None:
        """Create SQLite experience schema if not present."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experience_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_or_topic TEXT NOT NULL,
                    strategy_type TEXT NOT NULL, -- 'search', 'locator', 'extraction', 'failure'
                    outcome TEXT NOT NULL,        -- 'success' or 'failure'
                    details_json TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON experience_entries(domain_or_topic)")
            conn.commit()

    def record_experience(
        self,
        domain_or_topic: str,
        strategy_type: str,
        outcome: str,
        details: Dict[str, Any]
    ) -> None:
        """Save a strategy outcome (success or failure)."""
        domain_key = domain_or_topic.lower().strip()
        details_str = json.dumps(details)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Check if identical strategy already logged
            cursor.execute("""
                SELECT id, usage_count FROM experience_entries
                WHERE domain_or_topic = ? AND strategy_type = ? AND outcome = ?
            """, (domain_key, strategy_type, outcome))
            row = cursor.fetchone()

            if row:
                entry_id, count = row
                cursor.execute("""
                    UPDATE experience_entries
                    SET usage_count = ?, details_json = ?, last_observed = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (count + 1, details_str, entry_id))
            else:
                cursor.execute("""
                    INSERT INTO experience_entries
                    (domain_or_topic, strategy_type, outcome, details_json)
                    VALUES (?, ?, ?, ?)
                """, (domain_key, strategy_type, outcome, details_str))
            conn.commit()

    def get_advice(self, domain_or_topic: str) -> Dict[str, Any]:
        """Query past experience for a given domain or search topic."""
        domain_key = domain_or_topic.lower().strip()
        advice = {"recommended": [], "avoid": []}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strategy_type, outcome, details_json FROM experience_entries
                WHERE domain_or_topic = ? OR ? LIKE ('%' || domain_or_topic || '%')
            """, (domain_key, domain_key))

            for stype, outcome, djson in cursor.fetchall():
                try:
                    data = json.loads(djson)
                    if outcome == "success":
                        advice["recommended"].append({"type": stype, "details": data})
                    else:
                        advice["avoid"].append({"type": stype, "details": data})
                except Exception:
                    continue

        return advice

    def get_all_experiences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent experience entries for the UI dashboard."""
        records = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, domain_or_topic, strategy_type, outcome, details_json, usage_count, last_observed
                FROM experience_entries
                ORDER BY last_observed DESC
                LIMIT ?
            """, (limit,))
            for row in cursor.fetchall():
                item = dict(row)
                try:
                    item["details"] = json.loads(item["details_json"])
                except Exception:
                    item["details"] = {}
                records.append(item)
        return records

    def delete_entry(self, entry_id: int) -> bool:
        """Delete a single experience memory entry by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM experience_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_memory(self) -> None:
        """Clear all stored experience records."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM experience_entries")
            conn.commit()
        logger.info("Cleared all experience memory entries.")
