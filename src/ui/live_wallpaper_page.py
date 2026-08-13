"""Live wallpaper configuration page."""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.live_wallpaper.service import LiveWallpaperService
from src.ui.layout_helpers import LAYOUT_MARGIN, LAYOUT_SPACING, apply_card_layout, configure_action_button


class LiveWallpaperPage(QWidget):
    """UI to start/stop video live wallpaper."""

    request_start = Signal(str)  # media path
    request_stop = Signal()
    mute_changed = Signal(bool)
    toast = Signal(str, str)  # message, level
    error = Signal(str)

    def __init__(
        self,
        live_service: LiveWallpaperService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._service = live_service
        self._selected_path: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(
            LAYOUT_MARGIN + 8,
            LAYOUT_MARGIN + 4,
            LAYOUT_MARGIN + 8,
            LAYOUT_MARGIN,
        )
        root.setSpacing(LAYOUT_SPACING)

        title = QLabel("Live Wallpaper")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Play a video behind your desktop icons. "
            "While live wallpaper is active, the static image scheduler is paused."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        # Status card
        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        apply_card_layout(status_layout)
        status_title = QLabel("Status")
        status_title.setObjectName("sectionTitle")
        self.status_badge = QLabel("Inactive")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setProperty("status", "stopped")
        self.media_label = QLabel("No live media selected")
        self.media_label.setObjectName("mutedText")
        self.media_label.setWordWrap(True)
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_badge, alignment=Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.media_label)
        root.addWidget(status_card)

        # Media controls
        media_card = QFrame()
        media_card.setObjectName("card")
        media_layout = QVBoxLayout(media_card)
        apply_card_layout(media_layout)
        media_title = QLabel("Media")
        media_title.setObjectName("sectionTitle")
        media_hint = QLabel(
            "Supported: MP4, WebM, MKV, MOV, AVI. Video audio is muted by default."
        )
        media_hint.setObjectName("cardHint")
        media_hint.setWordWrap(True)

        self.select_media_button = QPushButton("Select Video")
        self.select_media_button.setObjectName("primaryButton")
        self.start_button = QPushButton("Start Live Wallpaper")
        self.start_button.setObjectName("primaryButton")
        self.stop_button = QPushButton("Stop Live Wallpaper")
        self.mute_checkbox = QCheckBox("Mute audio (recommended)")
        self.mute_checkbox.setChecked(True)
        self.mute_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        for btn in (self.select_media_button, self.start_button, self.stop_button):
            configure_action_button(btn)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)

        row = QHBoxLayout()
        row.setSpacing(LAYOUT_SPACING)
        row.addWidget(self.select_media_button)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        row.addStretch(1)

        media_layout.addWidget(media_title)
        media_layout.addWidget(media_hint)
        media_layout.addLayout(row)
        media_layout.addWidget(self.mute_checkbox)
        root.addWidget(media_card)

        note = QLabel(
            "Tip: Live wallpaper uses more CPU/GPU than a static image. "
            "Stop it anytime from this page or when you start the static scheduler."
        )
        note.setObjectName("mutedText")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addStretch(1)

        self.select_media_button.clicked.connect(self._select_media)
        self.start_button.clicked.connect(self._start_clicked)
        self.stop_button.clicked.connect(lambda: self.request_stop.emit())
        self.mute_checkbox.stateChanged.connect(self._on_mute_changed)

        self._service.status_changed.connect(self._on_status)
        self._service.media_changed.connect(self._on_media)
        self._on_status(self._service.is_active)
        if self._service.media_path:
            self._on_media(self._service.media_path)

    def _on_mute_changed(self, _state=None) -> None:
        self.mute_changed.emit(self.mute_checkbox.isChecked())

    @Slot()
    def _select_media(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select live wallpaper video",
            os.path.expanduser("~"),
            "Video (*.mp4 *.webm *.mkv *.avi *.mov *.m4v);;All files (*.*)",
        )
        if not path:
            return
        self._selected_path = path
        self.media_label.setText(path)
        self.toast.emit("Live media selected", "success")

    @Slot()
    def _start_clicked(self) -> None:
        path = self._selected_path or self._service.media_path
        if not path:
            self.error.emit("Select a video first.")
            return
        self.request_start.emit(path)

    @Slot(bool)
    def _on_status(self, active: bool) -> None:
        if active:
            self.status_badge.setText("Live active")
            self.status_badge.setProperty("status", "running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_badge.setText("Inactive")
            self.status_badge.setProperty("status", "stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    @Slot(str)
    def _on_media(self, path: str) -> None:
        self._selected_path = path
        self.media_label.setText(path or "No live media selected")
