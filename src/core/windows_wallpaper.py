"""Windows desktop wallpaper integration via the native API."""

from __future__ import annotations

import ctypes
import os
from typing import Optional

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02


def set_windows_wallpaper(image_path: str) -> tuple[bool, Optional[str]]:
    """Apply an image as the desktop wallpaper.

    Returns a tuple of (success, error_message).
    """
    if not image_path:
        return False, "No image path provided."

    if not os.path.isfile(image_path):
        return False, f"Image file not found: {image_path}"

    try:
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            os.path.abspath(image_path),
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE,
        )
        if result == 0:
            return False, f"Windows API rejected wallpaper: {os.path.basename(image_path)}"
        return True, None
    except OSError as exc:
        return False, f"Failed to set wallpaper: {exc}"
