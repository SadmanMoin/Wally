"""System tray integration."""

from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayIconController:
    """Manage tray icon visibility and menu actions."""

    def __init__(self, icon: QIcon, parent: Optional[QWidget] = None) -> None:
        self._parent = parent
        self.tray_icon = QSystemTrayIcon(icon, parent)
        self.tray_icon.setToolTip("Wally")

        self.action_open = QAction("Open", parent)
        self.action_change_now = QAction("Change Wallpaper Now", parent)
        self.action_pause = QAction("Pause Scheduler", parent)
        self.action_resume = QAction("Resume Scheduler", parent)
        self.action_exit = QAction("Exit", parent)

        menu = QMenu(parent)
        menu.addAction(self.action_open)
        menu.addAction(self.action_change_now)
        menu.addSeparator()
        menu.addAction(self.action_pause)
        menu.addAction(self.action_resume)
        menu.addSeparator()
        menu.addAction(self.action_exit)
        self.tray_icon.setContextMenu(menu)

        self._update_scheduler_actions("stopped")

    def show(self) -> None:
        self.tray_icon.show()

    def connect_activated(self, callback) -> None:
        self.tray_icon.activated.connect(callback)

    def notify(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information) -> None:
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, 2500)

    def update_scheduler_actions(self, status: str) -> None:
        self._update_scheduler_actions(status)

    def _update_scheduler_actions(self, status: str) -> None:
        running = status == "running"
        paused = status == "paused"
        self.action_pause.setEnabled(running)
        self.action_resume.setEnabled(paused)
