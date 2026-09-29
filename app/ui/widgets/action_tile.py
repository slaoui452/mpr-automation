"""Action tile: a large clickable card that runs one action. Its inside comes from forms/action_tile.ui.

In Qt Designer, a tile is a QFrame promoted to ActionTile in main_window.ui, with these dynamic
properties (Property Editor):
    actionId     name of the ActionService method to run, e.g. action_1
    title        shown in capitals on the tile and used in the activity panel
    description  one short sentence under the title
    needs        inputs required before the tile unlocks: date, option, file (comma separated)
    shortcut     keyboard shortcut, e.g. Ctrl+1
"""
from __future__ import annotations

import re

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QFrame, QLabel, QProgressBar, QPushButton, QShortcut, QWidget

from app.core.models import TileSpec
from app.ui.forms_loader import bind_widgets, load_form
from app.ui.theme.theme import set_style_prop


class ActionTile(QFrame):
    triggered = pyqtSignal(str)   # actionId
    cancel_clicked = pyqtSignal()

    # Widgets from forms/action_tile.ui
    tileTitle: QLabel
    tileDescription: QLabel
    tileNeeds: QLabel
    tileProgress: QProgressBar
    tileProgressText: QLabel
    tileProgressPercent: QLabel
    tileCancelButton: QPushButton
    tileShortcut: QLabel

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._action_id = ""
        self._title = ""
        self._needs = ""
        self._shortcut_text = ""
        self._shortcut: QShortcut | None = None
        load_form("action_tile.ui", self)
        bind_widgets(self, "action_tile.ui")
        self.setFocusPolicy(Qt.TabFocus)   # keyboard focus only: no red frame after a mouse click
        self.setAttribute(Qt.WA_Hover, True)
        self.tileCancelButton.clicked.connect(self.cancel_clicked)
        self.set_ready()

    # --- properties set in Qt Designer ----------------------------------------------
    def _get_action_id(self) -> str:
        return self._action_id

    def _set_action_id(self, value: str) -> None:
        self._action_id = value.strip()

    actionId = pyqtProperty(str, _get_action_id, _set_action_id)

    def _get_title(self) -> str:
        return self._title

    def _set_title(self, value: str) -> None:
        self._title = value.strip()
        self.tileTitle.setText(self._title.upper())

    title = pyqtProperty(str, _get_title, _set_title)

    def _get_description(self) -> str:
        return self.tileDescription.text()

    def _set_description(self, value: str) -> None:
        self.tileDescription.setText(value)

    description = pyqtProperty(str, _get_description, _set_description)

    def _get_needs(self) -> str:
        return self._needs

    def _set_needs(self, value: str) -> None:
        self._needs = value

    needs = pyqtProperty(str, _get_needs, _set_needs)

    def _get_shortcut(self) -> str:
        return self._shortcut_text

    def _set_shortcut(self, value: str) -> None:
        self._shortcut_text = value.strip()
        self.tileShortcut.setText(self._shortcut_text)
        self.tileShortcut.setVisible(bool(self._shortcut_text))
        if self._shortcut is None:
            self._shortcut = QShortcut(self)
            self._shortcut.setContext(Qt.WindowShortcut)
            self._shortcut.activated.connect(self._activate)
        self._shortcut.setKey(QKeySequence(self._shortcut_text))

    shortcut = pyqtProperty(str, _get_shortcut, _set_shortcut)

    def spec(self) -> TileSpec:
        needs = tuple(name.lower() for name in re.split(r"[,;\s]+", self._needs) if name)
        return TileSpec(self.objectName(), self._action_id, self._title or self._action_id,
                        needs, self._shortcut_text)

    # --- states, driven by the presenter through MainWindow ---------------------------
    def set_ready(self) -> None:
        self._set_state("ready", enabled=True)
        self.setCursor(Qt.PointingHandCursor)

    def set_blocked(self, reason: str) -> None:
        """Missing inputs: greyed, with the reason, e.g. 'Needs: input file'."""
        self._set_state("blocked", enabled=False)
        self.tileNeeds.setText(reason)
        self.tileNeeds.show()

    def set_locked(self) -> None:
        """Another action is running."""
        self._set_state("locked", enabled=False)

    def set_running(self) -> None:
        self._set_state("running", enabled=True, running=True)
        self.tileProgress.setRange(0, 0)   # moving bar until the first progress report
        self.tileProgressText.setText("Starting…")
        self.tileProgressPercent.clear()
        self.tileCancelButton.setEnabled(True)

    def set_progress(self, percent: int | None, text: str) -> None:
        if percent is None:
            self.tileProgress.setRange(0, 0)
            self.tileProgressPercent.clear()
        else:
            self.tileProgress.setRange(0, 100)
            self.tileProgress.setValue(percent)
            self.tileProgressPercent.setText(f"{percent}%")
        if text:
            self.tileProgressText.setText(text)

    def set_cancelling(self) -> None:
        self.tileProgressText.setText("Cancelling…")
        self.tileCancelButton.setEnabled(False)

    def _set_state(self, state: str, enabled: bool, running: bool = False) -> None:
        self.setEnabled(enabled)
        self.unsetCursor()
        self.tileNeeds.hide()
        self.tileDescription.setVisible(not running)   # the progress takes its place while running
        for widget in (self.tileProgress, self.tileProgressText, self.tileProgressPercent, self.tileCancelButton):
            widget.setVisible(running)
        set_style_prop(self, "state", state)

    # --- interaction ----------------------------------------------------------------
    def _activate(self) -> None:
        if self.isEnabled() and self.property("state") == "ready":
            self.triggered.emit(self._action_id)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if event.button() == Qt.LeftButton:
            event.accept()   # so that the release comes back to the tile
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self._activate()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._activate()
        else:
            super().keyPressEvent(event)
