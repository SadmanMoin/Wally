"""Data models for application usage tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class ForegroundApp:
    """Snapshot of the current foreground application."""

    process_name: str
    application_name: str
    process_id: int
    window_title: str = ""

    @property
    def key(self) -> str:
        return f"{self.process_name}|{self.application_name}".lower()


@dataclass
class UsageSession:
    """A continuous period of foreground usage for one application."""

    application_name: str
    process_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    date: Optional[date] = None
    id: Optional[int] = None

    def finalize(self, end_time: datetime) -> None:
        self.end_time = end_time
        self.duration_seconds = max(0, int((end_time - self.start_time).total_seconds()))
        self.date = self.start_time.date()


@dataclass(frozen=True)
class AppUsageSummary:
    """Aggregated usage for one application over a date range."""

    application_name: str
    process_name: str
    total_seconds: int
    session_count: int
    percentage: float = 0.0


@dataclass(frozen=True)
class DailyUsagePoint:
    """Total tracked seconds for a single calendar day."""

    day: date
    total_seconds: int
