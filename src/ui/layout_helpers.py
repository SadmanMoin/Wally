"""Responsive layout utilities and shared spacing constants."""

from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLayout,
    QLayoutItem,
    QPushButton,
    QSizePolicy,
    QStyle,
    QWidget,
)

# Shared spacing used across the application (logical pixels, DPI-aware).
LAYOUT_MARGIN = 16
LAYOUT_SPACING = 12
CARD_MARGIN = 16
CARD_SPACING = 12
COLUMN_BREAKPOINT = 860


class FlowLayout(QLayout):
    """Layout that wraps widgets to the next row when horizontal space runs out."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        margin: int = 0,
        h_spacing: int = -1,
        v_spacing: int = -1,
    ) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def addWidget(self, widget: QWidget) -> None:
        """Add a widget and reparent it so it actually appears on screen."""
        from PySide6.QtWidgets import QWidgetItem

        # Critical: without addChildWidget, buttons have no parent and stay invisible.
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))

    def horizontalSpacing(self) -> int:
        if self._h_spacing >= 0:
            return self._h_spacing
        return self._smart_spacing(QStyle.PixelMetric.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self) -> int:
        if self._v_spacing >= 0:
            return self._v_spacing
        return self._smart_spacing(QStyle.PixelMetric.PM_LayoutVerticalSpacing)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _smart_spacing(self, metric: QStyle.PixelMetric) -> int:
        parent = self.parentWidget()
        if parent is None:
            return LAYOUT_SPACING
        return parent.style().pixelMetric(metric, None, parent)

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(),
            margins.top(),
            -margins.right(),
            -margins.bottom(),
        )

        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            widget = item.widget()
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective.right() and line_height > 0:
                x = effective.x()
                y += line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()


class ResponsiveColumns(QWidget):
    """Place two panels side-by-side or stacked based on available width."""

    def __init__(
        self,
        left: QWidget,
        right: QWidget,
        breakpoint: int = COLUMN_BREAKPOINT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._left = left
        self._right = right
        self._breakpoint = breakpoint
        self._mode: Optional[str] = None
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(LAYOUT_SPACING)
        self._apply_layout(force=True)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_layout()

    def _apply_layout(self, force: bool = False) -> None:
        mode = "vertical" if self.width() < self._breakpoint else "horizontal"
        if not force and mode == self._mode:
            return

        self._mode = mode
        self._grid.removeWidget(self._left)
        self._grid.removeWidget(self._right)

        if mode == "horizontal":
            self._grid.addWidget(self._left, 0, 0)
            self._grid.addWidget(self._right, 0, 1)
            self._grid.setColumnStretch(0, 3)
            self._grid.setColumnStretch(1, 4)
            self._grid.setRowStretch(0, 1)
            self._grid.setRowStretch(1, 0)
        else:
            self._grid.addWidget(self._left, 0, 0)
            self._grid.addWidget(self._right, 1, 0)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)
            self._grid.setRowStretch(0, 0)
            self._grid.setRowStretch(1, 1)


def configure_action_button(button: QPushButton) -> None:
    """Size a button from its text so labels stay centered and never clip."""
    metrics = button.fontMetrics()
    text_width = metrics.horizontalAdvance(button.text())
    padding = max(24, metrics.height())
    button.setMinimumWidth(text_width + padding)
    button.setMinimumHeight(metrics.height() + padding)
    button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)


def add_buttons_flow(parent_layout: QLayout, buttons: Iterable[QPushButton]) -> FlowLayout:
    """Add buttons to a wrapping flow layout with consistent spacing."""
    flow = FlowLayout(h_spacing=LAYOUT_SPACING, v_spacing=LAYOUT_SPACING)
    for button in buttons:
        configure_action_button(button)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        flow.addWidget(button)
    # Use addLayout so the nested layout is owned and widgets are laid out.
    if hasattr(parent_layout, "addLayout"):
        parent_layout.addLayout(flow)
    else:
        parent_layout.addItem(flow)
    return flow


def configure_expanding(widget: QWidget, vertical_stretch: bool = False) -> None:
    """Apply a standard expanding size policy."""
    vertical = (
        QSizePolicy.Policy.Expanding
        if vertical_stretch
        else QSizePolicy.Policy.Preferred
    )
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, vertical)


def apply_card_layout(layout: QGridLayout | QLayout) -> None:
    """Apply standard card margins and spacing."""
    if hasattr(layout, "setContentsMargins"):
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
    if hasattr(layout, "setSpacing"):
        layout.setSpacing(CARD_SPACING)
