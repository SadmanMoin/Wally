"""Application bootstrap and lifecycle."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.live_wallpaper.service import LiveWallpaperService
from src.core.wallpaper_controller import WallpaperController
from src.core.wallpaper_service import WallpaperService
from src.services.logger import AppLogger
from src.services.settings_manager import SettingsManager
from src.ui.main_window import MainWindow
from src.ui.styles import WINDOWS11_STYLE
from src.usage_tracker.service import UsageTrackerService
from src.utils.icon_loader import load_app_icon


def hide_console_window() -> None:
    """Hide the attached console when launched via python.exe on Windows."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            ctypes.windll.user32.ShowWindow(console_window, 0)
    except OSError:
        pass


def create_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("Wally")
    app.setOrganizationName(SettingsManager.ORGANIZATION)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(WINDOWS11_STYLE)
    return app


def run() -> int:
    if sys.platform != "win32":
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Unsupported Platform",
            "Wally runs only on Windows.",
        )
        return 1

    hide_console_window()

    app = create_application()
    logger = AppLogger.instance()
    settings = SettingsManager()
    controller = WallpaperController()
    service = WallpaperService(controller, logger)
    live_service = LiveWallpaperService(logger=logger)
    live_service.set_muted(settings.get_live_muted())
    usage_service = UsageTrackerService(
        logger=logger,
        idle_timeout_seconds=settings.get_idle_timeout_minutes() * 60,
    )
    if settings.get_usage_tracking_enabled():
        usage_service.start()
    icon = load_app_icon()

    window = MainWindow(
        icon=icon,
        controller=controller,
        service=service,
        settings=settings,
        logger=logger,
        usage_service=usage_service,
        live_service=live_service,
    )
    window.show()

    # Restore live wallpaper after UI is ready (exclusive with static scheduler).
    if settings.get_live_enabled():
        media = settings.get_live_media_path()
        if media:
            window.start_live_wallpaper(media, restore=True)

    return app.exec()
