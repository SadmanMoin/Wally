"""Live wallpaper service: video playback on the desktop layer."""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.core.live_wallpaper.desktop_host import DesktopWallpaperHost
from src.services.logger import AppLogger

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v"}
LIVE_EXTENSIONS = VIDEO_EXTENSIONS


class LiveWallpaperService(QObject):
    """Plays a looping video as a live desktop wallpaper."""

    status_changed = Signal(bool)  # active
    error_occurred = Signal(str)
    media_changed = Signal(str)

    def __init__(
        self,
        logger: AppLogger,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._logger = logger
        self._active = False
        self._muted = True
        self._media_path: Optional[str] = None

        self._host = DesktopWallpaperHost()
        layout = QVBoxLayout(self._host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._video_widget: Optional[QWidget] = None
        self._player = None
        self._audio = None
        self._init_video_stack(layout)

    def _init_video_stack(self, layout: QVBoxLayout) -> None:
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget

            self._video_widget = QVideoWidget(self._host)
            self._video_widget.setStyleSheet("background-color: black;")
            self._video_widget.hide()
            layout.addWidget(self._video_widget)

            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._audio.setMuted(True)
            self._audio.setVolume(0.0)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(self._video_widget)
            self._player.setLoops(QMediaPlayer.Loops.Infinite)
            self._player.errorOccurred.connect(self._on_player_error)
        except Exception as exc:
            self._logger.warning("Video live wallpaper unavailable: %s", exc)
            self._video_widget = None
            self._player = None
            self._audio = None

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def media_path(self) -> Optional[str]:
        return self._media_path

    @property
    def muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool) -> None:
        self._muted = bool(muted)
        if self._audio is not None:
            self._audio.setMuted(self._muted)
            self._audio.setVolume(0.0 if self._muted else 0.35)

    @staticmethod
    def classify_media(path: str) -> Optional[str]:
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            return "video"
        return None

    def start(self, media_path: str) -> bool:
        """Start live wallpaper with the given video file."""
        if not media_path or not os.path.isfile(media_path):
            self.error_occurred.emit("Live wallpaper file not found.")
            return False

        if self.classify_media(media_path) is None:
            self.error_occurred.emit(
                "Unsupported live wallpaper format. Use a video file "
                "(MP4, WebM, MKV, MOV, or AVI)."
            )
            return False

        self.stop(emit_status=False)

        if not self._host.attach_to_desktop():
            message = (
                "Could not attach to the Windows desktop layer. "
                "Try restarting Explorer or running Wally again."
            )
            self._logger.error(message)
            self.error_occurred.emit(message)
            return False

        self._media_path = os.path.abspath(media_path)
        if not self._play_video(self._media_path):
            self.stop(emit_status=False)
            return False

        self._active = True
        self.status_changed.emit(True)
        self.media_changed.emit(self._media_path)
        self._logger.info("Live wallpaper started: %s", self._media_path)
        return True

    def stop(self, emit_status: bool = True) -> None:
        self._stop_playback()
        self._host.detach()
        was_active = self._active
        self._active = False
        if emit_status and was_active:
            self.status_changed.emit(False)
            self._logger.info("Live wallpaper stopped.")

    def _stop_playback(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player.setSource(QUrl())
        if self._video_widget is not None:
            self._video_widget.hide()

    def _play_video(self, path: str) -> bool:
        if self._player is None or self._video_widget is None:
            self.error_occurred.emit(
                "Video playback is not available. Install PySide6 multimedia support."
            )
            return False
        self._video_widget.show()
        self._host.refresh_geometry()
        self.set_muted(self._muted)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        return True

    @Slot(object, str)
    def _on_player_error(self, _error=None, error_string: str = "") -> None:
        message = error_string or "Video player error."
        self._logger.error("Live wallpaper video error: %s", message)
        self.error_occurred.emit(message)
