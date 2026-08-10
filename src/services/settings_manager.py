"""Persistent application settings."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QSettings


class SettingsManager:
    """Thin wrapper around QSettings for typed access."""

    ORGANIZATION = "WallpaperChanger"
    APPLICATION = "DesktopWallpaper"

    def __init__(self) -> None:
        self._settings = QSettings(self.ORGANIZATION, self.APPLICATION)

    def get_folders(self) -> List[str]:
        value = self._settings.value("folders", [])
        if isinstance(value, list):
            folders = [folder for folder in value if isinstance(folder, str)]
            if folders:
                return folders

        legacy_folder = self._settings.value("folder", type=str)
        if legacy_folder:
            self.set_folders([legacy_folder])
            return [legacy_folder]

        return []

    def set_folders(self, folders: List[str]) -> None:
        self._settings.setValue("folders", folders)

    def get_files(self) -> List[str]:
        """Return individually selected image file paths."""
        value = self._settings.value("files", [])
        if isinstance(value, list):
            return [path for path in value if isinstance(path, str) and path]
        if isinstance(value, str) and value:
            return [value]
        return []

    def set_files(self, files: List[str]) -> None:
        self._settings.setValue("files", files)

    def get_interval(self) -> int:
        return int(self._settings.value("interval", 60))

    def set_interval(self, seconds: int) -> None:
        self._settings.setValue("interval", seconds)

    def get_mode(self) -> str:
        mode = self._settings.value("mode", "Sequential")
        return mode if mode in {"Sequential", "Random"} else "Sequential"

    def set_mode(self, mode: str) -> None:
        self._settings.setValue("mode", mode)

    def get_startup_enabled(self) -> bool:
        return self._settings.value("startup", False, type=bool)

    def set_startup_enabled(self, enabled: bool) -> None:
        self._settings.setValue("startup", enabled)

    def get_scheduler_active(self) -> bool:
        return self._settings.value("scheduler_active", False, type=bool)

    def set_scheduler_active(self, active: bool) -> None:
        self._settings.setValue("scheduler_active", active)

    def get_scheduler_status(self) -> str:
        status = self._settings.value("scheduler_status", "stopped")
        if status in {"stopped", "running", "paused"}:
            return status
        return "running" if self.get_scheduler_active() else "stopped"

    def set_scheduler_status(self, status: str) -> None:
        self._settings.setValue("scheduler_status", status)
        self._settings.setValue("scheduler_active", status in {"running", "paused"})

    def sync(self) -> None:
        self._settings.sync()
