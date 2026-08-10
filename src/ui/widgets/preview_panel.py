"""Wallpaper preview widget with professional empty states."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.layout_helpers import apply_card_layout, configure_action_button


class PreviewPanel(QFrame):
    """Displays a scaled wallpaper preview with navigation controls."""

    apply_requested = Signal(str)
    preview_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._current_path: Optional[str] = None
        self._resolution: Optional[Tuple[int, int]] = None

        title = QLabel("Current Wallpaper")
        title.setObjectName("sectionTitle")

        hint = QLabel("Preview and browse images from your selected folders.")
        hint.setObjectName("cardHint")
        hint.setWordWrap(True)

        self.image_label = QLabel()
        self.image_label.setObjectName("previewImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(240)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.image_label.setWordWrap(True)

        self.filename_label = QLabel("No wallpaper selected")
        self.filename_label.setObjectName("filenameLabel")
        self.filename_label.setWordWrap(True)

        self.meta_label = QLabel("Select a wallpaper folder to get started")
        self.meta_label.setObjectName("mutedText")
        self.meta_label.setWordWrap(True)

        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.apply_button = QPushButton("Apply Preview")
        self.apply_button.setObjectName("primaryButton")
        self.change_now_button = QPushButton("Change Now")
        self.change_now_button.setObjectName("primaryButton")

        for button in (
            self.prev_button,
            self.next_button,
            self.apply_button,
            self.change_now_button,
        ):
            configure_action_button(button)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.apply_button)
        nav_layout.addWidget(self.change_now_button)

        layout = QVBoxLayout(self)
        apply_card_layout(layout)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.image_label, stretch=1)
        layout.addWidget(self.filename_label)
        layout.addWidget(self.meta_label)
        layout.addLayout(nav_layout)

        self.prev_button.clicked.connect(lambda: self.preview_changed.emit("prev"))
        self.next_button.clicked.connect(lambda: self.preview_changed.emit("next"))
        self.apply_button.clicked.connect(self._emit_apply)

        self._show_empty_state(
            "No wallpaper folder selected",
            "Add one or more folders containing images to begin.",
        )

    @property
    def current_path(self) -> Optional[str]:
        return self._current_path

    @property
    def resolution(self) -> Optional[Tuple[int, int]]:
        return self._resolution

    def set_preview(self, image_path: Optional[str]) -> None:
        self._current_path = image_path
        self._resolution = None

        if not image_path or not os.path.isfile(image_path):
            self._show_empty_state(
                "Wallpaper unavailable",
                "The image is missing or could not be loaded.",
            )
            self.apply_button.setEnabled(False)
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("Unable to load image preview")
            self.filename_label.setText(os.path.basename(image_path))
            self.meta_label.setText("Preview failed")
            self.apply_button.setEnabled(False)
            return

        self._resolution = (pixmap.width(), pixmap.height())
        self._render_pixmap(pixmap)
        self.filename_label.setText(os.path.basename(image_path))
        self.meta_label.setText(
            f"{pixmap.width()} × {pixmap.height()} px  ·  {self._format_size(image_path)}"
        )
        self.apply_button.setEnabled(True)

    def set_empty_folders(self) -> None:
        self._current_path = None
        self._resolution = None
        self._show_empty_state(
            "No wallpaper folder selected",
            "Add one or more folders containing images to begin.",
        )
        self.apply_button.setEnabled(False)

    def set_no_images(self) -> None:
        self._current_path = None
        self._resolution = None
        self._show_empty_state(
            "No wallpapers found",
            "The selected folders do not contain supported image files.",
        )
        self.apply_button.setEnabled(False)

    def _show_empty_state(self, title: str, hint: str) -> None:
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(f"{title}\n\n{hint}")
        self.filename_label.setText(title)
        self.meta_label.setText(hint)

    def _render_pixmap(self, pixmap: QPixmap) -> None:
        available = self.image_label.size()
        if available.width() < 8 or available.height() < 8:
            available = self.image_label.minimumSize()
            if available.width() < 8 or available.height() < 8:
                available = self.image_label.sizeHint()

        scaled = pixmap.scaled(
            max(available.width(), 100),
            max(available.height(), 100),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setText("")
        self.image_label.setPixmap(scaled)

    @staticmethod
    def _format_size(path: str) -> str:
        try:
            size = os.path.getsize(path)
        except OSError:
            return "Unknown size"
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._current_path and os.path.isfile(self._current_path):
            pixmap = QPixmap(self._current_path)
            if not pixmap.isNull():
                self._render_pixmap(pixmap)

    def _emit_apply(self) -> None:
        if self._current_path:
            self.apply_requested.emit(self._current_path)
