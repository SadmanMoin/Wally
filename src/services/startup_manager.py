"""Windows startup registration helpers."""

from __future__ import annotations

import os
import sys
from typing import Optional, Tuple


class StartupManager:
    """Manage the application Run registry entry."""

    REGISTRY_VALUE_NAME = "WallpaperChanger"

    @staticmethod
    def resolve_launch_command() -> str:
        """Return the command Windows should run on logon."""
        executable = os.path.realpath(sys.argv[0])
        if executable.lower().endswith(".exe"):
            return f'"{executable}"'
        return f'"{sys.executable}" "{executable}"'

    @classmethod
    def set_enabled(cls, enabled: bool) -> Tuple[bool, Optional[str]]:
        """Enable or disable startup registration."""
        try:
            import winreg
        except ImportError:
            return False, "Windows registry support is unavailable on this platform."

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
            ) as key:
                if enabled:
                    winreg.SetValueEx(
                        key,
                        cls.REGISTRY_VALUE_NAME,
                        0,
                        winreg.REG_SZ,
                        cls.resolve_launch_command(),
                    )
                else:
                    try:
                        winreg.DeleteValue(key, cls.REGISTRY_VALUE_NAME)
                    except FileNotFoundError:
                        pass
            return True, None
        except PermissionError:
            return False, "Insufficient permissions to modify startup settings."
        except OSError as exc:
            return False, f"Could not update startup settings: {exc}"

    @classmethod
    def is_enabled(cls) -> bool:
        """Return True when the app is registered for startup."""
        try:
            import winreg
        except ImportError:
            return False

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ,
            ) as key:
                winreg.QueryValueEx(key, cls.REGISTRY_VALUE_NAME)
                return True
        except OSError:
            return False
