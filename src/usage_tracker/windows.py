"""Windows foreground application and idle-time helpers via native APIs."""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from typing import Optional

from src.usage_tracker.models import ForegroundApp

# Process access rights
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetLastInputInfo.restype = wintypes.BOOL
kernel32.GetTickCount.restype = wintypes.DWORD


# Lightweight cache so we don't reopen process handles every poll for same PID.
_process_cache: dict[int, tuple[str, str]] = {}
_CACHE_MAX = 64


def _window_title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _process_image_path(pid: int) -> Optional[str]:
    if pid <= 0:
        return None

    access = PROCESS_QUERY_LIMITED_INFORMATION
    handle = kernel32.OpenProcess(access, False, pid)
    if not handle:
        # Fallback for older processes / permissions
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False,
            pid,
        )
    if not handle:
        return None

    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        if not ok:
            return None
        return buffer.value
    finally:
        kernel32.CloseHandle(handle)


def _display_name_from_path(path: str) -> tuple[str, str]:
    """Return (process_name, application_name) from an executable path."""
    process_name = os.path.basename(path) if path else "Unknown"
    stem = os.path.splitext(process_name)[0] if process_name else "Unknown"
    # Prefer a slightly cleaner application label without .exe
    application_name = stem.replace("_", " ").strip() or process_name
    # Title-case short names (chrome -> Chrome) but keep mixed-case names (Code)
    if application_name.islower() or application_name.isupper():
        application_name = application_name.title()
    return process_name, application_name


def get_foreground_app() -> Optional[ForegroundApp]:
    """Return the currently focused application, or None if unavailable."""
    if sys.platform != "win32":
        return None

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return None

    cached = _process_cache.get(pid.value)
    if cached is None:
        image_path = _process_image_path(pid.value)
        if image_path:
            process_name, application_name = _display_name_from_path(image_path)
        else:
            process_name, application_name = "Unknown", "Unknown"
        _process_cache[pid.value] = (process_name, application_name)
        if len(_process_cache) > _CACHE_MAX:
            # Drop arbitrary oldest-ish entries
            for key in list(_process_cache.keys())[:16]:
                _process_cache.pop(key, None)
    else:
        process_name, application_name = cached

    return ForegroundApp(
        process_name=process_name,
        application_name=application_name,
        process_id=int(pid.value),
        window_title=_window_title(hwnd),
    )


def get_idle_seconds() -> float:
    """Seconds since the last keyboard/mouse input (user idle time)."""
    if sys.platform != "win32":
        return 0.0

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0

    tick = kernel32.GetTickCount()
    # Handle 49.7-day tick wrap approximately
    idle_ms = (tick - info.dwTime) & 0xFFFFFFFF
    return idle_ms / 1000.0
