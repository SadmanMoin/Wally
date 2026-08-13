"""Lightweight chart widgets for usage statistics (no extra dependencies)."""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from src.ui.theme import get_current_palette

# Soft professional bar colors (Windows-ish blues/teals)
BAR_COLORS = [
    QColor("#0078D4"),
    QColor("#107C10"),
    QColor("#8764B8"),
    QColor("#D83B01"),
    QColor("#038387"),
    QColor("#C239B3"),
    QColor("#00B7C3"),
    QColor("#CA5010"),
]

# Brighter variants for dark themes so bars stay visible
BAR_COLORS_DARK = [
    QColor("#4CC2FF"),
    QColor("#6CCB5F"),
    QColor("#B4A0E5"),
    QColor("#FF8B60"),
    QColor("#30D5C8"),
    QColor("#E98AD9"),
    QColor("#5CE1E6"),
    QColor("#FF9F5A"),
]


def _theme_colors() -> tuple[QColor, QColor, QColor, QColor, QColor, list[QColor]]:
    """Return text, muted, track, border, accent, and bar palette for current theme."""
    palette = get_current_palette()
    text = QColor(palette.text)
    muted = QColor(palette.text_muted)
    # Lift muted text a bit more on dark themes for chart readability
    if palette.is_dark:
        muted = QColor(palette.text_secondary)
        if muted.lightness() < 170:
            muted = QColor(
                min(255, muted.red() + 40),
                min(255, muted.green() + 40),
                min(255, muted.blue() + 40),
            )
        if text.lightness() < 200:
            text = QColor("#F2F2F5")
        track = QColor(palette.bg_hover)
        bars = BAR_COLORS_DARK
    else:
        track = QColor("#F0F0F0")
        bars = BAR_COLORS
    border = QColor(palette.border)
    accent = QColor(palette.accent)
    return text, muted, track, border, accent, bars


