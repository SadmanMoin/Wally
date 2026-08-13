"""Wally application styling — supports wallpaper-driven dynamic themes."""

from __future__ import annotations

from src.ui.theme import DEFAULT_PALETTE, ThemePalette, palette_to_dict

STYLE_TEMPLATE = """
/* ── Base ─────────────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;
    font-size: 10pt;
    color: {text};
}}

QMainWindow, QWidget#centralRoot {{
    background-color: {bg_window};
    color: {text};
}}

QLabel {{
    color: {text};
    background: transparent;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ── Sidebar ──────────────────────────────────────────────────────── */
QFrame#sidebar {{
    background-color: {bg_sidebar};
    border: none;
    border-right: 1px solid {border};
}}

QLabel#sidebarBrand {{
    font-size: 13pt;
    font-weight: 600;
    color: {text};
}}

QLabel#sidebarTagline {{
    font-size: 8.5pt;
    color: {text_muted};
}}

QPushButton#navItem {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: {text_secondary};
    font-size: 10pt;
    font-weight: 500;
}}

QPushButton#navItem:hover {{
    background-color: {bg_hover};
}}

QPushButton#navItem:checked {{
    background-color: {bg_card};
    color: {accent};
    font-weight: 600;
    border: 1px solid {border};
}}

QPushButton#navItem:pressed {{
    background-color: {bg_pressed};
}}

/* ── Cards ────────────────────────────────────────────────────────── */
QFrame#card {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
}}

QFrame#cardElevated {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
}}

QFrame#statusDot {{
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
    border: none;
}}

QFrame#statusDot[status="running"] {{
    background-color: #0F7B0F;
}}

QFrame#statusDot[status="paused"] {{
    background-color: #C19C00;
}}

QFrame#statusDot[status="stopped"] {{
    background-color: #A4262C;
}}

/* ── Typography ───────────────────────────────────────────────────── */
QLabel#appTitle {{
    font-size: 20pt;
    font-weight: 600;
    color: {text};
    letter-spacing: -0.3px;
}}

QLabel#appSubtitle {{
    font-size: 10pt;
    color: {text_muted};
}}

QLabel#pageTitle {{
    font-size: 18pt;
    font-weight: 600;
    color: {text};
    letter-spacing: -0.2px;
}}

QLabel#pageSubtitle {{
    font-size: 10pt;
    color: {text_muted};
}}

QLabel#sectionTitle {{
    font-size: 11pt;
    font-weight: 600;
    color: {text};
}}

QLabel#cardHint {{
    font-size: 9pt;
    color: {text_muted};
}}

QLabel#mutedText {{
    color: {text_muted};
    font-size: 9.5pt;
}}

QLabel#metaLabel {{
    color: {text_muted};
    font-size: 9pt;
}}

QLabel#metaValue {{
    color: {text};
    font-size: 9.5pt;
    font-weight: 500;
}}

QLabel#filenameLabel {{
    font-size: 11pt;
    font-weight: 600;
    color: {text};
}}

QLabel#emptyTitle {{
    font-size: 12pt;
    font-weight: 600;
    color: {text};
}}

QLabel#emptyHint {{
    font-size: 9.5pt;
    color: {text_muted};
}}

/* ── Status badge ─────────────────────────────────────────────────── */
QLabel#statusBadge {{
    padding: 5px 12px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 9pt;
}}

QLabel#statusBadge[status="running"] {{
    background-color: #DFF6DD;
    color: #0F7B0F;
}}

QLabel#statusBadge[status="paused"] {{
    background-color: #FFF4CE;
    color: #8A6D00;
}}

QLabel#statusBadge[status="stopped"] {{
    background-color: #FDE7E9;
    color: #A4262C;
}}

/* ── Wallpaper preview ────────────────────────────────────────────── */
QLabel#previewImage {{
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 10px;
}}

QFrame#previewChrome {{
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 10px;
}}

/* ── Form controls ────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox, QListWidget, QPlainTextEdit, QDateEdit, QTableWidget {{
    background-color: {bg_input};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {accent};
    selection-color: {accent_text};
    color: {text};
}}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QPlainTextEdit:hover, QDateEdit:hover {{
    border-color: {border_strong};
    background-color: {bg_card};
    color: {text};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QDateEdit:focus {{
    border: 1px solid {accent};
    background-color: {bg_card};
    color: {text};
}}

QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled, QDateEdit:disabled {{
    color: {text_muted};
    background-color: {bg_hover};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 1.4em;
    border: none;
    background: transparent;
}}

QComboBox {{
    color: {text};
    background-color: {bg_input};
}}

QComboBox:on {{
    color: {text};
    background-color: {bg_card};
}}

QComboBox::drop-down {{
    border: none;
    width: 1.6em;
    background: transparent;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 8px;
    selection-background-color: {selection};
    selection-color: {text};
    color: {text};
    outline: none;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    color: {text};
    background-color: {bg_card};
    min-height: 28px;
    padding: 6px 10px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {selection};
    color: {text};
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {bg_hover};
    color: {text};
}}

QDateEdit {{
    color: {text};
    background-color: {bg_input};
}}

QCalendarWidget {{
    background-color: {bg_card};
    color: {text};
}}

QCalendarWidget QWidget {{
    background-color: {bg_card};
    color: {text};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {bg_card};
    color: {text};
    selection-background-color: {accent};
    selection-color: {accent_text};
}}

QCalendarWidget QToolButton {{
    color: {text};
    background-color: {bg_card};
}}

QCalendarWidget QMenu {{
    background-color: {bg_card};
    color: {text};
}}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {bg_card};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 8px 16px;
    text-align: center;
    color: {text};
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {bg_hover};
    border-color: {border_strong};
}}

QPushButton:pressed {{
    background-color: {bg_pressed};
}}

QPushButton#primaryButton {{
    background-color: {accent};
    border: 1px solid {accent};
    color: {accent_text};
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background-color: {accent_hover};
    border-color: {accent_hover};
}}

QPushButton#primaryButton:pressed {{
    background-color: {accent_pressed};
}}

QPushButton#dangerButton {{
    color: #A4262C;
    border-color: #E8B4B8;
}}

QPushButton#dangerButton:hover {{
    background-color: #FDF3F4;
    border-color: #D69CA1;
}}

QPushButton#dangerButton:pressed {{
    background-color: #F8E4E6;
}}

QPushButton#ghostButton {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {accent};
    font-weight: 600;
}}

QPushButton#ghostButton:hover {{
    background-color: {accent_soft};
    border-color: {accent_soft};
}}

QPushButton#presetChip {{
    background-color: {bg_chip};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 9pt;
    font-weight: 500;
    color: {text_secondary};
}}

QPushButton#presetChip:hover {{
    background-color: {bg_hover};
    border-color: {border_strong};
}}

QPushButton#presetChip:checked {{
    background-color: {accent_soft};
    border-color: {accent};
    color: {accent};
    font-weight: 600;
}}

QPushButton:disabled {{
    color: {text_muted};
    background-color: {bg_hover};
    border-color: {border};
}}

QPushButton#primaryButton:disabled {{
    background-color: {primary_disabled};
    border-color: {primary_disabled};
    color: {accent_text};
}}

/* ── Checkboxes ───────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 10px;
    color: {text};
}}

QCheckBox::indicator {{
    width: 1.15em;
    height: 1.15em;
    border-radius: 4px;
    border: 1px solid {border_strong};
    background: {bg_card};
}}

QCheckBox::indicator:hover {{
    border-color: {accent};
}}

QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Lists / tables ───────────────────────────────────────────────── */
QTableWidget {{
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 8px;
    gridline-color: transparent;
    outline: none;
    color: {text};
}}

QTableWidget::item {{
    padding: 8px 10px;
}}

QTableWidget::item:selected {{
    background-color: {selection};
    color: {text};
}}

QHeaderView::section {{
    background-color: {bg_chip};
    color: {text_muted};
    border: none;
    border-bottom: 1px solid {border};
    padding: 8px 10px;
    font-weight: 600;
}}

QDateEdit {{
    background-color: {bg_input};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 6px 10px;
    color: {text};
}}

QDateEdit:focus {{
    border: 1px solid {accent};
    background-color: {bg_card};
}}

QListWidget {{
    outline: none;
    background-color: {bg_input};
}}

QListWidget::item {{
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 0;
    color: {text};
}}

QListWidget::item:hover {{
    background-color: {bg_hover};
}}

QListWidget::item:selected {{
    background-color: {selection};
    color: {text};
}}

/* ── Log / text ───────────────────────────────────────────────────── */
QPlainTextEdit {{
    background-color: {bg_input};
    font-family: "Cascadia Mono", "Consolas", "Segoe UI", monospace;
    font-size: 9pt;
    color: {text};
}}

/* ── Scrollbars ───────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 10px;
    background: transparent;
    margin: 4px 2px 4px 0;
}}

QScrollBar::handle:vertical {{
    background: {scrollbar};
    min-height: 28px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {scrollbar_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    height: 10px;
    background: transparent;
    margin: 0 4px 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background: {scrollbar};
    min-width: 28px;
    border-radius: 5px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Menus / tooltips ─────────────────────────────────────────────── */
QMenu {{
    background-color: {bg_card};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
    color: {text};
}}

QMenu::item {{
    padding: 8px 28px 8px 14px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background-color: {selection};
}}

QMenu::separator {{
    height: 1px;
    background: {border};
    margin: 4px 8px;
}}

QToolTip {{
    background-color: {bg_card};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: 6px;
    padding: 6px 10px;
}}

/* ── Toast ────────────────────────────────────────────────────────── */
QFrame#toast {{
    background-color: #1F1F1F;
    border: none;
    border-radius: 10px;
}}

QLabel#toastMessage {{
    color: #FFFFFF;
    font-size: 9.5pt;
    font-weight: 500;
}}

QFrame#toast[level="success"] {{
    background-color: #0F7B0F;
}}

QFrame#toast[level="error"] {{
    background-color: #A4262C;
}}

QFrame#toast[level="info"] {{
    background-color: #1F1F1F;
}}

/* ── Settings rows ────────────────────────────────────────────────── */
QFrame#settingsRow {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {border};
}}

QLabel#settingsTitle {{
    font-size: 10pt;
    font-weight: 500;
    color: {text};
}}

QLabel#settingsDescription {{
    font-size: 9pt;
    color: {text_muted};
}}

QFrame#divider {{
    background-color: {border};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}
"""


def build_stylesheet(palette: ThemePalette | None = None) -> str:
    """Render the stylesheet for the given (or default) palette."""
    palette = palette or DEFAULT_PALETTE
    return STYLE_TEMPLATE.format(**palette_to_dict(palette))


# Default static theme used at startup before a wallpaper is applied.
WINDOWS11_STYLE = build_stylesheet(DEFAULT_PALETTE)
