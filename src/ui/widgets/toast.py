"""In-app toast / snackbar notifications."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget


class ToastHost(QWidget):
    """Hosts transient toast messages over a parent window."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        self._toast = QFrame(self)
        self._toast.setObjectName("toast")
        self._toast.setProperty("level", "info")

        self._message = QLabel()
        self._message.setObjectName("toastMessage")
        self._message.setWordWrap(True)
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout(self._toast)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.addWidget(self._message)

        self._opacity = QGraphicsOpacityEffect(self._toast)
        self._toast.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(180)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

    def show_message(self, message: str, level: str = "info", duration_ms: int = 2800) -> None:
        self._message.setText(message)
        self._toast.setProperty("level", level)
        self._toast.style().unpolish(self._toast)
        self._toast.style().polish(self._toast)

        self._reposition()
        self.show()
        self.raise_()

        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(1.0)
        self._fade.start()

        self._hide_timer.start(max(1200, duration_ms))

    def _fade_out(self) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._on_fade_finished)
        self._fade.start()

    def _on_fade_finished(self) -> None:
        try:
            self._fade.finished.disconnect(self._on_fade_finished)
        except (RuntimeError, TypeError):
            pass
        if self._opacity.opacity() < 0.05:
            self.hide()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return

        self.setGeometry(parent.rect())
        self._toast.adjustSize()
        toast_w = min(max(self._toast.sizeHint().width(), 220), parent.width() - 40)
        self._toast.setFixedWidth(toast_w)
        self._toast.adjustSize()

        x = (parent.width() - self._toast.width()) // 2
        y = parent.height() - self._toast.height() - 28
        self._toast.move(max(12, x), max(12, y))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self.isVisible():
            self._reposition()
