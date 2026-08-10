"""
Wallpaper Changer
=================

A modern Windows desktop application that rotates wallpapers on a schedule.
Runs as a GUI application with system tray support and no console window.

Build with PyInstaller:
    pyinstaller main.spec
"""

from src.app import run


if __name__ == "__main__":
    raise SystemExit(run())
