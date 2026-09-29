"""Société Générale inspired palette and stylesheet loader.

styles.qss uses `$token` placeholders (string.Template) resolved from PALETTE,
so a colour is changed in one place only.
"""
from __future__ import annotations

from pathlib import Path
from string import Template

RED = "#E9041E"         # SG red (logo, primary action)
RED_HOVER = "#C80319"
RED_PRESSED = "#A30214"
RED_TINT = "#FDECEE"
BLACK = "#000000"       # SG black (logo, header)
BLACK_HOVER = "#2B2B2B"
WHITE = "#FFFFFF"
TEXT = "#1A1A1A"
MUTED = "#6B6B6B"
SURFACE = "#F4F4F4"     # window background behind the cards
BORDER = "#DADADA"
BORDER_STRONG = "#B5B5B5"
DISABLED_BG = "#E6E6E6"
DISABLED_TEXT = "#9E9E9E"
SUCCESS = "#1B7F3B"

PALETTE = {
    "red": RED,
    "red_hover": RED_HOVER,
    "red_pressed": RED_PRESSED,
    "red_tint": RED_TINT,
    "black": BLACK,
    "black_hover": BLACK_HOVER,
    "white": WHITE,
    "text": TEXT,
    "muted": MUTED,
    "surface": SURFACE,
    "border": BORDER,
    "border_strong": BORDER_STRONG,
    "disabled_bg": DISABLED_BG,
    "disabled_text": DISABLED_TEXT,
    "success": SUCCESS,
}

FONT_FAMILY = "Segoe UI"
FONT_SIZE_PT = 10

_STYLESHEET_PATH = Path(__file__).with_name("styles.qss")
ASSETS_DIR = Path(__file__).with_name("assets")


def load_stylesheet() -> str:
    tokens = {**PALETTE, "assets": ASSETS_DIR.as_posix()}  # QSS urls need forward slashes
    return Template(_STYLESHEET_PATH.read_text(encoding="utf-8")).substitute(tokens)
