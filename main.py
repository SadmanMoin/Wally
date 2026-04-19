"""
Wallpaper Changer Application
=============================

This module defines a PySide6 application that allows users to select a
folder containing image files and automatically cycle the Windows desktop
background at a configurable interval. The application provides both
sequential and random modes, exposes a system tray icon, and can persist
user settings (selected folder, interval, mode and start‑on‑startup)
between sessions using QSettings.

The wallpaper is updated using the Windows API via `ctypes`. When the
wallpaper is changed a small log entry is added to the log area and a
status message is updated. A system tray icon allows quick access to the
start/stop functions and to exit the application when it is hidden.

Running the application on startup is implemented by writing a value to
``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`` via the winreg
module. If the operation fails (e.g. due to insufficient permissions) a
message is shown in the log.

To package this application into a self‑contained Windows executable use
PyInstaller. See the bottom of this file for an example command.

"""

import ctypes
import os
import random
import sys
import traceback
from typing import List, Optional

from PySide6.QtCore import QSettings, QTimer, Qt, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


def set_windows_wallpaper(image_path: str) -> bool:
    """Set the Windows desktop wallpaper to the specified image.

    This function uses the Windows API via ctypes to set the wallpaper. It
    broadcasts the change and updates the user profile so that the setting
    persists across sessions. If an exception occurs the function returns
    False.

    Parameters
    ----------
    image_path: str
        Absolute path to the image file to set as wallpaper.

    Returns
    -------
    bool
        True if the call succeeded, False otherwise.
    """
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDWININICHANGE = 0x02
    try:
        # Use SystemParametersInfoW to set the wallpaper and broadcast the change.
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE,
        )
        return True
    except Exception:
        return False


