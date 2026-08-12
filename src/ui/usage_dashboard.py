"""Application Usage dashboard page."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.layout_helpers import LAYOUT_MARGIN, LAYOUT_SPACING, apply_card_layout
from src.ui.widgets.usage_charts import DistributionChart, HorizontalBarChart, VerticalBarChart
from src.usage_tracker.service import UsageTrackerService


class UsageDashboard(QWidget):
    """Dashboard showing local foreground application usage statistics."""

    def __init__(
        self,
        usage_service: UsageTrackerService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._service = usage_service
        self._building = False

        root = QVBoxLayout(self)
        root.setContentsMargins(
            LAYOUT_MARGIN + 8,
            LAYOUT_MARGIN + 4,
            LAYOUT_MARGIN + 8,
            LAYOUT_MARGIN,
        )
        root.setSpacing(LAYOUT_SPACING)

        # Header
        title = QLabel("Application Usage")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "See how much time you spend in each app. Only the active foreground "
            "window is tracked — locally, on this PC."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        # Filters + status
        filter_card = QFrame()
        filter_card.setObjectName("card")
        filter_layout = QVBoxLayout(filter_card)
        apply_card_layout(filter_layout)

        filter_row = QHBoxLayout()
        filter_label = QLabel("Period")
        filter_label.setObjectName("metaLabel")
        self.period_combo = QComboBox()
        self.period_combo.addItems(
            ["Today", "Yesterday", "Last 7 days", "Last 30 days", "Custom"]
        )
        self.period_combo.setMinimumWidth(160)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        self._set_custom_dates_enabled(False)

        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.period_combo)
        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("From"))
        filter_row.addWidget(self.start_date)
        filter_row.addWidget(QLabel("To"))
        filter_row.addWidget(self.end_date)
        filter_row.addStretch(1)

        self.tracking_status = QLabel("Tracking: Off")
        self.tracking_status.setObjectName("statusBadge")
        self.tracking_status.setProperty("status", "stopped")
        self.tracking_status.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        filter_row.addWidget(self.tracking_status)

        self.current_app_label = QLabel("Current: —")
        self.current_app_label.setObjectName("mutedText")
        self.current_app_label.setWordWrap(True)

        filter_layout.addLayout(filter_row)
        filter_layout.addWidget(self.current_app_label)
        privacy = QLabel(
            "Privacy: only app names and durations are stored on this computer. "
            "No keystrokes, clipboard, or file contents are recorded."
        )
        privacy.setObjectName("cardHint")
        privacy.setWordWrap(True)
        filter_layout.addWidget(privacy)
        root.addWidget(filter_card)

        # Summary metrics
        metrics = QHBoxLayout()
        metrics.setSpacing(LAYOUT_SPACING)
        self.total_time_value = self._metric_card("Total tracked time", "0s")
        self.apps_count_value = self._metric_card("Applications", "0")
        self.sessions_value = self._metric_card("Sessions", "0")
        metrics.addWidget(self.total_time_value[0])
        metrics.addWidget(self.apps_count_value[0])
        metrics.addWidget(self.sessions_value[0])
        root.addLayout(metrics)

        # Charts row
        charts = QHBoxLayout()
        charts.setSpacing(LAYOUT_SPACING)

        top_card = QFrame()
        top_card.setObjectName("card")
        top_layout = QVBoxLayout(top_card)
        apply_card_layout(top_layout)
        top_title = QLabel("Top applications")
        top_title.setObjectName("sectionTitle")
        self.top_chart = HorizontalBarChart()
        top_layout.addWidget(top_title)
        top_layout.addWidget(self.top_chart)
        charts.addWidget(top_card, stretch=1)

        dist_card = QFrame()
        dist_card.setObjectName("card")
        dist_layout = QVBoxLayout(dist_card)
        apply_card_layout(dist_layout)
        dist_title = QLabel("Usage distribution")
        dist_title.setObjectName("sectionTitle")
        self.dist_chart = DistributionChart()
        dist_layout.addWidget(dist_title)
        dist_layout.addWidget(self.dist_chart)
        self.trend_chart = VerticalBarChart()
        trend_title = QLabel("Daily trend")
        trend_title.setObjectName("sectionTitle")
        dist_layout.addWidget(trend_title)
        dist_layout.addWidget(self.trend_chart)
        charts.addWidget(dist_card, stretch=1)
        root.addLayout(charts)

        # Table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout(table_card)
        apply_card_layout(table_layout)
        table_title = QLabel("Application usage")
        table_title.setObjectName("sectionTitle")
        table_hint = QLabel("Active (foreground) time only — background apps are not counted.")
        table_hint.setObjectName("cardHint")
        table_hint.setWordWrap(True)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Application", "Process", "Time Used", "Percentage", "Sessions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(220)
        self.table.setShowGrid(False)

        table_layout.addWidget(table_title)
        table_layout.addWidget(table_hint)
        table_layout.addWidget(self.table)
        root.addWidget(table_card, stretch=1)

        # Signals
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        self.start_date.dateChanged.connect(self._on_dates_changed)
        self.end_date.dateChanged.connect(self._on_dates_changed)
        self._service.session_recorded.connect(self.refresh)
        self._service.status_changed.connect(self._on_tracking_status)
        self._service.idle_changed.connect(self._on_idle_changed)
        self._service.current_app_changed.connect(self._on_current_app)

        # Soft auto-refresh while page is shown
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(15_000)
        self._refresh_timer.timeout.connect(self.refresh)

        self._on_tracking_status(self._service.is_tracking)
        self.refresh()

    def _metric_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        apply_card_layout(layout)
        label = QLabel(title)
        label.setObjectName("metaLabel")
        value_label = QLabel(value)
        value_label.setObjectName("pageTitle")
        value_label.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(value_label)
        return card, value_label

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()
        self._refresh_timer.start()

    def hideEvent(self, event) -> None:  # type: ignore[override]
        super().hideEvent(event)
        self._refresh_timer.stop()

    def _set_custom_dates_enabled(self, enabled: bool) -> None:
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    @Slot(str)
    def _on_period_changed(self, text: str) -> None:
        is_custom = text.strip().lower() == "custom"
        self._set_custom_dates_enabled(is_custom)
        if not is_custom:
            start, end = self._service.resolve_range(text)
            self._building = True
            self.start_date.setDate(QDate(start.year, start.month, start.day))
            self.end_date.setDate(QDate(end.year, end.month, end.day))
            self._building = False
        self.refresh()

    @Slot()
    def _on_dates_changed(self) -> None:
        if self._building:
            return
        if self.period_combo.currentText().strip().lower() != "custom":
            return
        self.refresh()

    @Slot(bool)
    def _on_tracking_status(self, enabled: bool) -> None:
        if enabled:
            self.tracking_status.setText("Tracking: Active")
            self.tracking_status.setProperty("status", "running")
        else:
            self.tracking_status.setText("Tracking: Off")
            self.tracking_status.setProperty("status", "stopped")
        self.tracking_status.style().unpolish(self.tracking_status)
        self.tracking_status.style().polish(self.tracking_status)

    @Slot(bool)
    def _on_idle_changed(self, idle: bool) -> None:
        if idle and self._service.is_tracking:
            self.tracking_status.setText("Tracking: Idle")
            self.tracking_status.setProperty("status", "paused")
            self.tracking_status.style().unpolish(self.tracking_status)
            self.tracking_status.style().polish(self.tracking_status)
            self.current_app_label.setText("Current: idle (not counting)")
        elif self._service.is_tracking:
            self._on_tracking_status(True)

    @Slot(str)
    def _on_current_app(self, label: str) -> None:
        if self._service.is_idle:
            self.current_app_label.setText("Current: idle (not counting)")
        elif label:
            self.current_app_label.setText(f"Current: {label}")
        else:
            self.current_app_label.setText("Current: —")

    def _selected_range(self) -> tuple[date, date]:
        preset = self.period_combo.currentText()
        if preset.strip().lower() == "custom":
            start = self.start_date.date().toPython()
            end = self.end_date.date().toPython()
            return self._service.resolve_range("Custom", start, end)
        return self._service.resolve_range(preset)

    @Slot()
    def refresh(self) -> None:
        start, end = self._selected_range()
        summaries = self._service.summarize(start, end)
        total = self._service.total_seconds(start, end)
        sessions = sum(item.session_count for item in summaries)

        self.total_time_value[1].setText(self._service.format_duration(total))
        self.apps_count_value[1].setText(str(len(summaries)))
        self.sessions_value[1].setText(str(sessions))

        # Table
        self.table.setRowCount(len(summaries))
        for row, item in enumerate(summaries):
            values = [
                item.application_name,
                item.process_name,
                self._service.format_duration(item.total_seconds),
                f"{item.percentage:.0f}%",
                str(item.session_count),
            ]
            for col, text in enumerate(values):
                cell = QTableWidgetItem(text)
                if col >= 2:
                    cell.setTextAlignment(
                        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    )
                self.table.setItem(row, col, cell)

        # Top apps chart
        top = summaries[:6]
        self.top_chart.set_data(
            [
                (
                    s.application_name,
                    float(s.total_seconds),
                    self._service.format_duration(s.total_seconds),
                )
                for s in top
            ]
        )
        self.dist_chart.set_data(
            [(s.application_name, float(s.total_seconds)) for s in top]
        )

        # Daily trend
        trend = self._service.daily_trend(start, end)
        span = (end - start).days
        trend_items = []
        for point in trend:
            if span <= 0:
                label = "Today"
            elif span <= 6:
                label = point.day.strftime("%a")
            else:
                label = point.day.strftime("%m/%d")
            trend_items.append(
                (label, float(point.total_seconds), self._service.format_duration(point.total_seconds))
            )
        self.trend_chart.set_data(trend_items)
