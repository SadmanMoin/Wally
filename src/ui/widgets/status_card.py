"""Compact status summary card."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.layout_helpers import apply_card_layout


class StatusCard(QFrame):
    """Shows scheduler state and key runtime details."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        title = QLabel("Status")
        title.setObjectName("sectionTitle")

        self._dot = QFrame()
        self._dot.setObjectName("statusDot")
        self._dot.setProperty("status", "stopped")

        self._status_label = QLabel("Inactive")
        self._status_label.setObjectName("statusBadge")
        self._status_label.setProperty("status", "stopped")
        self._status_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        status_row.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(self._status_label)
        status_row.addStretch(1)

        self._current = self._meta_pair("Current wallpaper")
        self._next = self._meta_pair("Next change")
        self._source = self._meta_pair("Wallpaper source")
        self._scheduler = self._meta_pair("Scheduler")

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.addWidget(self._current[0], 0, 0)
        grid.addWidget(self._current[1], 0, 1)
        grid.addWidget(self._next[0], 0, 2)
        grid.addWidget(self._next[1], 0, 3)
        grid.addWidget(self._source[0], 1, 0)
        grid.addWidget(self._source[1], 1, 1)
        grid.addWidget(self._scheduler[0], 1, 2)
        grid.addWidget(self._scheduler[1], 1, 3)

        layout = QVBoxLayout(self)
        apply_card_layout(layout)
        layout.addWidget(title)
        layout.addLayout(status_row)
        layout.addSpacing(4)
        layout.addLayout(grid)

    @staticmethod
    def _meta_pair(label: str) -> tuple[QLabel, QLabel]:
        key = QLabel(label)
        key.setObjectName("metaLabel")
        value = QLabel("—")
        value.setObjectName("metaValue")
        value.setWordWrap(True)
        return key, value

    def set_status(self, status: str) -> None:
        labels = {
            "running": "Active",
            "paused": "Paused",
            "stopped": "Inactive",
        }
        text = labels.get(status, "Inactive")
        for widget in (self._dot, self._status_label):
            if widget is self._status_label:
                widget.setText(text)
            widget.setProperty("status", status)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def set_details(
        self,
        current: str,
        next_change: str,
        source: str,
        scheduler: str,
    ) -> None:
        self._current[1].setText(current or "None")
        self._next[1].setText(next_change or "—")
        self._source[1].setText(source or "No folder selected")
        self._scheduler[1].setText(scheduler or "Stopped")
