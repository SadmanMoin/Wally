"""Windows 11 inspired application styling with DPI-friendly sizing."""

WINDOWS11_STYLE = """
/* ── Base ─────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;
    font-size: 10pt;
}

QMainWindow, QWidget#centralRoot {
    background-color: #F3F3F3;
    color: #1A1A1A;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* ── Sidebar ──────────────────────────────────────────────────────── */
QFrame#sidebar {
    background-color: #EDEDED;
    border: none;
    border-right: 1px solid #E0E0E0;
}

QLabel#sidebarBrand {
    font-size: 13pt;
    font-weight: 600;
    color: #1A1A1A;
}

QLabel#sidebarTagline {
    font-size: 8.5pt;
    color: #6B6B6B;
}

QPushButton#navItem {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: #2B2B2B;
    font-size: 10pt;
    font-weight: 500;
}

QPushButton#navItem:hover {
    background-color: #E0E0E0;
}

QPushButton#navItem:checked {
    background-color: #FFFFFF;
    color: #0078D4;
    font-weight: 600;
    border: 1px solid #E5E5E5;
}

QPushButton#navItem:pressed {
    background-color: #D6D6D6;
}

/* ── Cards ────────────────────────────────────────────────────────── */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 12px;
}

QFrame#cardElevated {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 12px;
}

QFrame#statusDot {
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
    border: none;
}

QFrame#statusDot[status="running"] {
    background-color: #0F7B0F;
}

QFrame#statusDot[status="paused"] {
    background-color: #C19C00;
}

QFrame#statusDot[status="stopped"] {
    background-color: #A4262C;
}

/* ── Typography ───────────────────────────────────────────────────── */
QLabel#appTitle {
    font-size: 20pt;
    font-weight: 600;
    color: #1A1A1A;
    letter-spacing: -0.3px;
}

QLabel#appSubtitle {
    font-size: 10pt;
    color: #6B6B6B;
}

QLabel#pageTitle {
    font-size: 18pt;
    font-weight: 600;
    color: #1A1A1A;
    letter-spacing: -0.2px;
}

QLabel#pageSubtitle {
    font-size: 10pt;
    color: #6B6B6B;
}

QLabel#sectionTitle {
    font-size: 11pt;
    font-weight: 600;
    color: #1A1A1A;
}

QLabel#cardHint {
    font-size: 9pt;
    color: #6B6B6B;
}

QLabel#mutedText {
    color: #6B6B6B;
    font-size: 9.5pt;
}

QLabel#metaLabel {
    color: #6B6B6B;
    font-size: 9pt;
}

QLabel#metaValue {
    color: #1A1A1A;
    font-size: 9.5pt;
    font-weight: 500;
}

QLabel#filenameLabel {
    font-size: 11pt;
    font-weight: 600;
    color: #1A1A1A;
}

QLabel#emptyTitle {
    font-size: 12pt;
    font-weight: 600;
    color: #1A1A1A;
}

QLabel#emptyHint {
    font-size: 9.5pt;
    color: #6B6B6B;
}

/* ── Status badge ─────────────────────────────────────────────────── */
QLabel#statusBadge {
    padding: 5px 12px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 9pt;
}

QLabel#statusBadge[status="running"] {
    background-color: #DFF6DD;
    color: #0F7B0F;
}

QLabel#statusBadge[status="paused"] {
    background-color: #FFF4CE;
    color: #8A6D00;
}

QLabel#statusBadge[status="stopped"] {
    background-color: #FDE7E9;
    color: #A4262C;
}

/* ── Wallpaper preview ────────────────────────────────────────────── */
QLabel#previewImage {
    background-color: #F5F5F5;
    border: 1px solid #E5E5E5;
    border-radius: 10px;
}

QFrame#previewChrome {
    background-color: #F8F8F8;
    border: 1px solid #E5E5E5;
    border-radius: 10px;
}

/* ── Form controls ────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox, QListWidget, QPlainTextEdit {
    background-color: #FAFAFA;
    border: 1px solid #D1D1D1;
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
    color: #1A1A1A;
}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QPlainTextEdit:hover {
    border-color: #B0B0B0;
    background-color: #FFFFFF;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #0078D4;
    background-color: #FFFFFF;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 1.4em;
    border: none;
    background: transparent;
}

QComboBox::drop-down {
    border: none;
    width: 1.6em;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    selection-background-color: #E8F3FF;
    selection-color: #1A1A1A;
    outline: none;
    padding: 4px;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D1;
    border-radius: 8px;
    padding: 8px 16px;
    text-align: center;
    color: #1A1A1A;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #F5F5F5;
    border-color: #C7C7C7;
}

QPushButton:pressed {
    background-color: #EBEBEB;
}

QPushButton#primaryButton {
    background-color: #0078D4;
    border: 1px solid #0078D4;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #106EBE;
    border-color: #106EBE;
}

QPushButton#primaryButton:pressed {
    background-color: #005A9E;
}

QPushButton#dangerButton {
    color: #A4262C;
    border-color: #E8B4B8;
}

QPushButton#dangerButton:hover {
    background-color: #FDF3F4;
    border-color: #D69CA1;
}

QPushButton#dangerButton:pressed {
    background-color: #F8E4E6;
}

QPushButton#ghostButton {
    background-color: transparent;
    border: 1px solid transparent;
    color: #0078D4;
    font-weight: 600;
}

QPushButton#ghostButton:hover {
    background-color: #E8F3FF;
    border-color: #E8F3FF;
}

QPushButton#presetChip {
    background-color: #F5F5F5;
    border: 1px solid #E0E0E0;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 9pt;
    font-weight: 500;
    color: #2B2B2B;
}

QPushButton#presetChip:hover {
    background-color: #EBEBEB;
    border-color: #D0D0D0;
}

QPushButton#presetChip:checked {
    background-color: #E8F3FF;
    border-color: #0078D4;
    color: #0078D4;
    font-weight: 600;
}

QPushButton:disabled {
    color: #A0A0A0;
    background-color: #F0F0F0;
    border-color: #E0E0E0;
}

QPushButton#primaryButton:disabled {
    background-color: #B4D6FA;
    border-color: #B4D6FA;
    color: #FFFFFF;
}

/* ── Checkboxes ───────────────────────────────────────────────────── */
QCheckBox {
    spacing: 10px;
    color: #1A1A1A;
}

QCheckBox::indicator {
    width: 1.15em;
    height: 1.15em;
    border-radius: 4px;
    border: 1px solid #8A8886;
    background: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #0078D4;
}

QCheckBox::indicator:checked {
    background-color: #0078D4;
    border-color: #0078D4;
}

/* ── Lists ────────────────────────────────────────────────────────── */
QListWidget {
    outline: none;
    background-color: #FAFAFA;
}

QListWidget::item {
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 0;
    color: #1A1A1A;
}

QListWidget::item:hover {
    background-color: #F0F0F0;
}

QListWidget::item:selected {
    background-color: #E8F3FF;
    color: #1A1A1A;
}

/* ── Log / text ───────────────────────────────────────────────────── */
QPlainTextEdit {
    background-color: #FAFAFA;
    font-family: "Cascadia Mono", "Consolas", "Segoe UI", monospace;
    font-size: 9pt;
}

/* ── Scrollbars ───────────────────────────────────────────────────── */
QScrollBar:vertical {
    width: 10px;
    background: transparent;
    margin: 4px 2px 4px 0;
}

QScrollBar::handle:vertical {
    background: #C8C8C8;
    min-height: 28px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #A8A8A8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 10px;
    background: transparent;
    margin: 0 4px 2px 4px;
}

QScrollBar::handle:horizontal {
    background: #C8C8C8;
    min-width: 28px;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Menus / tooltips ─────────────────────────────────────────────── */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 28px 8px 14px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #E8F3FF;
}

QMenu::separator {
    height: 1px;
    background: #E5E5E5;
    margin: 4px 8px;
}

QToolTip {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #D1D1D1;
    border-radius: 6px;
    padding: 6px 10px;
}

/* ── Toast ────────────────────────────────────────────────────────── */
QFrame#toast {
    background-color: #1F1F1F;
    border: none;
    border-radius: 10px;
}

QLabel#toastMessage {
    color: #FFFFFF;
    font-size: 9.5pt;
    font-weight: 500;
}

QFrame#toast[level="success"] {
    background-color: #0F7B0F;
}

QFrame#toast[level="error"] {
    background-color: #A4262C;
}

QFrame#toast[level="info"] {
    background-color: #1F1F1F;
}

/* ── Settings rows ────────────────────────────────────────────────── */
QFrame#settingsRow {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid #F0F0F0;
}

QLabel#settingsTitle {
    font-size: 10pt;
    font-weight: 500;
    color: #1A1A1A;
}

QLabel#settingsDescription {
    font-size: 9pt;
    color: #6B6B6B;
}

QFrame#divider {
    background-color: #EFEFEF;
    border: none;
    max-height: 1px;
    min-height: 1px;
}
"""
