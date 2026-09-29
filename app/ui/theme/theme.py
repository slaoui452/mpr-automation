"""Applies the SG theme: Fusion style, font, palette, and styles.qss with its colour tokens."""
from __future__ import annotations

import logging
from string import Template

from PyQt5.QtGui import QColor, QFont, QImageReader, QPalette
from PyQt5.QtWidgets import QApplication, QLabel, QWidget

from app.core.paths import resource_path
from app.ui.theme.tokens import COLORS, FONT_FAMILY, FONT_SIZE_PT, LETTER_SPACING

logger = logging.getLogger(__name__)

THEME_DIR = ("app", "ui", "theme")


def icon_path(name: str) -> str:
    return str(resource_path(*THEME_DIR, "icons", name))


def build_stylesheet() -> str:
    source = resource_path(*THEME_DIR, "styles.qss").read_text(encoding="utf-8")
    tokens = {**COLORS, "icons": resource_path(*THEME_DIR, "icons").as_posix()}
    try:
        return Template(source).substitute(tokens)
    except KeyError as exc:
        raise KeyError(f"styles.qss uses ${exc.args[0]}, which tokens.py doesn't define.") from None
    except ValueError as exc:
        raise ValueError(f"styles.qss: {exc}. Write a literal dollar sign as $$.") from None


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")  # same rendering on every Windows version
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE_PT))
    app.setPalette(_palette())
    app.setStyleSheet(build_stylesheet())
    if b"svg" not in [bytes(fmt) for fmt in QImageReader.supportedImageFormats()]:
        logger.warning("This Qt installation can't read SVG files, so the icons won't show.")


def _palette() -> QPalette:
    """Colours for what styles.qss doesn't cover (text selection, links, tooltips)."""
    palette = QPalette()
    for role, name in ((QPalette.Window, "canvas"), (QPalette.Base, "surface"), (QPalette.Text, "text"),
                       (QPalette.WindowText, "text"), (QPalette.ButtonText, "text"),
                       (QPalette.Highlight, "red"), (QPalette.HighlightedText, "white"),
                       (QPalette.Link, "red"), (QPalette.ToolTipBase, "black"), (QPalette.ToolTipText, "white")):
        palette.setColor(role, QColor(COLORS[name]))
    return palette


def set_style_prop(widget: QWidget, name: str, value: object) -> None:
    """Changes a dynamic property used by styles.qss, then refreshes the widget and its children."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    for w in (widget, *widget.findChildren(QWidget)):
        w.style().unpolish(w)
        w.style().polish(w)
    apply_letter_spacing(widget)
    widget.update()


def apply_letter_spacing(root: QWidget) -> None:
    """Letter spacing for the uppercase labels, by role (see LETTER_SPACING in tokens.py)."""
    for label in (root, *root.findChildren(QLabel)):
        spacing = LETTER_SPACING.get(str(label.property("role")))
        if spacing and isinstance(label, QLabel):
            font = label.font()
            font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
            label.setFont(font)
