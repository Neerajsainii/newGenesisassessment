from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    output_path TEXT,
                    error_message TEXT
                )
                """
            )
            conn.commit()

    def create_job(self, job_id: str, mode: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, mode, status, created_at)
                VALUES (?, ?, 'queued', ?)
                """,
                (job_id, mode, _utc_now()),
            )
            conn.commit()

    def update_status(
        self,
        job_id: str,
        status: str,
        output_path: str | None = None,
        error_message: str | None = None,
    ) -> None:
        started_at = _utc_now() if status == "running" else None
        finished_at = _utc_now() if status in {"succeeded", "failed"} else None

        with self._connect() as conn:
            if status == "running":
                conn.execute(
                    "UPDATE jobs SET status=?, started_at=? WHERE job_id=?",
                    (status, started_at, job_id),
                )
            elif status == "succeeded":
                conn.execute(
                    """
                    UPDATE jobs
                    SET status=?, finished_at=?, output_path=?, error_message=NULL
                    WHERE job_id=?
                    """,
                    (status, finished_at, output_path, job_id),
                )
            elif status == "failed":
                conn.execute(
                    """
                    UPDATE jobs
                    SET status=?, finished_at=?, error_message=?
                    WHERE job_id=?
                    """,
                    (status, finished_at, error_message, job_id),
                )
            else:
                conn.execute("UPDATE jobs SET status=? WHERE job_id=?", (status, job_id))
            conn.commit()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            return dict(row) if row else None