class WallpaperController:
    """Encapsulates logic for loading images and cycling through them.

    The controller maintains a list of absolute file paths pointing to
    supported image types within a selected directory. It exposes methods to
    retrieve the next image in either sequential or random order and keeps
    track of the current index when running in sequential mode.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    def __init__(self) -> None:
        self.folder: Optional[str] = None
        self.images: List[str] = []
        self.index: int = 0

    def load_folder(self, folder: str) -> None:
        """Scan the provided folder for supported image files.

        Parameters
        ----------
        folder: str
            Absolute path to a directory containing images.

        Raises
        ------
        FileNotFoundError
            If the folder does not exist or cannot be read.

        ValueError
            If no supported images are found in the directory.
        """
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"Folder does not exist: {folder}")

        # Walk the directory non‑recursively and collect supported images.
        found: List[str] = []
        for name in os.listdir(folder):
            lower_name = name.lower()
            _, ext = os.path.splitext(lower_name)
            if ext in self.SUPPORTED_EXTENSIONS:
                abs_path = os.path.abspath(os.path.join(folder, name))
                found.append(abs_path)

        if not found:
            raise ValueError("Selected folder contains no supported image files.")

        # Sort the list for deterministic ordering when using sequential mode.
        found.sort()
        self.folder = folder
        self.images = found
        self.index = 0

    def next_image(self, random_mode: bool) -> str:
        """Return the next image path according to the current mode.

        If `random_mode` is True, a random image is selected. Otherwise the
        list is traversed sequentially and the index wraps around at the end.

        Parameters
        ----------
        random_mode: bool
            Whether to select the next image randomly.

        Returns
        -------
        str
            Absolute path to the next image.

        Raises
        ------
        RuntimeError
            If no images have been loaded.
        """
        if not self.images:
            raise RuntimeError("No images have been loaded.")

        if random_mode:
            return random.choice(self.images)

        # Sequential mode
        path = self.images[self.index]
        self.index = (self.index + 1) % len(self.images)
        return path


class MainWindow(QMainWindow):
    """Main application window providing the user interface.

    This class defines all UI elements, wires up signals and slots, manages
    application settings persistence, and controls the wallpaper timer.
    """

    def __init__(self, icon: QIcon, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Wallpaper Changer")
        self.setWindowIcon(icon)
        self.controller = WallpaperController()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.change_wallpaper)

        # Initialize settings
        self.settings = QSettings("OpenAI", "WallpaperChanger")
        # Setup UI
        self._setup_ui(icon)
        self._load_settings()

    def _setup_ui(self, icon: QIcon) -> None:
        """Create widgets, layouts and connect signals for the main window."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.browse_button = QPushButton("Browse…")
        self.browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(QLabel("Image folder:"))
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(self.browse_button)
        main_layout.addLayout(folder_layout)

        # Interval and mode controls
        controls_layout = QGridLayout()
        # Interval spin box (seconds)
        interval_label = QLabel("Interval (s):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 86400)
        self.interval_spin.setSingleStep(5)
        self.interval_spin.setValue(60)
        controls_layout.addWidget(interval_label, 0, 0)
        controls_layout.addWidget(self.interval_spin, 0, 1)
        # Mode combo box
        mode_label = QLabel("Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sequential", "Random"])
        controls_layout.addWidget(mode_label, 1, 0)
        controls_layout.addWidget(self.mode_combo, 1, 1)
        main_layout.addLayout(controls_layout)

        # Start/Stop buttons
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_slideshow)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_slideshow)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        main_layout.addLayout(buttons_layout)

        # Status and current file
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Stopped")
        self.current_label = QLabel("Current:")
        self.current_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_label)
        main_layout.addLayout(status_layout)

        # Log area
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(500)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log_edit)

        # Startup checkbox
        self.startup_checkbox = QCheckBox("Run on Windows startup")
        self.startup_checkbox.stateChanged.connect(self.on_startup_checkbox_changed)
        main_layout.addWidget(self.startup_checkbox)

        # System tray
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Wallpaper Changer")
        tray_menu = QMenu()
        self.action_show = QAction("Show", self)
        self.action_show.triggered.connect(self.show_normal)
        tray_menu.addAction(self.action_show)
        self.action_start = QAction("Start", self)
        self.action_start.triggered.connect(self.start_slideshow)
        tray_menu.addAction(self.action_start)
        self.action_stop = QAction("Stop", self)
        self.action_stop.triggered.connect(self.stop_slideshow)
        self.action_stop.setEnabled(False)
        tray_menu.addAction(self.action_stop)
        tray_menu.addSeparator()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        # Styling for a modern look
        self.setStyleSheet(
            """
            QWidget {
                font-size: 10pt;
            }
            QLineEdit {
                background: #f3f3f3;
                padding: 4px;
            }
            QPlainTextEdit {
                background: #fafafa;
            }
            QPushButton {
                padding: 6px 12px;
            }
            QLabel#status_label {
                font-weight: bold;
            }
            """
        )

    def _load_settings(self) -> None:
        """Restore user settings from persistent storage."""
        folder = self.settings.value("folder", type=str)
        if folder and os.path.isdir(folder):
            self.folder_edit.setText(folder)
            try:
                self.controller.load_folder(folder)
            except Exception:
                # ignore errors; user can reselect folder
                pass
        interval = self.settings.value("interval", 60, type=int)
        self.interval_spin.setValue(interval)
        mode = self.settings.value("mode", "Sequential")
        index = self.mode_combo.findText(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
        startup = self.settings.value("startup", False, type=bool)
        self.startup_checkbox.setChecked(bool(startup))
        # Update startup entry based on restored value
        if startup:
            self._apply_startup(True)

    def _save_settings(self) -> None:
        """Save current settings to persistent storage."""
        self.settings.setValue("folder", self.folder_edit.text())
        self.settings.setValue("interval", self.interval_spin.value())
        self.settings.setValue("mode", self.mode_combo.currentText())
        self.settings.setValue("startup", self.startup_checkbox.isChecked())

    @Slot()
    def select_folder(self) -> None:
        """Open a file dialog to select the folder containing wallpapers."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Image Folder",
            self.folder_edit.text() or os.path.expanduser("~"),
        )
        if directory:
            try:
                self.controller.load_folder(directory)
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))
                return
            self.folder_edit.setText(directory)
            self.log_message(f"Loaded folder: {directory}")
            # Save new folder
            self._save_settings()

    @Slot()
    def start_slideshow(self) -> None:
        """Start the wallpaper slideshow.

        Validates the selected folder and interval, sets up the timer, and
        updates the UI accordingly. If already running no action is taken.
        """
        if self.timer.isActive():
            return
        folder = self.folder_edit.text()
        if not folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        try:
            self.controller.load_folder(folder)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        interval_seconds = self.interval_spin.value()
        if interval_seconds <= 0:
            QMessageBox.warning(self, "Warning", "Interval must be greater than zero.")
            return
        self.timer.start(interval_seconds * 1000)
        self.start_button.setEnabled(False)
        self.action_start.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.action_stop.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.log_message("Slideshow started.")
        # Save settings now
        self._save_settings()
        # Immediately change wallpaper when starting
        self.change_wallpaper()

    @Slot()
    def stop_slideshow(self) -> None:
        """Stop the wallpaper slideshow and update the UI."""
        if not self.timer.isActive():
            return
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.action_start.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.action_stop.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.log_message("Slideshow stopped.")

    @Slot()
    def change_wallpaper(self) -> None:
        """Retrieve the next image and set it as the desktop wallpaper."""
        random_mode = self.mode_combo.currentText() == "Random"
        try:
            image_path = self.controller.next_image(random_mode)
        except Exception as exc:
            self.log_message(f"Error selecting next image: {exc}")
            self.stop_slideshow()
            return
        success = set_windows_wallpaper(image_path)
        if success:
            filename = os.path.basename(image_path)
            self.current_label.setText(f"Current: {filename}")
            self.log_message(f"Wallpaper changed to {filename}")
            # Show a balloon notification
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "Wallpaper Changed",
                    filename,
                    QSystemTrayIcon.Information,
                    3000,
                )
        else:
            self.log_message(f"Failed to change wallpaper to {image_path}")

    def log_message(self, message: str) -> None:
        """Append a message to the log area with a newline."""
        self.log_edit.appendPlainText(message)
        # Ensure the last line is visible
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    @Slot(int)
    def on_startup_checkbox_changed(self, state: int) -> None:
        """Toggle running the application on Windows startup based on checkbox."""
        enabled = state == Qt.Checked
        self._apply_startup(enabled)
        # Save setting
        self._save_settings()

    def _apply_startup(self, enable: bool) -> None:
        """Add or remove the application from Windows startup via registry.

        On Windows, the recommended way to run an application on user logon is
        to create a string value under the `Run` key in `HKEY_CURRENT_USER`.
        See GeeksforGeeks: "Adding a Python script to windows start‑up" for
        details【453262710304037†L27-L56】.
        """
        try:
            import winreg  # type: ignore

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    # Determine executable path
                    # When packaged with PyInstaller, sys.argv[0] will be the .exe
                    # Otherwise use the python interpreter with script path.
                    exe_path = os.path.realpath(sys.argv[0])
                    if exe_path.lower().endswith(".exe"):
                        value = exe_path
                    else:
                        # Use python executable and script path
                        value = f'"{sys.executable}" "{exe_path}"'
                    winreg.SetValueEx(key, "WallpaperChanger", 0, winreg.REG_SZ, value)
                    self.log_message("Added application to startup.")
                else:
                    # Remove the registry value
                    try:
                        winreg.DeleteValue(key, "WallpaperChanger")
                        self.log_message("Removed application from startup.")
                    except FileNotFoundError:
                        pass
        except ImportError:
            self.log_message("winreg module not available; cannot modify startup settings.")
        except PermissionError:
            self.log_message("Insufficient permissions to modify startup settings.")
        except Exception as exc:
            self.log_message(f"Error modifying startup settings: {exc}")

    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle clicks on the system tray icon."""
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
            QSystemTrayIcon.MiddleClick,
        ):
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()

    def show_normal(self) -> None:
        """Show and raise the main window."""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Override close event to minimize to tray instead of exiting."""
        # On close, hide window and show a message in tray
        if self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Wallpaper Changer",
                "Application minimized to tray. Double click the icon to restore.",
                QSystemTrayIcon.Information,
                3000,
            )
        else:
            # Save settings before exiting
            self._save_settings()
            super().closeEvent(event)


def load_app_icon() -> QIcon:
    """Load the application icon from the resources folder.

    Returns a null icon if the resource cannot be found. The icon should be
    placed in the resources directory alongside this module. If the file is
    missing the application will still function, but the system tray icon
    may appear blank.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "resources", "icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    # Fallback: dynamically generate a simple gradient icon using QPixmap
    try:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        from PySide6.QtGui import QPainter, QLinearGradient, QColor

        painter = QPainter(pixmap)
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor(100, 149, 237))  # cornflower blue
        gradient.setColorAt(1, QColor(123, 104, 238))  # medium slate blue
        painter.fillRect(0, 0, size, size, gradient)
        # Draw a white rectangle representing a window/wallpaper icon
        rect_margin = size // 5
        painter.setPen(Qt.white)
        painter.setBrush(QColor(255, 255, 255, 180))
        painter.drawRect(rect_margin, rect_margin, size - 2 * rect_margin, size - 2 * rect_margin)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        # On failure return a null icon
        return QIcon()


def main() -> None:
    """Entry point for the application."""
    # Ensure the program only runs on Windows.
    if sys.platform != "win32":
        QMessageBox.critical(None, "Unsupported Platform", "This application runs only on Windows.")
        return
    app = QApplication(sys.argv)
    # Prevent the app from quitting when the last window closes to keep tray alive
    app.setQuitOnLastWindowClosed(False)
    icon = load_app_icon()
    window = MainWindow(icon)
    window.show()
    # Execute the application
    try:
        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
