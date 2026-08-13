"""Wallpaper-driven dynamic theming for Wally."""

from __future__ import annotations

import colorsys
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

ColorTuple = Tuple[int, int, int]


@dataclass(frozen=True)
class ThemePalette:
    """UI colors derived from (or defaulting without) a wallpaper."""

    bg_window: str
    bg_sidebar: str
    bg_card: str
    bg_input: str
    bg_hover: str
    bg_pressed: str
    bg_chip: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_secondary: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    accent_text: str
    primary_disabled: str
    selection: str
    scrollbar: str
    scrollbar_hover: str
    is_dark: bool


def _clamp(value: int, low: int = 0, high: int = 255) -> int:
    return max(low, min(high, int(value)))


def _hex(rgb: ColorTuple) -> str:
    return f"#{_clamp(rgb[0]):02X}{_clamp(rgb[1]):02X}{_clamp(rgb[2]):02X}"


def _rgb(color: QColor) -> ColorTuple:
    return (color.red(), color.green(), color.blue())


def _mix(a: ColorTuple, b: ColorTuple, t: float) -> ColorTuple:
    return (
        _clamp(a[0] + (b[0] - a[0]) * t),
        _clamp(a[1] + (b[1] - a[1]) * t),
        _clamp(a[2] + (b[2] - a[2]) * t),
    )


