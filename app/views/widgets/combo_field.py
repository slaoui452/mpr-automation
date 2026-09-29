"""Combo box with a non-selectable placeholder item."""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtWidgets import QComboBox, QWidget
from PyQt5.QtCore import pyqtSignal

from app.views.style_utils import set_style_property
from app.views.widgets.card import Card


class ComboField(Card):
    value_changed = pyqtSignal(object)  # str, or None when the placeholder is shown

    def __init__(self, title: str, hint: str, placeholder: str, values: Iterable[str],
                 parent: QWidget | None = None):
        super().__init__(title, hint, parent)

        self._combo = QComboBox()
        self._combo.addItem(placeholder)
        self._combo.model().item(0).setEnabled(False)  # placeholder cannot be re-selected
        self._combo.addItems(list(values))
        self._combo.setMinimumWidth(260)
        self._combo.setToolTip(f"Choose a {title.lower()}")
        self.body.addWidget(self._combo)

        self._combo.currentIndexChanged.connect(self._on_index_changed)
        self._on_index_changed(self._combo.currentIndex())

    def value(self) -> str | None:
        return self._combo.currentText() if self._combo.currentIndex() > 0 else None

    def _on_index_changed(self, index: int) -> None:
        set_style_property(self._combo, "placeholder", index <= 0)
        self.value_changed.emit(self.value())
