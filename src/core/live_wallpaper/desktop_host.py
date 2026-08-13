"""Host a Qt window as a Windows live wallpaper (behind desktop icons)."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowExW.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
]
user32.FindWindowExW.restype = wintypes.HWND
user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_ulong),
]
user32.SendMessageTimeoutW.restype = wintypes.LPARAM
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.SetParent.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL

SMTO_NORMAL = 0x0000
SPI_SETDESKWALLPAPER_MSG = 0x052C  # undocumented Progman spawn WorkerW
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
SW_SHOW = 5
SM_CXSCREEN = 0
SM_CYSCREEN = 1


def _spawn_workerw(progman: int) -> None:
    """Ask Progman to create the WorkerW wallpaper surface (Windows quirk)."""
    result = ctypes.c_ulong(0)
    # Classic spawn
    user32.SendMessageTimeoutW(
        progman,
        SPI_SETDESKWALLPAPER_MSG,
        0,
        0,
        SMTO_NORMAL,
        1000,
        ctypes.byref(result),
    )
    # Windows 10/11 alternate parameters used by several wallpaper apps
    user32.SendMessageTimeoutW(
        progman,
        SPI_SETDESKWALLPAPER_MSG,
        0x0000000D,
        0x00000001,
        SMTO_NORMAL,
        1000,
        ctypes.byref(result),
    )


def _find_workerw() -> Optional[int]:
    """Return HWND of the WorkerW layer used for desktop wallpapers."""
    if sys.platform != "win32":
        return None

    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return None

    _spawn_workerw(int(progman))

    found = {"after_defview": 0, "any_worker": 0}

    @EnumWindowsProc
    def _callback(hwnd, _lparam):
        class_name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_name, 256)
        name = class_name.value

        shell_view = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if shell_view:
            # WorkerW created after the desktop list view (preferred target).
            worker = user32.FindWindowExW(0, hwnd, "WorkerW", None)
            if worker:
                found["after_defview"] = int(worker)

        if name == "WorkerW" and not found["any_worker"]:
            # Fallback: a WorkerW that does not host the icon view.
            if not user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None):
                found["any_worker"] = int(hwnd)
        return True

    # Keep a reference so the callback is not garbage-collected during EnumWindows.
    _find_workerw._enum_cb = _callback  # type: ignore[attr-defined]
    user32.EnumWindows(_callback, 0)

    if found["after_defview"]:
        return found["after_defview"]
    if found["any_worker"]:
        return found["any_worker"]
    # Last resort: parent under Progman (works on some setups).
    return int(progman)


def primary_screen_size() -> tuple[int, int]:
    return (
        int(user32.GetSystemMetrics(SM_CXSCREEN)),
        int(user32.GetSystemMetrics(SM_CYSCREEN)),
    )


class DesktopWallpaperHost(QWidget):
    """Fullscreen widget reparented under Windows desktop WorkerW."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("liveWallpaperHost")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._attached = False
        self._worker_hwnd: Optional[int] = None

        width, height = primary_screen_size()
        self.setGeometry(0, 0, width, height)

    @property
    def is_attached(self) -> bool:
        return self._attached

    def attach_to_desktop(self) -> bool:
        """Parent this window under WorkerW so it sits behind icons."""
        if sys.platform != "win32":
            return False

        worker = _find_workerw()
        if not worker:
            # Retry once — Explorer sometimes needs a second spawn.
            worker = _find_workerw()
        if not worker:
            return False

        self.show()
        hwnd = int(self.winId())
        user32.SetParent(hwnd, worker)
        width, height = primary_screen_size()
        self.setGeometry(0, 0, width, height)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            width,
            height,
            SWP_NOZORDER | SWP_SHOWWINDOW,
        )
        user32.ShowWindow(hwnd, SW_SHOW)
        self._worker_hwnd = worker
        self._attached = True
        return True

    def detach(self) -> None:
        """Hide and detach from the desktop layer."""
        if sys.platform == "win32" and self._attached:
            try:
                hwnd = int(self.winId())
                # Reparent back to desktop root before hide.
                user32.SetParent(hwnd, 0)
            except Exception:
                pass
        self.hide()
        self._attached = False
        self._worker_hwnd = None

    def refresh_geometry(self) -> None:
        width, height = primary_screen_size()
        self.setGeometry(0, 0, width, height)
        if self._attached and sys.platform == "win32":
            hwnd = int(self.winId())
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                width,
                height,
                SWP_NOZORDER | SWP_SHOWWINDOW,
            )
