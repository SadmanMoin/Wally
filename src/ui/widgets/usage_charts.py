"""Lightweight chart widgets for usage statistics (no extra dependencies)."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

# Soft professional palette (Windows-ish blues/teals)
PALETTE = [
    QColor("#0078D4"),
    QColor("#107C10"),
    QColor("#8764B8"),
    QColor("#D83B01"),
    QColor("#038387"),
    QColor("#C239B3"),
    QColor("#00B7C3"),
    QColor("#CA5010"),
]


class HorizontalBarChart(QWidget):
    """Horizontal bars for top applications by usage time."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, float, str]] = []  # label, value, display
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, items: Sequence[Tuple[str, float, str]]) -> None:
        self._items = list(items)[:8]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)

        if not self._items:
            painter.setPen(QColor("#6B6B6B"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No usage data yet")
            return

        max_val = max(v for _, v, _ in self._items) or 1.0
        row_h = max(22, rect.height() // max(len(self._items), 1))
        label_w = min(140, rect.width() // 3)
        value_w = 70
        bar_area = rect.width() - label_w - value_w - 16

        font = QFont(self.font())
        font.setPointSize(9)
        painter.setFont(font)

        for index, (label, value, display) in enumerate(self._items):
            y = rect.top() + index * row_h
            color = PALETTE[index % len(PALETTE)]

            # Label
            painter.setPen(QColor("#1A1A1A"))
            text = label if len(label) <= 18 else label[:16] + "…"
            painter.drawText(
                QRectF(rect.left(), y, label_w - 8, row_h - 4),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                text,
            )

            # Track
            bar_x = rect.left() + label_w
            track = QRectF(bar_x, y + 6, bar_area, max(10, row_h - 14))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F0F0F0"))
            painter.drawRoundedRect(track, 4, 4)

            # Fill
            width = bar_area * (value / max_val)
            fill = QRectF(bar_x, y + 6, max(4.0, width), max(10, row_h - 14))
            painter.setBrush(color)
            painter.drawRoundedRect(fill, 4, 4)

            # Value
            painter.setPen(QColor("#6B6B6B"))
            painter.drawText(
                QRectF(bar_x + bar_area + 8, y, value_w, row_h - 4),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                display,
            )


class VerticalBarChart(QWidget):
    """Daily usage trend as vertical bars."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, float, str]] = []
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_data(self, items: Sequence[Tuple[str, float, str]]) -> None:
        self._items = list(items)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -28)

        if not self._items:
            painter.setPen(QColor("#6B6B6B"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No trend data yet")
            return

        max_val = max(v for _, v, _ in self._items) or 1.0
        n = len(self._items)
        gap = 4 if n > 14 else 6
        bar_w = max(6.0, (rect.width() - gap * (n - 1)) / n)

        # Axis line
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        font = QFont(self.font())
        font.setPointSize(8)
        painter.setFont(font)

        for index, (label, value, _display) in enumerate(self._items):
            x = rect.left() + index * (bar_w + gap)
            height = 0 if max_val <= 0 else (rect.height() * (value / max_val))
            bar = QRectF(x, rect.bottom() - height, bar_w, max(1.0, height))
            color = PALETTE[0]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(bar, 3, 3)

            # Sparse labels for readability
            show_label = n <= 10 or index % max(1, n // 7) == 0 or index == n - 1
            if show_label:
                painter.setPen(QColor("#6B6B6B"))
                painter.drawText(
                    QRectF(x - 8, rect.bottom() + 4, bar_w + 16, 18),
                    int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                    label,
                )


class DistributionChart(QWidget):
    """Simple stacked horizontal distribution of usage share."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, float]] = []
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, items: Sequence[Tuple[str, float]]) -> None:
        self._items = list(items)[:8]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -28)

        if not self._items:
            painter.setPen(QColor("#6B6B6B"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No distribution data")
            return

        total = sum(v for _, v in self._items) or 1.0
        x = float(rect.left())
        painter.setPen(Qt.PenStyle.NoPen)

        for index, (_label, value) in enumerate(self._items):
            width = rect.width() * (value / total)
            segment = QRectF(x, rect.top(), max(2.0, width), rect.height())
            painter.setBrush(PALETTE[index % len(PALETTE)])
            painter.drawRect(segment)
            x += width

        # Legend
        font = QFont(self.font())
        font.setPointSize(8)
        painter.setFont(font)
        legend_y = rect.bottom() + 8
        lx = rect.left()
        for index, (label, value) in enumerate(self._items[:5]):
            color = PALETTE[index % len(PALETTE)]
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(lx, legend_y, 10, 10), 2, 2)
            painter.setPen(QColor("#6B6B6B"))
            text = f"{label} {value / total * 100:.0f}%"
            painter.drawText(int(lx + 14), int(legend_y + 10), text)
            lx += painter.fontMetrics().horizontalAdvance(text) + 28
