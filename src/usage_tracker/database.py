"""SQLite persistence for application usage sessions."""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date
from typing import Iterator, List, Optional, Tuple

from src.usage_tracker.models import DailyUsagePoint, UsageSession


def default_db_path() -> str:
    app_data = os.getenv("APPDATA") or os.path.expanduser("~")
    directory = os.path.join(app_data, "WallpaperChanger")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "usage.db")


class UsageDatabase:
    """Thread-safe SQLite store for usage sessions."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or default_db_path()
        self._lock = threading.RLock()
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_usage_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_name TEXT NOT NULL,
                    process_name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    date TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_usage_date
                    ON app_usage_sessions(date);
                CREATE INDEX IF NOT EXISTS idx_usage_app
                    ON app_usage_sessions(application_name);
                CREATE INDEX IF NOT EXISTS idx_usage_process
                    ON app_usage_sessions(process_name);
                CREATE INDEX IF NOT EXISTS idx_usage_date_app
                    ON app_usage_sessions(date, application_name);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_session(self, session: UsageSession) -> int:
        """Persist a finalized session and return its row id."""
        if session.end_time is None:
            raise ValueError("Session must be finalized before insert.")

        start = session.start_time.isoformat(timespec="seconds")
        end = session.end_time.isoformat(timespec="seconds")
        day = (session.date or session.start_time.date()).isoformat()

        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO app_usage_sessions (
                        application_name, process_name, start_time, end_time,
                        duration_seconds, date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.application_name,
                        session.process_name,
                        start,
                        end,
                        int(session.duration_seconds),
                        day,
                    ),
                )
                return int(cursor.lastrowid)

    def aggregate_by_app(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Tuple[str, str, int, int]]:
        """Return (application_name, process_name, total_seconds, sessions)."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        application_name,
                        process_name,
                        SUM(duration_seconds) AS total_seconds,
                        COUNT(*) AS session_count
                    FROM app_usage_sessions
                    WHERE date >= ? AND date <= ?
                    GROUP BY application_name, process_name
                    ORDER BY total_seconds DESC
                    """,
                    (start_date.isoformat(), end_date.isoformat()),
                ).fetchall()
        return [
            (
                row["application_name"],
                row["process_name"],
                int(row["total_seconds"] or 0),
                int(row["session_count"] or 0),
            )
            for row in rows
        ]

    def daily_totals(
        self,
        start_date: date,
        end_date: date,
    ) -> List[DailyUsagePoint]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT date, SUM(duration_seconds) AS total_seconds
                    FROM app_usage_sessions
                    WHERE date >= ? AND date <= ?
                    GROUP BY date
                    ORDER BY date ASC
                    """,
                    (start_date.isoformat(), end_date.isoformat()),
                ).fetchall()
        return [
            DailyUsagePoint(
                day=date.fromisoformat(row["date"]),
                total_seconds=int(row["total_seconds"] or 0),
            )
            for row in rows
        ]

    def total_seconds(self, start_date: date, end_date: date) -> int:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT SUM(duration_seconds) AS total_seconds
                    FROM app_usage_sessions
                    WHERE date >= ? AND date <= ?
                    """,
                    (start_date.isoformat(), end_date.isoformat()),
                ).fetchone()
        return int((row["total_seconds"] if row else 0) or 0)

    def delete_all(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM app_usage_sessions")
