"""Usage statistics queries and formatting helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from src.usage_tracker.database import UsageDatabase
from src.usage_tracker.models import AppUsageSummary, DailyUsagePoint


def resolve_range(
    preset: str,
    custom_start: Optional[date] = None,
    custom_end: Optional[date] = None,
    today: Optional[date] = None,
) -> Tuple[date, date]:
    """Map a UI preset name to an inclusive date range."""
    today = today or date.today()
    preset_key = (preset or "Today").strip().lower()

    if preset_key == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if preset_key in {"last 7 days", "7 days", "week"}:
        return today - timedelta(days=6), today
    if preset_key in {"last 30 days", "30 days", "month"}:
        return today - timedelta(days=29), today
    if preset_key in {"custom", "custom range"}:
        start = custom_start or today
        end = custom_end or today
        if start > end:
            start, end = end, start
        return start, end
    # Default: today
    return today, today


def format_duration(seconds: int) -> str:
    """Human-readable duration such as 2h 35m or 45m."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    rem_h = hours % 24
    rem_m = minutes % 60
    rem_s = seconds % 60

    if days > 0:
        return f"{days}d {rem_h}h"
    if hours > 0:
        if rem_m:
            return f"{hours}h {rem_m}m"
        return f"{hours}h"
    if rem_s and minutes < 5:
        return f"{minutes}m {rem_s}s"
    return f"{minutes}m"


class UsageStatistics:
    """High-level statistics built from the SQLite store."""

    def __init__(self, database: UsageDatabase) -> None:
        self._db = database

    def summarize(
        self,
        start_date: date,
        end_date: date,
        limit: Optional[int] = None,
    ) -> List[AppUsageSummary]:
        rows = self._db.aggregate_by_app(start_date, end_date)
        total = sum(item[2] for item in rows) or 0
        summaries: List[AppUsageSummary] = []
        for app_name, process_name, total_seconds, sessions in rows:
            percentage = (total_seconds / total * 100.0) if total else 0.0
            summaries.append(
                AppUsageSummary(
                    application_name=app_name,
                    process_name=process_name,
                    total_seconds=total_seconds,
                    session_count=sessions,
                    percentage=percentage,
                )
            )
        if limit is not None:
            return summaries[:limit]
        return summaries

    def total_seconds(self, start_date: date, end_date: date) -> int:
        return self._db.total_seconds(start_date, end_date)

    def daily_trend(self, start_date: date, end_date: date) -> List[DailyUsagePoint]:
        """Return a continuous daily series (zeros for missing days)."""
        points = {p.day: p.total_seconds for p in self._db.daily_totals(start_date, end_date)}
        series: List[DailyUsagePoint] = []
        day = start_date
        while day <= end_date:
            series.append(DailyUsagePoint(day=day, total_seconds=points.get(day, 0)))
            day += timedelta(days=1)
        return series

    def top_apps(
        self,
        start_date: date,
        end_date: date,
        limit: int = 5,
    ) -> List[AppUsageSummary]:
        return self.summarize(start_date, end_date, limit=limit)
