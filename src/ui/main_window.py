"""Main application window — professional Windows 11 style dashboard."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.wallpaper_controller import WallpaperController
from src.core.wallpaper_service import WallpaperService
from src.core.windows_wallpaper import set_windows_wallpaper
from src.services.logger import AppLogger
from src.services.settings_manager import SettingsManager
from src.services.startup_manager import StartupManager
from src.ui.layout_helpers import (
    LAYOUT_MARGIN,
    LAYOUT_SPACING,
    add_buttons_flow,
    apply_card_layout,
    configure_action_button,
    configure_expanding,
)
from src.ui.tray_icon import TrayIconController
from src.ui.usage_dashboard import UsageDashboard
from src.ui.widgets.log_panel import LogPanel
from src.ui.widgets.preview_panel import PreviewPanel
from src.ui.widgets.sidebar import Sidebar
from src.ui.widgets.status_card import StatusCard
from src.ui.widgets.toast import ToastHost
from src.usage_tracker.service import UsageTrackerService

# Interval presets: (label, seconds). None seconds = custom.
INTERVAL_PRESETS = [
    ("5 min", 300),
    ("15 min", 900),
    ("30 min", 1800),
    ("1 hour", 3600),
    ("6 hours", 21600),
    ("Custom", None),
]


class MainWindow(QMainWindow):
    """Primary UI for configuring and controlling wallpaper rotation."""

    def __init__(
        self,
        icon: QIcon,
        controller: WallpaperController,
        service: WallpaperService,
        settings: SettingsManager,
        logger: AppLogger,
        usage_service: Optional[UsageTrackerService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Wallpaper Changer")
        self.setWindowIcon(icon)
        self.setMinimumSize(900, 600)
        self.resize(1120, 740)

        self._icon = icon
        self._controller = controller
        self._service = service
        self._settings = settings
        self._logger = logger
        self._usage_service = usage_service
        self._logger.add_listener(self._on_log_message)
        self._tray = TrayIconController(icon, self)
        self._preset_buttons: Dict[int, QPushButton] = {}
        self._syncing_interval = False

        self._build_ui()
        self._connect_signals()
        self._load_settings()
        self._tray.show()

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._refresh_status_details)
        self._countdown_timer.start()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("centralRoot")
        self.setCentralWidget(root)

        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = Sidebar(
            [
                ("home", "Home"),
                ("wallpapers", "Wallpapers"),
                ("schedule", "Schedule"),
                ("usage", "Application Usage"),
                ("settings", "Settings"),
                ("about", "About"),
            ]
        )
        shell.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        shell.addWidget(self.stack, stretch=1)

        self._page_index = {
            "home": 0,
            "wallpapers": 1,
            "schedule": 2,
            "usage": 3,
            "settings": 4,
            "about": 5,
        }

        self.stack.addWidget(self._wrap_scroll(self._build_home_page()))
        self.stack.addWidget(self._wrap_scroll(self._build_wallpapers_page()))
        self.stack.addWidget(self._wrap_scroll(self._build_schedule_page()))
        self.stack.addWidget(self._wrap_scroll(self._build_usage_page()))
        self.stack.addWidget(self._wrap_scroll(self._build_settings_page()))
        self.stack.addWidget(self._wrap_scroll(self._build_about_page()))

        self._toast = ToastHost(root)

    def _wrap_scroll(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    def _page_header(self, title: str, subtitle: str) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        title_label.setWordWrap(True)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        header.addWidget(title_label)
        header.addWidget(subtitle_label)
        return header

    def _make_card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        apply_card_layout(layout)
        return card, layout

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN)
        layout.setSpacing(LAYOUT_SPACING)

        header_row = QHBoxLayout()
        header_col = self._page_header(
            "Home",
            "Automatically change your desktop wallpaper on schedule.",
        )
        header_row.addLayout(header_col, stretch=1)

        self.status_badge = QLabel("Inactive")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setProperty("status", "stopped")
        self.status_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.status_badge, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_row)

        self.status_card = StatusCard()
        layout.addWidget(self.status_card)

        self.preview_panel = PreviewPanel()
        configure_expanding(self.preview_panel, vertical_stretch=True)
        layout.addWidget(self.preview_panel, stretch=1)

        # Quick schedule summary on home
        quick, quick_layout = self._make_card()
        quick_title = QLabel("Quick Controls")
        quick_title.setObjectName("sectionTitle")
        quick_hint = QLabel("Start, pause, or stop automatic wallpaper rotation.")
        quick_hint.setObjectName("cardHint")
        quick_hint.setWordWrap(True)
        quick_layout.addWidget(quick_title)
        quick_layout.addWidget(quick_hint)

        self.start_button = QPushButton("Start Scheduler")
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.change_now_button = QPushButton("Change Now")
        add_buttons_flow(
            quick_layout,
            [
                self.start_button,
                self.pause_button,
                self.stop_button,
                self.change_now_button,
            ],
        )

        self.home_schedule_summary = QLabel("Scheduler is inactive.")
        self.home_schedule_summary.setObjectName("mutedText")
        self.home_schedule_summary.setWordWrap(True)
        quick_layout.addWidget(self.home_schedule_summary)
        layout.addWidget(quick)

        layout.addStretch(0)
        return page

    def _build_wallpapers_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN)
        layout.setSpacing(LAYOUT_SPACING)
        layout.addLayout(
            self._page_header(
                "Wallpapers",
                "Add image files or folders that supply wallpapers for your desktop.",
            )
        )

        card, card_layout = self._make_card()
        title = QLabel("Wallpaper Sources")
        title.setObjectName("sectionTitle")
        hint = QLabel(
            "Add image files and/or folders. Supported formats: "
            "JPG, PNG, BMP, WEBP, GIF."
        )
        hint.setObjectName("cardHint")
        hint.setWordWrap(True)

        self.source_list = QListWidget()
        # Keep legacy attribute name used by older references if any.
        self.folder_list = self.source_list
        configure_expanding(self.source_list, vertical_stretch=True)
        self.source_list.setMinimumHeight(200)
        self.source_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.source_list.setAlternatingRowColors(False)
        self.source_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.add_file_button = QPushButton("Add Image File")
        self.add_file_button.setObjectName("primaryButton")
        self.add_file_button.setToolTip("Choose one or more image files to use as wallpapers")
        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.setToolTip("Choose a folder; all supported images inside are used")
        self.remove_folder_button = QPushButton("Remove Selected")
        self.remove_folder_button.setObjectName("dangerButton")
        self.remove_folder_button.setToolTip("Remove the selected files or folders from the list")

        for button in (
            self.add_file_button,
            self.add_folder_button,
            self.remove_folder_button,
        ):
            configure_action_button(button)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(40)

        # Explicit horizontal row so buttons are always visible (not only FlowLayout).
        button_row = QHBoxLayout()
        button_row.setSpacing(LAYOUT_SPACING)
        button_row.addWidget(self.add_file_button)
        button_row.addWidget(self.add_folder_button)
        button_row.addWidget(self.remove_folder_button)
        button_row.addStretch(1)

        card_layout.addWidget(title)
        card_layout.addWidget(hint)
        card_layout.addLayout(button_row)
        card_layout.addWidget(self.source_list, stretch=1)

        self.image_count_label = QLabel("0 wallpapers loaded")
        self.image_count_label.setObjectName("mutedText")
        self.image_count_label.setWordWrap(True)
        card_layout.addWidget(self.image_count_label)

        self.folders_empty_hint = QLabel(
            "No wallpapers yet. Use the buttons above to add image files or a folder."
        )
        self.folders_empty_hint.setObjectName("emptyHint")
        self.folders_empty_hint.setWordWrap(True)
        self.folders_empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.folders_empty_hint)

        layout.addWidget(card, stretch=1)

        # Mode card (randomization lives with wallpaper source)
        mode_card, mode_layout = self._make_card()
        mode_title = QLabel("Rotation Mode")
        mode_title.setObjectName("sectionTitle")
        mode_hint = QLabel("Choose how the next wallpaper is selected.")
        mode_hint.setObjectName("cardHint")
        mode_hint.setWordWrap(True)

        mode_row = QHBoxLayout()
        mode_label = QLabel("Change mode")
        mode_label.setObjectName("metaLabel")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sequential", "Random"])
        configure_expanding(self.mode_combo)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_combo, stretch=1)

        mode_layout.addWidget(mode_title)
        mode_layout.addWidget(mode_hint)
        mode_layout.addLayout(mode_row)
        layout.addWidget(mode_card)

        return page

    def _build_schedule_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN)
        layout.setSpacing(LAYOUT_SPACING)
        layout.addLayout(
            self._page_header(
                "Schedule",
                "Control how often your wallpaper changes automatically.",
            )
        )

        # Enable / status
        status_card, status_layout = self._make_card()
        status_title = QLabel("Automatic Changing")
        status_title.setObjectName("sectionTitle")
        status_hint = QLabel(
            "When active, wallpapers rotate on the interval below. "
            "You can pause or stop at any time."
        )
        status_hint.setObjectName("cardHint")
        status_hint.setWordWrap(True)

        self.schedule_status_badge = QLabel("Inactive")
        self.schedule_status_badge.setObjectName("statusBadge")
        self.schedule_status_badge.setProperty("status", "stopped")
        self.schedule_status_badge.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )

        badge_row = QHBoxLayout()
        badge_row.addWidget(QLabel("Status"))
        badge_row.addWidget(self.schedule_status_badge)
        badge_row.addStretch(1)

        self.countdown_label = QLabel("Next change: —")
        self.countdown_label.setObjectName("metaValue")
        self.countdown_label.setWordWrap(True)

        status_layout.addWidget(status_title)
        status_layout.addWidget(status_hint)
        status_layout.addLayout(badge_row)
        status_layout.addWidget(self.countdown_label)

        self.schedule_start_button = QPushButton("Start Scheduler")
        self.schedule_start_button.setObjectName("primaryButton")
        self.schedule_pause_button = QPushButton("Pause")
        self.schedule_stop_button = QPushButton("Stop")
        add_buttons_flow(
            status_layout,
            [
                self.schedule_start_button,
                self.schedule_pause_button,
                self.schedule_stop_button,
            ],
        )
        layout.addWidget(status_card)

        # Interval
        interval_card, interval_layout = self._make_card()
        interval_title = QLabel("Time Interval")
        interval_title.setObjectName("sectionTitle")
        interval_hint = QLabel("Pick a preset or enter a custom interval in seconds.")
        interval_hint.setObjectName("cardHint")
        interval_hint.setWordWrap(True)
        interval_layout.addWidget(interval_title)
        interval_layout.addWidget(interval_hint)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        self._preset_group = QButtonGroup(self)
        self._preset_group.setExclusive(True)
        for label, seconds in INTERVAL_PRESETS:
            chip = QPushButton(label)
            chip.setObjectName("presetChip")
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            configure_action_button(chip)
            if seconds is None:
                self._preset_buttons[-1] = chip
                chip.clicked.connect(self._on_custom_preset_clicked)
            else:
                self._preset_buttons[seconds] = chip
                chip.clicked.connect(lambda checked=False, s=seconds: self._on_preset_clicked(s))
            self._preset_group.addButton(chip)
            presets_row.addWidget(chip)
        presets_row.addStretch(1)
        interval_layout.addLayout(presets_row)

        custom_row = QHBoxLayout()
        custom_label = QLabel("Custom interval")
        custom_label.setObjectName("metaLabel")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 86400)
        self.interval_spin.setSingleStep(5)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setToolTip("Interval between wallpaper changes (5–86400 seconds)")
        configure_expanding(self.interval_spin)
        custom_row.addWidget(custom_label)
        custom_row.addWidget(self.interval_spin, stretch=1)
        interval_layout.addLayout(custom_row)

        self.interval_human_label = QLabel("Every 1 minute")
        self.interval_human_label.setObjectName("mutedText")
        interval_layout.addWidget(self.interval_human_label)
        layout.addWidget(interval_card)

        # Empty / disabled guidance
        self.schedule_empty_card, empty_layout = self._make_card()
        empty_title = QLabel("Scheduler inactive")
        empty_title.setObjectName("emptyTitle")
        empty_hint = QLabel(
            "Add image files or folders, then start the scheduler to rotate "
            "images automatically."
        )
        empty_hint.setObjectName("emptyHint")
        empty_hint.setWordWrap(True)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_hint)
        go_folders = QPushButton("Go to Wallpapers")
        go_folders.setObjectName("primaryButton")
        configure_action_button(go_folders)
        go_folders.setCursor(Qt.CursorShape.PointingHandCursor)
        go_folders.clicked.connect(lambda: self._navigate("wallpapers"))
        empty_layout.addWidget(go_folders, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.schedule_empty_card)

        layout.addStretch(1)
        return page

    def _build_usage_page(self) -> QWidget:
        if self._usage_service is None:
            # Fallback empty page if service was not provided.
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(
                LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN
            )
            layout.addLayout(
                self._page_header(
                    "Application Usage",
                    "Usage tracking is unavailable in this session.",
                )
            )
            return page

        self.usage_dashboard = UsageDashboard(self._usage_service)
        return self.usage_dashboard

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN)
        layout.setSpacing(LAYOUT_SPACING)
        layout.addLayout(
            self._page_header(
                "Settings",
                "Configure general application behavior.",
            )
        )

        general, general_layout = self._make_card()
        general_title = QLabel("General")
        general_title.setObjectName("sectionTitle")
        general_layout.addWidget(general_title)

        self.startup_checkbox = QCheckBox("Start with Windows")
        self.startup_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        startup_desc = QLabel(
            "Launch Wallpaper Changer automatically when you sign in to Windows."
        )
        startup_desc.setObjectName("settingsDescription")
        startup_desc.setWordWrap(True)
        general_layout.addWidget(self.startup_checkbox)
        general_layout.addWidget(startup_desc)
        general_layout.addSpacing(8)

        tray_title = QLabel("System tray")
        tray_title.setObjectName("settingsTitle")
        tray_desc = QLabel(
            "Closing the window minimizes the app to the system tray. "
            "Wallpaper scheduling continues in the background. "
            "Use Exit from the tray menu to quit completely."
        )
        tray_desc.setObjectName("settingsDescription")
        tray_desc.setWordWrap(True)
        general_layout.addWidget(tray_title)
        general_layout.addWidget(tray_desc)
        layout.addWidget(general)

        # Application usage tracking settings
        usage_card, usage_layout = self._make_card()
        usage_title = QLabel("Application Usage")
        usage_title.setObjectName("sectionTitle")
        usage_layout.addWidget(usage_title)

        self.usage_tracking_checkbox = QCheckBox("Enable Application Usage Tracking")
        self.usage_tracking_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        usage_desc = QLabel(
            "Track how long each app is in the foreground. Data stays on this PC "
            "in a local SQLite database. No keystrokes or content are recorded."
        )
        usage_desc.setObjectName("settingsDescription")
        usage_desc.setWordWrap(True)
        usage_layout.addWidget(self.usage_tracking_checkbox)
        usage_layout.addWidget(usage_desc)
        usage_layout.addSpacing(8)

        idle_row = QHBoxLayout()
        idle_label = QLabel("Idle timeout (minutes)")
        idle_label.setObjectName("settingsTitle")
        self.idle_timeout_spin = QSpinBox()
        self.idle_timeout_spin.setRange(1, 120)
        self.idle_timeout_spin.setValue(5)
        self.idle_timeout_spin.setSuffix(" min")
        self.idle_timeout_spin.setToolTip(
            "Stop counting usage after this much keyboard/mouse inactivity."
        )
        configure_expanding(self.idle_timeout_spin)
        idle_row.addWidget(idle_label)
        idle_row.addWidget(self.idle_timeout_spin, stretch=1)
        usage_layout.addLayout(idle_row)
        idle_desc = QLabel(
            "If you leave the PC idle longer than this, time is not counted toward any app."
        )
        idle_desc.setObjectName("settingsDescription")
        idle_desc.setWordWrap(True)
        usage_layout.addWidget(idle_desc)

        open_usage = QPushButton("Open Application Usage")
        configure_action_button(open_usage)
        open_usage.setCursor(Qt.CursorShape.PointingHandCursor)
        open_usage.clicked.connect(lambda: self._navigate("usage"))
        usage_layout.addWidget(open_usage, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(usage_card)

        wallpaper_card, wallpaper_layout = self._make_card()
        wallpaper_title = QLabel("Wallpaper")
        wallpaper_title.setObjectName("sectionTitle")
        wallpaper_layout.addWidget(wallpaper_title)

        mode_desc = QLabel(
            "Rotation mode (Sequential or Random) is configured on the Wallpapers page. "
            "Wallpaper sources are the image files and folders you add there."
        )
        mode_desc.setObjectName("settingsDescription")
        mode_desc.setWordWrap(True)
        wallpaper_layout.addWidget(mode_desc)

        open_wallpapers = QPushButton("Open Wallpapers")
        configure_action_button(open_wallpapers)
        open_wallpapers.setCursor(Qt.CursorShape.PointingHandCursor)
        open_wallpapers.clicked.connect(lambda: self._navigate("wallpapers"))
        wallpaper_layout.addWidget(open_wallpapers, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(wallpaper_card)

        schedule_card, schedule_layout = self._make_card()
        schedule_title = QLabel("Schedule")
        schedule_title.setObjectName("sectionTitle")
        schedule_layout.addWidget(schedule_title)
        schedule_desc = QLabel(
            "Enable the scheduler, choose an interval, and use custom timing "
            "from the Schedule page."
        )
        schedule_desc.setObjectName("settingsDescription")
        schedule_desc.setWordWrap(True)
        schedule_layout.addWidget(schedule_desc)
        open_schedule = QPushButton("Open Schedule")
        configure_action_button(open_schedule)
        open_schedule.setCursor(Qt.CursorShape.PointingHandCursor)
        open_schedule.clicked.connect(lambda: self._navigate("schedule"))
        schedule_layout.addWidget(open_schedule, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(schedule_card)

        note = QLabel("Folders, interval, mode, and scheduler state are saved automatically.")
        note.setObjectName("mutedText")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(LAYOUT_MARGIN + 8, LAYOUT_MARGIN + 4, LAYOUT_MARGIN + 8, LAYOUT_MARGIN)
        layout.setSpacing(LAYOUT_SPACING)
        layout.addLayout(
            self._page_header(
                "About",
                "Wallpaper Changer — a lightweight Windows desktop utility.",
            )
        )

        about_card, about_layout = self._make_card()
        about_title = QLabel("Wallpaper Changer")
        about_title.setObjectName("sectionTitle")
        about_body = QLabel(
            "Automatically change your desktop wallpaper on a schedule. "
            "Select image files or folders, choose sequential or random rotation, "
            "and keep the app running quietly in the system tray."
        )
        about_body.setObjectName("settingsDescription")
        about_body.setWordWrap(True)
        about_layout.addWidget(about_title)
        about_layout.addWidget(about_body)
        about_layout.addSpacing(8)

        features = QLabel(
            "• Image files and multi-folder wallpaper sources\n"
            "• Sequential and random modes\n"
            "• Configurable change interval\n"
            "• Local application usage tracking\n"
            "• System tray background operation\n"
            "• Optional start with Windows"
        )
        features.setObjectName("metaValue")
        features.setWordWrap(True)
        about_layout.addWidget(features)
        layout.addWidget(about_card)

        self.log_panel = LogPanel()
        configure_expanding(self.log_panel, vertical_stretch=True)
        layout.addWidget(self.log_panel, stretch=1)
        return page

    # ── Signals ─────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.sidebar.page_changed.connect(self._on_page_changed)

        self.add_file_button.clicked.connect(self._add_files)
        self.add_folder_button.clicked.connect(self._add_folder)
        self.remove_folder_button.clicked.connect(self._remove_selected_source)

        self.start_button.clicked.connect(self._start_or_resume_scheduler)
        self.pause_button.clicked.connect(self._pause_scheduler)
        self.stop_button.clicked.connect(self._stop_scheduler)
        self.change_now_button.clicked.connect(self._change_wallpaper_now)

        self.schedule_start_button.clicked.connect(self._start_or_resume_scheduler)
        self.schedule_pause_button.clicked.connect(self._pause_scheduler)
        self.schedule_stop_button.clicked.connect(self._stop_scheduler)

        self.preview_panel.change_now_button.clicked.connect(self._change_wallpaper_now)

        self.interval_spin.valueChanged.connect(self._on_interval_spin_changed)
        self.mode_combo.currentTextChanged.connect(self._on_schedule_changed)
        self.startup_checkbox.stateChanged.connect(self._on_startup_changed)
        self.usage_tracking_checkbox.stateChanged.connect(self._on_usage_tracking_changed)
        self.idle_timeout_spin.valueChanged.connect(self._on_idle_timeout_changed)

        self.preview_panel.preview_changed.connect(self._on_preview_navigate)
        self.preview_panel.apply_requested.connect(self._apply_preview_wallpaper)

        self._service.wallpaper_changed.connect(self._on_wallpaper_changed)
        self._service.status_changed.connect(self._on_status_changed)
        self._service.error_occurred.connect(self._show_error)

        self._tray.action_open.triggered.connect(self.show_window)
        self._tray.action_change_now.triggered.connect(self._change_wallpaper_now)
        self._tray.action_pause.triggered.connect(self._pause_scheduler)
        self._tray.action_resume.triggered.connect(self._resume_scheduler)
        self._tray.action_exit.triggered.connect(self._exit_application)
        self._tray.connect_activated(self._on_tray_activated)

    @Slot(str)
    def _on_page_changed(self, page_id: str) -> None:
        self._navigate(page_id)

    def _navigate(self, page_id: str) -> None:
        index = self._page_index.get(page_id)
        if index is None:
            return
        self.stack.setCurrentIndex(index)
        self.sidebar.set_current(page_id)

    # ── Settings ────────────────────────────────────────────────────

    def _load_settings(self) -> None:
        folders = self._settings.get_folders()
        files = self._settings.get_files()
        self.source_list.clear()
        for folder in folders:
            self._add_source_item("folder", folder)
        for path in files:
            self._add_source_item("file", path)

        interval = self._settings.get_interval()
        self._syncing_interval = True
        self.interval_spin.setValue(interval)
        self._syncing_interval = False
        self._sync_preset_selection(interval)
        self._update_interval_human_label(interval)

        mode_index = self.mode_combo.findText(self._settings.get_mode())
        if mode_index >= 0:
            self.mode_combo.setCurrentIndex(mode_index)

        startup_enabled = self._settings.get_startup_enabled()
        self.startup_checkbox.blockSignals(True)
        self.startup_checkbox.setChecked(startup_enabled)
        self.startup_checkbox.blockSignals(False)

        usage_enabled = self._settings.get_usage_tracking_enabled()
        self.usage_tracking_checkbox.blockSignals(True)
        self.usage_tracking_checkbox.setChecked(usage_enabled)
        self.usage_tracking_checkbox.blockSignals(False)

        idle_minutes = self._settings.get_idle_timeout_minutes()
        self.idle_timeout_spin.blockSignals(True)
        self.idle_timeout_spin.setValue(idle_minutes)
        self.idle_timeout_spin.blockSignals(False)
        if self._usage_service is not None:
            self._usage_service.set_idle_timeout_minutes(idle_minutes)

        if folders or files:
            self._reload_wallpapers(show_errors=False)
        else:
            self._update_folders_empty_state()
            self.preview_panel.set_empty_folders()

        self._apply_schedule_to_service()
        self._update_control_states(self._service.status)

        if self._settings.get_scheduler_active() and self._controller.image_count > 0:
            restored_status = self._settings.get_scheduler_status()
            try:
                if restored_status == WallpaperService.STATUS_RUNNING:
                    self._service.start()
                elif restored_status == WallpaperService.STATUS_PAUSED:
                    self._service.start()
                    self._service.pause()
            except Exception as exc:
                self._logger.warning("Could not restore scheduler state: %s", exc)

        self._logger.info("Application started. Log file: %s", self._logger.log_path)
        self._refresh_status_details()

    def _save_settings(self) -> None:
        folders, files = self._collect_sources()
        self._settings.set_folders(folders)
        self._settings.set_files(files)
        self._settings.set_interval(self.interval_spin.value())
        self._settings.set_mode(self.mode_combo.currentText())
        self._settings.set_startup_enabled(self.startup_checkbox.isChecked())
        self._settings.set_usage_tracking_enabled(self.usage_tracking_checkbox.isChecked())
        self._settings.set_idle_timeout_minutes(self.idle_timeout_spin.value())
        self._settings.set_scheduler_status(self._service.status)
        self._settings.sync()

    def _add_source_item(self, source_type: str, path: str) -> None:
        """Add a folder or file entry to the source list."""
        label = f"Folder  ·  {path}" if source_type == "folder" else f"Image  ·  {path}"
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, source_type)
        item.setData(Qt.ItemDataRole.UserRole + 1, path)
        item.setToolTip(path)
        self.source_list.addItem(item)

    def _collect_sources(self) -> tuple[List[str], List[str]]:
        folders: List[str] = []
        files: List[str] = []
        for index in range(self.source_list.count()):
            item = self.source_list.item(index)
            source_type = item.data(Qt.ItemDataRole.UserRole)
            path = item.data(Qt.ItemDataRole.UserRole + 1)
            if not path:
                # Fallback for any plain-text legacy items
                path = item.text()
                source_type = "folder" if os.path.isdir(path) else "file"
            if source_type == "file":
                files.append(path)
            else:
                folders.append(path)
        return folders, files

    def _collect_folders(self) -> List[str]:
        folders, _files = self._collect_sources()
        return folders

    def _collect_files(self) -> List[str]:
        _folders, files = self._collect_sources()
        return files

    def _source_paths(self) -> set[str]:
        folders, files = self._collect_sources()
        return set(folders) | set(files)

    def _reload_wallpapers(self, show_errors: bool = True) -> bool:
        folders, files = self._collect_sources()
        self._update_folders_empty_state()
        if not folders and not files:
            self._controller.folders = []
            self._controller.files = []
            self._controller.images = []
            self.image_count_label.setText("0 wallpapers loaded")
            self.preview_panel.set_empty_folders()
            self._refresh_status_details()
            return False

        try:
            self._controller.load_sources(folders, files)
        except (FileNotFoundError, ValueError) as exc:
            if show_errors:
                self._show_error(str(exc))
            self.image_count_label.setText("0 wallpapers loaded")
            self.preview_panel.set_no_images()
            self._refresh_status_details()
            return False

        count = self._controller.image_count
        folder_count = len(self._controller.folders)
        file_count = len(self._controller.files)
        parts: List[str] = []
        if folder_count:
            parts.append(f"{folder_count} folder{'s' if folder_count != 1 else ''}")
        if file_count:
            parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
        source_text = " and ".join(parts) if parts else "sources"
        plural = "s" if count != 1 else ""
        self.image_count_label.setText(
            f"{count} wallpaper{plural} loaded from {source_text}"
        )
        preview_path = self._controller.preview_at(0)
        self.preview_panel.set_preview(preview_path)
        self._save_settings()
        self._refresh_status_details()
        return True

    def _update_folders_empty_state(self) -> None:
        has_sources = self.source_list.count() > 0
        self.folders_empty_hint.setVisible(not has_sources)
        self.source_list.setVisible(True)

    # ── Interval presets ────────────────────────────────────────────

    def _on_preset_clicked(self, seconds: int) -> None:
        self._syncing_interval = True
        self.interval_spin.setValue(seconds)
        self._syncing_interval = False
        self._sync_preset_selection(seconds)
        self._update_interval_human_label(seconds)
        self._on_schedule_changed()
        self._show_toast("Schedule updated", "success")

    def _on_custom_preset_clicked(self) -> None:
        chip = self._preset_buttons.get(-1)
        if chip:
            chip.setChecked(True)
        self.interval_spin.setFocus()
        self.interval_spin.selectAll()

    @Slot(int)
    def _on_interval_spin_changed(self, value: int) -> None:
        if self._syncing_interval:
            return
        self._sync_preset_selection(value)
        self._update_interval_human_label(value)
        self._on_schedule_changed()

    def _sync_preset_selection(self, seconds: int) -> None:
        matched = False
        for value, button in self._preset_buttons.items():
            if value == -1:
                continue
            is_match = value == seconds
            button.setChecked(is_match)
            if is_match:
                matched = True
        custom = self._preset_buttons.get(-1)
        if custom is not None:
            custom.setChecked(not matched)

    def _update_interval_human_label(self, seconds: int) -> None:
        self.interval_human_label.setText(f"Every {self._format_duration(seconds)}")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        if seconds < 3600:
            minutes = seconds // 60
            rem = seconds % 60
            if rem == 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes}m {rem}s"
        hours = seconds // 3600
        rem_m = (seconds % 3600) // 60
        if rem_m == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours}h {rem_m}m"

    # ── Source / scheduler actions ──────────────────────────────────

    @Slot()
    def _add_files(self) -> None:
        file_filter = (
            "Image files (*.jpg *.jpeg *.png *.bmp *.webp *.gif);;"
            "All files (*.*)"
        )
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Wallpaper Image(s)",
            os.path.expanduser("~"),
            file_filter,
        )
        if not paths:
            return

        existing = self._source_paths()
        added = 0
        skipped = 0
        for path in paths:
            abs_path = os.path.abspath(path)
            _, extension = os.path.splitext(abs_path.lower())
            if extension not in WallpaperController.SUPPORTED_EXTENSIONS:
                skipped += 1
                continue
            if abs_path in existing:
                skipped += 1
                continue
            self._add_source_item("file", abs_path)
            existing.add(abs_path)
            added += 1

        if added == 0:
            if skipped:
                self._show_toast("No new image files were added", "info")
            return

        if self._reload_wallpapers():
            self._logger.info("Added %s wallpaper file(s).", added)
            self._show_toast(
                f"Added {added} image file{'s' if added != 1 else ''}",
                "success",
            )

    @Slot()
    def _add_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Wallpaper Folder",
            os.path.expanduser("~"),
        )
        if not directory:
            return

        if directory in self._source_paths():
            self._show_toast("That folder is already in the list", "info")
            return

        self._add_source_item("folder", directory)
        if self._reload_wallpapers():
            self._logger.info("Added wallpaper folder: %s", directory)
            self._show_toast("Wallpaper folder selected", "success")

    @Slot()
    def _remove_selected_source(self) -> None:
        selected_items = self.source_list.selectedItems()
        if not selected_items:
            self._show_toast("Select a file or folder to remove", "info")
            return

        for item in selected_items:
            row = self.source_list.row(item)
            self.source_list.takeItem(row)

        self._reload_wallpapers(show_errors=False)
        self._logger.info("Removed selected wallpaper source(s).")
        self._show_toast("Removed from list", "success")

        if self._controller.image_count == 0 and self._service.status != WallpaperService.STATUS_STOPPED:
            self._service.stop()
            self._save_settings()

    # Keep old name as alias for any external callers.
    @Slot()
    def _remove_selected_folder(self) -> None:
        self._remove_selected_source()

    @Slot()
    def _start_or_resume_scheduler(self) -> None:
        if self._service.status == WallpaperService.STATUS_PAUSED:
            self._resume_scheduler()
        else:
            self._start_scheduler()

    @Slot()
    def _start_scheduler(self) -> None:
        if not self._reload_wallpapers():
            self._show_error(
                "Add at least one image file or folder containing supported images."
            )
            return

        self._apply_schedule_to_service()
        try:
            self._service.start()
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._save_settings()
        self._show_toast("Scheduler started", "success")

    @Slot()
    def _pause_scheduler(self) -> None:
        self._service.pause()
        self._save_settings()
        self._show_toast("Scheduler paused", "info")

    @Slot()
    def _resume_scheduler(self) -> None:
        if self._controller.image_count == 0:
            self._show_error("Add image files or folders before resuming the scheduler.")
            return
        self._apply_schedule_to_service()
        self._service.resume()
        self._save_settings()
        self._show_toast("Scheduler resumed", "success")

    @Slot()
    def _stop_scheduler(self) -> None:
        self._service.stop()
        self._save_settings()
        self._show_toast("Scheduler stopped", "info")

    @Slot()
    def _change_wallpaper_now(self) -> None:
        if self._controller.image_count == 0:
            if not self._reload_wallpapers():
                self._show_error(
                    "Add at least one image file or folder containing supported images."
                )
                return

        if self._service.status == WallpaperService.STATUS_STOPPED:
            self._apply_schedule_to_service()

        self._service.apply_next_wallpaper()

    def _apply_schedule_to_service(self) -> None:
        self._service.configure(
            self.interval_spin.value(),
            self.mode_combo.currentText() == "Random",
        )

    @Slot()
    def _on_schedule_changed(self) -> None:
        self._apply_schedule_to_service()
        self._save_settings()
        self._refresh_status_details()

    @Slot(str)
    def _on_preview_navigate(self, direction: str) -> None:
        delta = -1 if direction == "prev" else 1
        preview_path = self._controller.step_preview(delta)
        self.preview_panel.set_preview(preview_path)

    @Slot(str)
    def _apply_preview_wallpaper(self, image_path: str) -> None:
        success, error_message = set_windows_wallpaper(image_path)
        if not success:
            self._show_error(error_message or "Could not apply wallpaper.")
            return

        self._controller.sync_preview_to_path(image_path)
        self._logger.info("Applied preview wallpaper: %s", image_path)
        # Mirror service path: update UI the same way as automatic changes.
        self._on_wallpaper_changed(image_path)

    @Slot(str)
    def _on_wallpaper_changed(self, image_path: str) -> None:
        filename = os.path.basename(image_path)
        self.preview_panel.set_preview(image_path)
        self._tray.notify("Wallpaper Changed", filename)
        self._refresh_status_details()
        self._show_toast("Wallpaper changed successfully", "success")

    @Slot(str)
    def _on_status_changed(self, status: str) -> None:
        self._update_control_states(status)
        self._save_settings()
        self._refresh_status_details()

    def _update_control_states(self, status: str) -> None:
        running = status == WallpaperService.STATUS_RUNNING
        paused = status == WallpaperService.STATUS_PAUSED
        stopped = status == WallpaperService.STATUS_STOPPED

        labels = {
            WallpaperService.STATUS_RUNNING: "Active",
            WallpaperService.STATUS_PAUSED: "Paused",
            WallpaperService.STATUS_STOPPED: "Inactive",
        }
        text = labels.get(status, "Inactive")
        for badge in (self.status_badge, self.schedule_status_badge):
            badge.setText(text)
            badge.setProperty("status", status)
            badge.style().unpolish(badge)
            badge.style().polish(badge)

        self.status_card.set_status(status)

        for start_btn in (self.start_button, self.schedule_start_button):
            start_btn.setEnabled(stopped or paused)
            start_btn.setText("Resume" if paused else "Start Scheduler")

        for pause_btn in (self.pause_button, self.schedule_pause_button):
            pause_btn.setEnabled(running)
        for stop_btn in (self.stop_button, self.schedule_stop_button):
            stop_btn.setEnabled(running or paused)

        self._tray.update_scheduler_actions(status)
        self.schedule_empty_card.setVisible(stopped and self._controller.image_count == 0)

    def _refresh_status_details(self) -> None:
        current_path = self._service.current_image or self.preview_panel.current_path
        if current_path:
            current_name = os.path.basename(current_path)
        else:
            current_name = "None"

        status = self._service.status
        remaining = self._service.remaining_seconds()
        if status == WallpaperService.STATUS_RUNNING and remaining is not None:
            next_change = f"in {self._format_duration(remaining)}"
            countdown = f"Next change: in {self._format_duration(remaining)}"
        elif status == WallpaperService.STATUS_PAUSED:
            next_change = "Paused"
            countdown = "Next change: paused"
        else:
            next_change = "—"
            countdown = "Next change: — (scheduler inactive)"

        folders, files = self._collect_sources()
        if not folders and not files:
            source = "No source selected"
        elif len(folders) + len(files) == 1:
            source = (folders + files)[0]
        else:
            parts: List[str] = []
            if folders:
                parts.append(f"{len(folders)} folder{'s' if len(folders) != 1 else ''}")
            if files:
                parts.append(f"{len(files)} file{'s' if len(files) != 1 else ''}")
            source = ", ".join(parts)

        scheduler_labels = {
            WallpaperService.STATUS_RUNNING: "Running",
            WallpaperService.STATUS_PAUSED: "Paused",
            WallpaperService.STATUS_STOPPED: "Stopped",
        }
        scheduler = scheduler_labels.get(status, "Stopped")
        interval = self.interval_spin.value()
        mode = self.mode_combo.currentText()

        self.status_card.set_details(current_name, next_change, source, scheduler)
        self.countdown_label.setText(countdown)
        self.home_schedule_summary.setText(
            f"{scheduler} · every {self._format_duration(interval)} · {mode} mode"
            + (f" · {self._controller.image_count} wallpapers" if self._controller.image_count else "")
        )
        self.schedule_empty_card.setVisible(
            status == WallpaperService.STATUS_STOPPED and self._controller.image_count == 0
        )

    @Slot(int)
    def _on_startup_changed(self, state: int) -> None:
        enabled = state == int(Qt.CheckState.Checked)
        success, error_message = StartupManager.set_enabled(enabled)
        if not success:
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(not enabled)
            self.startup_checkbox.blockSignals(False)
            self._show_error(error_message or "Could not update startup settings.")
            return

        self._settings.set_startup_enabled(enabled)
        self._save_settings()
        self._logger.info("Startup %s.", "enabled" if enabled else "disabled")
        self._show_toast(
            "Start with Windows enabled" if enabled else "Start with Windows disabled",
            "success",
        )

    @Slot(int)
    def _on_usage_tracking_changed(self, state: int) -> None:
        enabled = state == int(Qt.CheckState.Checked)
        self._settings.set_usage_tracking_enabled(enabled)
        if self._usage_service is not None:
            if enabled:
                self._usage_service.set_idle_timeout_minutes(self.idle_timeout_spin.value())
                self._usage_service.start()
                self._show_toast("Application usage tracking enabled", "success")
            else:
                self._usage_service.stop()
                self._show_toast("Application usage tracking disabled", "info")
        self._save_settings()
        self._logger.info("Usage tracking %s.", "enabled" if enabled else "disabled")

    @Slot(int)
    def _on_idle_timeout_changed(self, minutes: int) -> None:
        self._settings.set_idle_timeout_minutes(minutes)
        if self._usage_service is not None:
            self._usage_service.set_idle_timeout_minutes(minutes)
        self._save_settings()
        self._show_toast(f"Idle timeout set to {minutes} min", "success")

    def _on_log_message(self, level: str, message: str) -> None:
        self.log_panel.append(level, message)

    def _show_toast(self, message: str, level: str = "info") -> None:
        self._toast.show_message(message, level=level)

    @Slot(str)
    def _show_error(self, message: str) -> None:
        self._logger.error(message)
        self._show_toast(message, "error")
        QMessageBox.warning(self, "Wallpaper Changer", message)

    @Slot()
    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    @Slot()
    def _exit_application(self) -> None:
        self._save_settings()
        if self._usage_service is not None:
            self._usage_service.stop()
        self._logger.remove_listener(self._on_log_message)
        self._countdown_timer.stop()
        self._tray.tray_icon.hide()
        QApplication.instance().quit()

    @Slot(object)
    def _on_tray_activated(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible():
                self.hide()
            else:
                self.show_window()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "_toast") and self._toast.isVisible():
            self._toast._reposition()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._tray.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self._tray.notify(
                "Wallpaper Changer",
                "The app is still running in the system tray.",
            )
            return

        self._save_settings()
        super().closeEvent(event)