class HorizontalBarChart(QWidget):
    """Horizontal bars for top applications by usage time."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, float, str]] = []  # label, value, display
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def set_data(self, items: Sequence[Tuple[str, float, str]]) -> None:
        self._items = list(items)[:8]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        text_color, muted_color, track_color, _border, _accent, bars = _theme_colors()

        if not self._items:
            painter.setPen(muted_color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No usage data yet")
            return

        max_val = max(v for _, v, _ in self._items) or 1.0
        row_h = max(24, rect.height() // max(len(self._items), 1))
        label_w = min(150, rect.width() // 3)
        value_w = 72
        bar_area = rect.width() - label_w - value_w - 16

        font = QFont(self.font())
        font.setPointSize(9)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        for index, (label, value, display) in enumerate(self._items):
            y = rect.top() + index * row_h
            color = bars[index % len(bars)]

            painter.setPen(text_color)
            text = label if len(label) <= 18 else label[:16] + "…"
            painter.drawText(
                QRectF(rect.left(), y, label_w - 8, row_h - 4),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                text,
            )

            bar_x = rect.left() + label_w
            track = QRectF(bar_x, y + 6, bar_area, max(10, row_h - 14))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(track_color)
            painter.drawRoundedRect(track, 4, 4)

            width = bar_area * (value / max_val)
            fill = QRectF(bar_x, y + 6, max(4.0, width), max(10, row_h - 14))
            painter.setBrush(color)
            painter.drawRoundedRect(fill, 4, 4)

            painter.setPen(muted_color)
            painter.drawText(
                QRectF(bar_x + bar_area + 8, y, value_w, row_h - 4),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                display,
            )


class VerticalBarChart(QWidget):
    """Daily usage trend as clickable vertical bars."""

    # Emits the calendar date for the clicked day column.
    day_clicked = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # label, seconds, display, date
        self._items: List[Tuple[str, float, str, Optional[date]]] = []
        self._hit_regions: List[Tuple[QRectF, date, str, float]] = []
        self._selected_day: Optional[date] = None
        self._hover_index: int = -1
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def set_data(
        self,
        items: Sequence[Tuple[str, float, str, Optional[date]]],
    ) -> None:
        self._items = list(items)
        # Keep selection if still present
        if self._selected_day is not None:
            days = {item[3] for item in self._items if item[3] is not None}
            if self._selected_day not in days:
                self._selected_day = None
        self.update()

    def set_selected_day(self, day: Optional[date]) -> None:
        self._selected_day = day
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -32)
        text_color, muted_color, track_color, border, accent, _bars = _theme_colors()
        self._hit_regions = []

        if not self._items:
            painter.setPen(muted_color)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No trend data yet")
            return

        max_val = max(v for _, v, _, _ in self._items) or 1.0
        n = len(self._items)
        gap = 4 if n > 14 else 6
        bar_w = max(8.0, (rect.width() - gap * (n - 1)) / n)

        painter.setPen(QPen(border, 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        font = QFont(self.font())
        font.setPointSize(8)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        for index, (label, value, display, day) in enumerate(self._items):
            x = rect.left() + index * (bar_w + gap)
            height = 0 if max_val <= 0 else (rect.height() * (value / max_val))
            # Clickable column covers full height for easier hits
            hit = QRectF(x - 1, rect.top(), bar_w + 2, rect.height() + 28)
            if day is not None:
                self._hit_regions.append((hit, day, display, value))

            bar = QRectF(x, rect.bottom() - max(height, 3.0 if value > 0 else 1.0), bar_w, max(3.0 if value > 0 else 1.0, height))
            selected = day is not None and day == self._selected_day
            hovered = index == self._hover_index

            color = QColor(accent)
            if selected:
                color = color.lighter(120) if color.lightness() < 180 else color.darker(115)
            elif hovered:
                color = color.lighter(115) if color.lightness() < 180 else color.darker(110)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(bar, 3, 3)

            if selected:
                painter.setPen(QPen(text_color, 1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(bar.adjusted(-1, -1, 1, 1), 4, 4)

            show_label = n <= 10 or index % max(1, n // 7) == 0 or index == n - 1 or selected
            if show_label:
                painter.setPen(text_color if selected else muted_color)
                painter.drawText(
                    QRectF(x - 10, rect.bottom() + 4, bar_w + 20, 18),
                    int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                    label,
                )

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        pos = event.position() if hasattr(event, "position") else QPointF(event.pos())
        hover = -1
        for index, (rect, day, display, _value) in enumerate(self._hit_regions):
            if rect.contains(pos):
                hover = index
                # Match bar index for highlight (regions align with items that have dates).
                for item_index, item in enumerate(self._items):
                    if item[3] == day:
                        hover = item_index
                        break
                tip = f"{day.strftime('%A, %b %d')}: {display}"
                global_pos = (
                    event.globalPosition().toPoint()
                    if hasattr(event, "globalPosition")
                    else event.globalPos()
                )
                QToolTip.showText(global_pos, tip, self)
                break
        if hover != self._hover_index:
            self._hover_index = hover
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hover_index = -1
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        pos = event.position() if hasattr(event, "position") else QPointF(event.pos())
        for rect, day, _display, _value in self._hit_regions:
            if rect.contains(pos):
                self._selected_day = day
                self.update()
                self.day_clicked.emit(day)
                return
        super().mousePressEvent(event)


class DistributionChart(QWidget):
    """Simple stacked horizontal distribution of usage share."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, float]] = []
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, items: Sequence[Tuple[str, float]]) -> None:
        self._items = list(items)[:8]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -32)
        text_color, muted_color, _track, _border, _accent, bars = _theme_colors()

        if not self._items:
            painter.setPen(muted_color)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No distribution data")
            return

        total = sum(v for _, v in self._items) or 1.0
        x = float(rect.left())
        painter.setPen(Qt.PenStyle.NoPen)

        for index, (_label, value) in enumerate(self._items):
            width = rect.width() * (value / total)
            segment = QRectF(x, rect.top(), max(2.0, width), rect.height())
            painter.setBrush(bars[index % len(bars)])
            painter.drawRect(segment)
            x += width

        font = QFont(self.font())
        font.setPointSize(8)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        legend_y = rect.bottom() + 10
        lx = rect.left()
        for index, (label, value) in enumerate(self._items[:5]):
            color = bars[index % len(bars)]
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(lx, legend_y, 10, 10), 2, 2)
            painter.setPen(text_color)
            text = f"{label} {value / total * 100:.0f}%"
            painter.drawText(int(lx + 14), int(legend_y + 10), text)
            lx += painter.fontMetrics().horizontalAdvance(text) + 28
