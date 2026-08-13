"""Compact sidebar navigation for the main window."""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QFrame):
    """Vertical navigation rail with brand header and page buttons."""

    page_changed = Signal(str)

    def __init__(
        self,
        items: List[Tuple[str, str]],
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            items: List of (page_id, label) pairs.
        """
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        brand = QLabel("Wally")
        brand.setObjectName("sidebarBrand")
        brand.setWordWrap(True)

        tagline = QLabel("Wallpaper & usage utility")
        tagline.setObjectName("sidebarTagline")
        tagline.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(4)
        layout.addWidget(brand)
        layout.addWidget(tagline)
        layout.addSpacing(18)

        for page_id, label in items:
            button = QPushButton(label)
            button.setObjectName("navItem")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.clicked.connect(self._make_handler(page_id))
            self._group.addButton(button)
            self._buttons[page_id] = button
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel("Running in system tray when closed")
        footer.setObjectName("sidebarTagline")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        if items:
            first_id = items[0][0]
            self._buttons[first_id].setChecked(True)

    def _make_handler(self, page_id: str) -> Callable[[], None]:
        def _handler() -> None:
            self.page_changed.emit(page_id)

        return _handler

    def set_current(self, page_id: str) -> None:
        button = self._buttons.get(page_id)
        if button is not None:
            button.setChecked(True)
