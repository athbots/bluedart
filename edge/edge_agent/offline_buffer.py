"""
Offline Edge SQLite Telemetry Buffer.
Persists telemetry locally when internet is offline, replaying with exponential backoff and idempotency.
"""

import sqlite3
import json
import time
import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("offline_buffer")


class OfflineEdgeBuffer:
    def __init__(self, db_path: str = "./edge_buffer.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_queue (
                    id TEXT PRIMARY KEY,
                    vehicle_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    next_retry_at REAL NOT NULL
                )
            """)
            conn.commit()

    def enqueue(self, vehicle_id: str, topic: str, payload_dict: Dict[str, Any]) -> str:
        """Enqueue payload into SQLite local buffer."""
        p_copy = dict(payload_dict)
        event_id = p_copy.pop("message_id", None) or str(uuid.uuid4())
        p_copy["message_id"] = event_id
        now = time.time()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO telemetry_queue
                (id, vehicle_id, topic, payload, retry_count, created_at, next_retry_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, vehicle_id, topic, json.dumps(p_copy), 0, now, now),
            )
            conn.commit()
        return event_id

    def get_pending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch pending records eligible for transmission."""
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, vehicle_id, topic, payload, retry_count
                FROM telemetry_queue
                WHERE next_retry_at <= ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (now, limit),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "vehicle_id": row["vehicle_id"],
                    "topic": row["topic"],
                    "payload": json.loads(row["payload"]),
                    "retry_count": row["retry_count"],
                })
            return results

    def acknowledge_success(self, event_id: str):
        """Remove event from buffer after successful server ingestion."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM telemetry_queue WHERE id = ?", (event_id,))
            conn.commit()

    def record_failure(self, event_id: str, current_retries: int):
        """Apply exponential backoff to next retry timestamp."""
        next_retries = current_retries + 1
        # Exponential backoff: 2s, 4s, 8s, 16s ... max 120s
        backoff_seconds = min(120, 2 ** min(next_retries, 7))
        next_time = time.time() + backoff_seconds

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE telemetry_queue
                SET retry_count = ?, next_retry_at = ?
                WHERE id = ?
                """,
                (next_retries, next_time, event_id),
            )
            conn.commit()

    def get_queue_size(self) -> int:
        """Return total pending buffer items."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM telemetry_queue")
            return cursor.fetchone()[0]
