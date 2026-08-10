"""Application icon helpers."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap


def load_app_icon() -> QIcon:
    """Load the application icon from resources or generate a fallback."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icon_path = os.path.join(base_dir, "resources", "icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)

    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor("#0078D4"))
    gradient.setColorAt(1, QColor("#005A9E"))
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, size - 8, size - 8, 14, 14)

    painter.setPen(QColor("#FFFFFF"))
    painter.setBrush(QColor(255, 255, 255, 210))
    margin = size // 5
    painter.drawRoundedRect(
        margin,
        margin,
        size - 2 * margin,
        size - 2 * margin,
        8,
        8,
    )
    painter.end()
    return QIcon(pixmap)