def _luminance(rgb: ColorTuple) -> float:
    r, g, b = [c / 255.0 for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _saturate(rgb: ColorTuple) -> float:
    r, g, b = [c / 255.0 for c in rgb]
    _h, s, _v = colorsys.rgb_to_hsv(r, g, b)
    return s


def _adjust(rgb: ColorTuple, sat_delta: float = 0.0, val_delta: float = 0.0) -> ColorTuple:
    r, g, b = [c / 255.0 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(0.0, min(1.0, s + sat_delta))
    v = max(0.0, min(1.0, v + val_delta))
    rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
    return (_clamp(rr * 255), _clamp(gg * 255), _clamp(bb * 255))


def _contrast_text(bg: ColorTuple) -> ColorTuple:
    return (255, 255, 255) if _luminance(bg) < 0.55 else (20, 20, 20)


DEFAULT_PALETTE = ThemePalette(
    bg_window="#F3F3F3",
    bg_sidebar="#EDEDED",
    bg_card="#FFFFFF",
    bg_input="#FAFAFA",
    bg_hover="#F5F5F5",
    bg_pressed="#EBEBEB",
    bg_chip="#F5F5F5",
    border="#E5E5E5",
    border_strong="#D1D1D1",
    text="#1A1A1A",
    text_muted="#6B6B6B",
    text_secondary="#2B2B2B",
    accent="#0078D4",
    accent_hover="#106EBE",
    accent_pressed="#005A9E",
    accent_soft="#E8F3FF",
    accent_text="#FFFFFF",
    primary_disabled="#B4D6FA",
    selection="#E8F3FF",
    scrollbar="#C8C8C8",
    scrollbar_hover="#A8A8A8",
    is_dark=False,
)

# Last applied palette — used by custom-painted widgets (charts).
CURRENT_PALETTE: ThemePalette = DEFAULT_PALETTE


def get_current_palette() -> ThemePalette:
    return CURRENT_PALETTE


def extract_colors_from_image(image_path: str) -> Optional[Tuple[ColorTuple, ColorTuple]]:
    """Return (average_rgb, accent_rgb) sampled from the wallpaper image."""
    if not image_path or not os.path.isfile(image_path):
        return None

    image = QImage(image_path)
    if image.isNull():
        return None

    # Small sample keeps CPU low while wallpaper changes.
    sample = image.scaled(48, 48)
    total = [0, 0, 0]
    count = 0
    best_accent: Optional[ColorTuple] = None
    best_score = -1.0

    for y in range(sample.height()):
        for x in range(sample.width()):
            color = QColor(sample.pixel(x, y))
            if color.alpha() < 20:
                continue
            rgb = _rgb(color)
            total[0] += rgb[0]
            total[1] += rgb[1]
            total[2] += rgb[2]
            count += 1

            sat = _saturate(rgb)
            lum = _luminance(rgb)
            # Prefer vivid mid-tone colors for accent (avoid near-black/white).
            if 0.12 < lum < 0.88 and sat > 0.12:
                score = sat * 1.4 + (1.0 - abs(lum - 0.45)) * 0.4
                if score > best_score:
                    best_score = score
                    best_accent = rgb

    if count == 0:
        return None

    average = (
        total[0] // count,
        total[1] // count,
        total[2] // count,
    )
    accent = best_accent or _adjust(average, sat_delta=0.25, val_delta=0.05)
    # Ensure accent is not too dull
    if _saturate(accent) < 0.18:
        accent = _adjust(accent, sat_delta=0.35, val_delta=0.05)
    return average, accent


def build_palette_from_wallpaper(image_path: Optional[str]) -> ThemePalette:
    """Build a readable UI palette influenced by the current wallpaper."""
    extracted = extract_colors_from_image(image_path) if image_path else None
    if extracted is None:
        return DEFAULT_PALETTE

    average, accent = extracted
    avg_lum = _luminance(average)
    is_dark = avg_lum < 0.42

    if is_dark:
        base = _mix(average, (18, 18, 22), 0.72)
        window = _mix(base, (12, 12, 16), 0.35)
        sidebar = _mix(base, (28, 28, 34), 0.25)
        card = _mix(base, (36, 36, 42), 0.15)
        inp = _mix(card, (48, 48, 56), 0.25)
        hover = _mix(card, (255, 255, 255), 0.08)
        pressed = _mix(card, (0, 0, 0), 0.12)
        chip = _mix(card, (255, 255, 255), 0.06)
        border = _mix(card, (255, 255, 255), 0.14)
        border_strong = _mix(card, (255, 255, 255), 0.22)
        text = (242, 242, 245)
        text_muted = (170, 172, 180)
        text_secondary = (220, 222, 228)
        scrollbar = _mix(card, (255, 255, 255), 0.25)
        scrollbar_hover = _mix(card, (255, 255, 255), 0.4)
        soft_mix = 0.22
    else:
        base = _mix(average, (245, 245, 247), 0.78)
        window = _mix(base, (243, 243, 243), 0.45)
        sidebar = _mix(base, (237, 237, 239), 0.35)
        card = _mix((255, 255, 255), average, 0.06)
        inp = _mix((250, 250, 250), average, 0.05)
        hover = _mix(card, average, 0.08)
        pressed = _mix(card, average, 0.14)
        chip = _mix((245, 245, 245), average, 0.08)
        border = _mix((229, 229, 229), average, 0.12)
        border_strong = _mix((209, 209, 209), average, 0.1)
        text = (26, 26, 26)
        text_muted = (107, 107, 107)
        text_secondary = (43, 43, 43)
        scrollbar = (200, 200, 200)
        scrollbar_hover = (168, 168, 168)
        soft_mix = 0.16

    # Accent tuned for buttons / active states
    accent_use = accent
    if is_dark and _luminance(accent_use) < 0.28:
        accent_use = _adjust(accent_use, val_delta=0.22)
    if not is_dark and _luminance(accent_use) > 0.78:
        accent_use = _adjust(accent_use, val_delta=-0.18, sat_delta=0.1)

    accent_hover = _adjust(accent_use, val_delta=-0.08 if not is_dark else 0.06)
    accent_pressed = _adjust(accent_use, val_delta=-0.14 if not is_dark else -0.05)
    accent_soft = _mix(card, accent_use, soft_mix)
    accent_text = _contrast_text(accent_use)
    primary_disabled = _mix(accent_use, (180, 180, 180) if not is_dark else (80, 80, 90), 0.45)

    return ThemePalette(
        bg_window=_hex(window),
        bg_sidebar=_hex(sidebar),
        bg_card=_hex(card),
        bg_input=_hex(inp),
        bg_hover=_hex(hover),
        bg_pressed=_hex(pressed),
        bg_chip=_hex(chip),
        border=_hex(border),
        border_strong=_hex(border_strong),
        text=_hex(text),
        text_muted=_hex(text_muted),
        text_secondary=_hex(text_secondary),
        accent=_hex(accent_use),
        accent_hover=_hex(accent_hover),
        accent_pressed=_hex(accent_pressed),
        accent_soft=_hex(accent_soft),
        accent_text=_hex(accent_text),
        primary_disabled=_hex(primary_disabled),
        selection=_hex(accent_soft),
        scrollbar=_hex(scrollbar),
        scrollbar_hover=_hex(scrollbar_hover),
        is_dark=is_dark,
    )


def palette_to_dict(palette: ThemePalette) -> Dict[str, str]:
    return {
        "bg_window": palette.bg_window,
        "bg_sidebar": palette.bg_sidebar,
        "bg_card": palette.bg_card,
        "bg_input": palette.bg_input,
        "bg_hover": palette.bg_hover,
        "bg_pressed": palette.bg_pressed,
        "bg_chip": palette.bg_chip,
        "border": palette.border,
        "border_strong": palette.border_strong,
        "text": palette.text,
        "text_muted": palette.text_muted,
        "text_secondary": palette.text_secondary,
        "accent": palette.accent,
        "accent_hover": palette.accent_hover,
        "accent_pressed": palette.accent_pressed,
        "accent_soft": palette.accent_soft,
        "accent_text": palette.accent_text,
        "primary_disabled": palette.primary_disabled,
        "selection": palette.selection,
        "scrollbar": palette.scrollbar,
        "scrollbar_hover": palette.scrollbar_hover,
    }


def apply_theme_to_app(image_path: Optional[str] = None) -> ThemePalette:
    """Extract theme from wallpaper (if any) and apply to the running QApplication."""
    global CURRENT_PALETTE
    from src.ui.styles import build_stylesheet

    palette = build_palette_from_wallpaper(image_path)
    CURRENT_PALETTE = palette
    app = QApplication.instance()
    if app is not None:
        # Clear then re-apply so widgets fully pick up new colors (including combos).
        sheet = build_stylesheet(palette)
        app.setStyleSheet("")
        app.setStyleSheet(sheet)
        # Force custom-painted charts to repaint with theme text colors.
        try:
            from src.ui.widgets.usage_charts import (
                DistributionChart,
                HorizontalBarChart,
                VerticalBarChart,
            )

            chart_types = (HorizontalBarChart, VerticalBarChart, DistributionChart)
        except Exception:
            chart_types = ()

        for widget in app.allWidgets():
            if widget is None:
                continue
            try:
                style = widget.style()
                if style is not None:
                    style.unpolish(widget)
                    style.polish(widget)
                widget.update()
                if chart_types and isinstance(widget, chart_types):
                    widget.update()
            except Exception:
                continue
    return palette
