"""Helpers for driving QSS from dynamic properties."""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget


def set_style_property(widget: QWidget, name: str, value) -> None:
    """Set a dynamic property and re-apply the stylesheet so `[name="value"]` selectors update."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
