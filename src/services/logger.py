"""Centralized logging to file and UI listeners."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Callable, List, Optional


class AppLogger:
    """Application logger with rotating file output and UI callbacks."""

    _instance: Optional["AppLogger"] = None

    def __init__(self, log_dir: Optional[str] = None) -> None:
        self._listeners: List[Callable[[str, str], None]] = []
        self._logger = logging.getLogger("wallpaper_changer")
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()
        self._logger.propagate = False

        if log_dir is None:
            app_data = os.getenv("APPDATA") or os.path.expanduser("~")
            log_dir = os.path.join(app_data, "WallpaperChanger", "logs")

        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "app.log")

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=512_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        self._logger.addHandler(file_handler)
        self.log_path = log_path

    @classmethod
    def instance(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_listener(self, callback: Callable[[str, str], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _emit(self, level: str, message: str) -> None:
        for listener in list(self._listeners):
            listener(level, message)

    def info(self, message: str, *args) -> None:
        formatted = message % args if args else message
        self._logger.info(formatted)
        self._emit("INFO", formatted)

    def warning(self, message: str, *args) -> None:
        formatted = message % args if args else message
        self._logger.warning(formatted)
        self._emit("WARNING", formatted)

    def error(self, message: str, *args) -> None:
        formatted = message % args if args else message
        self._logger.error(formatted)
        self._emit("ERROR", formatted)
