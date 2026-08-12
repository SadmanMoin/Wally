"""Qt service wrapping the usage tracker with a background timer."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from src.services.logger import AppLogger
from src.usage_tracker.database import UsageDatabase
from src.usage_tracker.models import AppUsageSummary, DailyUsagePoint, ForegroundApp
from src.usage_tracker.statistics import UsageStatistics, format_duration, resolve_range
from src.usage_tracker.tracker import UsageTracker

# Poll interval — light on CPU while still accurate enough for session timing.
POLL_INTERVAL_MS = 2000


class UsageTrackerService(QObject):
    """Exposes usage tracking + statistics to the UI layer."""

    status_changed = Signal(bool)  # tracking enabled
    idle_changed = Signal(bool)
    session_recorded = Signal()
    current_app_changed = Signal(str)

    def __init__(
        self,
        logger: AppLogger,
        database: Optional[UsageDatabase] = None,
        idle_timeout_seconds: int = 300,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._logger = logger
        self._db = database or UsageDatabase()
        self._stats = UsageStatistics(self._db)
        self._tracker = UsageTracker(
            database=self._db,
            logger=logger,
            idle_timeout_seconds=idle_timeout_seconds,
            on_session_saved=self._on_session_saved,
        )
        self._last_app_label = ""

        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._on_poll)

    @property
    def database(self) -> UsageDatabase:
        return self._db

    @property
    def is_tracking(self) -> bool:
        return self._tracker.enabled

    @property
    def is_idle(self) -> bool:
        return self._tracker.is_idle

    @property
    def current_app(self) -> Optional[ForegroundApp]:
        return self._tracker.current_app

    def set_idle_timeout_seconds(self, seconds: int) -> None:
        self._tracker.set_idle_timeout_seconds(seconds)

    def set_idle_timeout_minutes(self, minutes: int) -> None:
        self.set_idle_timeout_seconds(max(1, int(minutes)) * 60)

    def start(self) -> None:
        if self._tracker.enabled:
            return
        self._tracker.start()
        self._timer.start()
        self.status_changed.emit(True)

    def stop(self) -> None:
        if not self._tracker.enabled:
            self._tracker.flush()
            return
        self._timer.stop()
        self._tracker.stop()
        self.status_changed.emit(False)
        self.current_app_changed.emit("")

    def flush(self) -> None:
        self._tracker.flush()

    @Slot()
    def _on_poll(self) -> None:
        was_idle = self._tracker.is_idle
        prev_label = self._last_app_label
        self._tracker.tick()
        if self._tracker.is_idle != was_idle:
            self.idle_changed.emit(self._tracker.is_idle)

        app = self._tracker.current_app
        label = ""
        if app and not self._tracker.is_idle:
            label = f"{app.application_name} ({app.process_name})"
        if label != prev_label:
            self._last_app_label = label
            self.current_app_changed.emit(label)

    def _on_session_saved(self, _session) -> None:
        self.session_recorded.emit()

    # ── Statistics API ──────────────────────────────────────────────

    def resolve_range(
        self,
        preset: str,
        custom_start: Optional[date] = None,
        custom_end: Optional[date] = None,
    ):
        return resolve_range(preset, custom_start, custom_end)

    def summarize(
        self,
        start_date: date,
        end_date: date,
        limit: Optional[int] = None,
    ) -> List[AppUsageSummary]:
        return self._stats.summarize(start_date, end_date, limit=limit)

    def total_seconds(self, start_date: date, end_date: date) -> int:
        return self._stats.total_seconds(start_date, end_date)

    def daily_trend(self, start_date: date, end_date: date) -> List[DailyUsagePoint]:
        return self._stats.daily_trend(start_date, end_date)

    def top_apps(
        self,
        start_date: date,
        end_date: date,
        limit: int = 5,
    ) -> List[AppUsageSummary]:
        return self._stats.top_apps(start_date, end_date, limit=limit)

    @staticmethod
    def format_duration(seconds: int) -> str:
        return format_duration(seconds)
