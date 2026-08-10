"""Background scheduler that rotates wallpapers independently of the UI."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot

from src.core.wallpaper_controller import WallpaperController
from src.core.windows_wallpaper import set_windows_wallpaper
from src.services.logger import AppLogger


class WallpaperService(QObject):
    """Runs the wallpaper timer and emits state changes to the UI and tray."""

    wallpaper_changed = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    STATUS_STOPPED = "stopped"
    STATUS_RUNNING = "running"
    STATUS_PAUSED = "paused"

    def __init__(
        self,
        controller: WallpaperController,
        logger: AppLogger,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._logger = logger
        self._random_mode = False
        self._interval_seconds = 60
        self._status = self.STATUS_STOPPED
        self._current_image: Optional[str] = None

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.CoarseTimer)
        self._timer.timeout.connect(self._on_timer)

    @property
    def status(self) -> str:
        return self._status

    @property
    def current_image(self) -> Optional[str]:
        return self._current_image

    @property
    def is_active(self) -> bool:
        return self._status == self.STATUS_RUNNING

    @property
    def is_paused(self) -> bool:
        return self._status == self.STATUS_PAUSED

    @property
    def interval_seconds(self) -> int:
        """Configured interval between wallpaper changes."""
        return self._interval_seconds

    @property
    def random_mode(self) -> bool:
        """Whether the next wallpaper is chosen randomly."""
        return self._random_mode

    def remaining_seconds(self) -> Optional[int]:
        """Seconds until the next scheduled change, or None when not running."""
        if self._status != self.STATUS_RUNNING or not self._timer.isActive():
            return None
        remaining_ms = self._timer.remainingTime()
        if remaining_ms < 0:
            return None
        return max(0, (remaining_ms + 999) // 1000)

    def configure(self, interval_seconds: int, random_mode: bool) -> None:
        self._interval_seconds = max(5, interval_seconds)
        self._random_mode = random_mode
        if self._timer.isActive():
            self._timer.start(self._interval_seconds * 1000)

    def start(self) -> None:
        if not self._controller.images:
            raise RuntimeError("Load at least one wallpaper folder before starting.")

        self._timer.start(self._interval_seconds * 1000)
        self._set_status(self.STATUS_RUNNING)
        self._logger.info("Scheduler started.")
        self.apply_next_wallpaper()

    def pause(self) -> None:
        if self._status != self.STATUS_RUNNING:
            return
        self._timer.stop()
        self._set_status(self.STATUS_PAUSED)
        self._logger.info("Scheduler paused.")

    def resume(self) -> None:
        if self._status != self.STATUS_PAUSED:
            return
        self._timer.start(self._interval_seconds * 1000)
        self._set_status(self.STATUS_RUNNING)
        self._logger.info("Scheduler resumed.")

    def stop(self) -> None:
        if self._status == self.STATUS_STOPPED:
            return
        self._timer.stop()
        self._set_status(self.STATUS_STOPPED)
        self._logger.info("Scheduler stopped.")

    @Slot()
    def apply_next_wallpaper(self) -> None:
        """Immediately apply the next wallpaper."""
        try:
            image_path = self._controller.next_image(self._random_mode)
        except Exception as exc:
            message = f"Could not select the next wallpaper: {exc}"
            self._logger.error(message)
            self.error_occurred.emit(message)
            self.stop()
            return

        success, error_message = set_windows_wallpaper(image_path)
        if not success:
            message = error_message or "Unknown wallpaper error."
            self._logger.error(message)
            self.error_occurred.emit(message)
            return

        self._current_image = image_path
        self._controller.sync_preview_to_path(image_path)
        self._logger.info("Wallpaper changed to %s", image_path)
        self.wallpaper_changed.emit(image_path)

    @Slot()
    def _on_timer(self) -> None:
        self.apply_next_wallpaper()

    def _set_status(self, status: str) -> None:
        self._status = status
        self.status_changed.emit(status)
