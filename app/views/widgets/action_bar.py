"""The three action buttons, built from config.ACTIONS."""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.config import ActionSpec


class ActionBar(QWidget):
    action_triggered = pyqtSignal(str)  # action id

    def __init__(self, actions: Iterable[ActionSpec], parent: QWidget | None = None):
        super().__init__(parent)
        self._specs = {spec.id: spec for spec in actions}
        self._buttons: dict[str, QPushButton] = {}
        self._inputs_complete = False
        self._busy_id: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch(1)  # right-aligned, primary action last (closest to the eye path end)

        for spec in self._specs.values():
            button = QPushButton(spec.label)
            button.setProperty("variant", spec.variant)
            button.setCursor(Qt.PointingHandCursor)
            button.setShortcut(QKeySequence(spec.shortcut))
            button.setToolTip(f"{spec.tooltip} ({spec.shortcut})")
            button.clicked.connect(lambda _=False, action_id=spec.id: self.action_triggered.emit(action_id))
            layout.addWidget(button)
            self._buttons[spec.id] = button

        self._refresh()

    def set_inputs_complete(self, complete: bool) -> None:
        self._inputs_complete = complete
        self._refresh()

    def set_busy(self, action_id: str | None) -> None:
        """Show `action_id` as running and lock every button; pass None to release."""
        self._busy_id = action_id
        self._refresh()

    def _refresh(self) -> None:
        for action_id, button in self._buttons.items():
            spec = self._specs[action_id]
            button.setText("Running…" if action_id == self._busy_id else spec.label)
            enabled = self._busy_id is None and (self._inputs_complete or not spec.requires_complete_input)
            button.setEnabled(enabled)
            if not enabled and self._busy_id is None:
                button.setToolTip(f"{spec.tooltip} — complete all fields first")
            else:
                button.setToolTip(f"{spec.tooltip} ({spec.shortcut})")
