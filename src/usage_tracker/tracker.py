"""Foreground application usage tracker (poll + session accounting)."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from src.services.logger import AppLogger
from src.usage_tracker.database import UsageDatabase
from src.usage_tracker.models import ForegroundApp, UsageSession
from src.usage_tracker.windows import get_foreground_app, get_idle_seconds


# Ignore ultra-short focus switches (alt-tab noise).
MIN_SESSION_SECONDS = 1


class UsageTracker:
    """Tracks foreground app sessions and persists them when they end."""

    def __init__(
        self,
        database: UsageDatabase,
        logger: Optional[AppLogger] = None,
        idle_timeout_seconds: int = 300,
        on_session_saved: Optional[Callable[[UsageSession], None]] = None,
    ) -> None:
        self._db = database
        self._logger = logger
        self._idle_timeout_seconds = max(30, int(idle_timeout_seconds))
        self._on_session_saved = on_session_saved

        self._enabled = False
        self._idle = False
        self._current: Optional[UsageSession] = None
        self._current_key: Optional[str] = None
        self._current_app: Optional[ForegroundApp] = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def is_idle(self) -> bool:
        return self._idle

    @property
    def current_app(self) -> Optional[ForegroundApp]:
        return self._current_app

    @property
    def idle_timeout_seconds(self) -> int:
        return self._idle_timeout_seconds

    def set_idle_timeout_seconds(self, seconds: int) -> None:
        self._idle_timeout_seconds = max(30, int(seconds))

    def start(self) -> None:
        self._enabled = True
        self._idle = False
        if self._logger:
            self._logger.info(
                "Usage tracking started (idle timeout %ss).",
                self._idle_timeout_seconds,
            )

    def stop(self) -> None:
        self._enabled = False
        self._close_current(datetime.now(), reason="stopped")
        self._current_app = None
        self._idle = False
        if self._logger:
            self._logger.info("Usage tracking stopped.")

    def tick(self) -> None:
        """Poll foreground app / idle state. Call from a lightweight timer."""
        if not self._enabled:
            return

        now = datetime.now()
        idle_seconds = get_idle_seconds()
        is_idle = idle_seconds >= self._idle_timeout_seconds

        if is_idle:
            if not self._idle:
                self._close_current(now, reason="idle")
                self._idle = True
                self._current_app = None
            return

        # User became active again
        if self._idle:
            self._idle = False

        app = get_foreground_app()
        if app is None:
            self._close_current(now, reason="no-foreground")
            self._current_app = None
            return

        self._current_app = app
        key = app.key

        if self._current is None:
            self._start_session(app, now)
            return

        if key != self._current_key:
            self._close_current(now, reason="switch")
            self._start_session(app, now)

    def flush(self) -> None:
        """End the active session without disabling tracking."""
        self._close_current(datetime.now(), reason="flush")

    def _start_session(self, app: ForegroundApp, when: datetime) -> None:
        self._current = UsageSession(
            application_name=app.application_name,
            process_name=app.process_name,
            start_time=when,
            date=when.date(),
        )
        self._current_key = app.key

    def _close_current(self, when: datetime, reason: str = "") -> None:
        session = self._current
        self._current = None
        self._current_key = None
        if session is None:
            return

        session.finalize(when)
        if session.duration_seconds < MIN_SESSION_SECONDS:
            return

        try:
            session.id = self._db.insert_session(session)
            if self._on_session_saved:
                self._on_session_saved(session)
        except Exception as exc:
            if self._logger:
                self._logger.error("Failed to save usage session: %s", exc)
