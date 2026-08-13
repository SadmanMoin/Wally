"""
Wally
=====

A modern Windows desktop application that rotates wallpapers on a schedule
and tracks local application usage. Runs with system tray support.

Build with PyInstaller:
    pyinstaller main.spec
"""

from src.app import run


if __name__ == "__main__":
    raise SystemExit(run())
