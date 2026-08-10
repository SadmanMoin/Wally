"""Scrollable log panel for in-app activity."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from src.ui.layout_helpers import apply_card_layout


class LogPanel(QFrame):
    """Displays recent application log messages."""

    MAX_BLOCKS = 400

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")

        title = QLabel("Activity Log")
        title.setObjectName("sectionTitle")

        hint = QLabel("Recent application events and status messages.")
        hint.setObjectName("cardHint")
        hint.setWordWrap(True)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(self.MAX_BLOCKS)
        self.log_view.setPlaceholderText("Application events will appear here…")
        self.log_view.setMinimumHeight(160)

        layout = QVBoxLayout(self)
        apply_card_layout(layout)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.log_view, stretch=1)

    def append(self, level: str, message: str) -> None:
        prefix = {
            "INFO": "[INFO]",
            "WARNING": "[WARN]",
            "ERROR": "[ERROR]",
        }.get(level, "[LOG]")
        self.log_view.appendPlainText(f"{prefix} {message}")
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
