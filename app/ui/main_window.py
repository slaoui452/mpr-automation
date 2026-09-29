"""Main window: loads forms/main_window.ui, re-exposes user actions as signals, offers setters.

Passive view: no business logic. The presenter listens to the signals and calls the setters.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable, Sequence

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import QComboBox, QDateEdit, QLabel, QMainWindow, QPushButton, QShortcut, QSplitter, QWidget

from app.core.models import DateMessage, FileInfo, TileSpec
from app.ui.forms_loader import bind_widgets, load_form
from app.ui.theme.theme import apply_letter_spacing, set_style_prop
from app.ui.theme.tokens import COLORS
# Promoted widgets used by main_window.ui. Importing them here also lets PyInstaller find them.
from app.ui.widgets.action_tile import ActionTile
from app.ui.widgets.activity_panel import ActivityPanel
from app.ui.widgets.file_drop_zone import FileDropZone
from app.ui.widgets.logo_mark import LogoMark, make_logo_icon

ACTIVITY_PANEL_HEIGHT = 190


class MainWindow(QMainWindow):
    date_changed = pyqtSignal(object)     # datetime.date
    option_changed = pyqtSignal(object)   # str, or None while the placeholder is shown
    file_chosen = pyqtSignal(str)
    file_cleared = pyqtSignal()
    action_requested = pyqtSignal(str)    # actionId of the clicked tile
    cancel_requested = pyqtSignal()

    # Widgets from forms/main_window.ui: each name is the objectName set in Qt Designer.
    logoMark: LogoMark
    versionLabel: QLabel
    contentWidget: QWidget
    dateLabel: QLabel
    dateEdit: QDateEdit
    todayButton: QPushButton
    dateBadge: QLabel
    dateMessage: QLabel
    optionLabel: QLabel
    optionCombo: QComboBox
    fileLabel: QLabel
    fileDropZone: FileDropZone
    splitter: QSplitter
    activityPanel: ActivityPanel

    def __init__(self, log_file: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        load_form("main_window.ui", self)
        bind_widgets(self, "main_window.ui")
        self.fileDropZone.setup()
        self.activityPanel.setup(log_file)
        self._tiles = {tile.spec().action_id: tile for tile in self.findChildren(ActionTile)}
        self._busy = False
        self._close_guard: Callable[[], bool] | None = None
        self._splitter_sizes: list[int] = []

        self.setWindowIcon(make_logo_icon())
        self.contentWidget.setAttribute(Qt.WA_StyledBackground, True)
        self.dateEdit.setDate(QDate.currentDate())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([10_000, ACTIVITY_PANEL_HEIGHT])
        apply_letter_spacing(self)
        self._connect()

    def _connect(self) -> None:
        self.dateEdit.dateChanged.connect(lambda qdate: self.date_changed.emit(qdate.toPyDate()))
        self.todayButton.clicked.connect(lambda: self.dateEdit.setDate(QDate.currentDate()))
        self.optionCombo.currentIndexChanged.connect(self._on_option_index_changed)
        self.fileDropZone.file_chosen.connect(self.file_chosen)
        self.fileDropZone.cleared.connect(self.file_cleared)
        for tile in self._tiles.values():
            tile.triggered.connect(self.action_requested)
            tile.cancel_clicked.connect(self.cancel_requested)
        self.activityPanel.collapsed_changed.connect(self._on_activity_collapsed)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.fileDropZone.browse)
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self._on_escape)

    # --- read by the presenter ----------------------------------------------------
    def current_date(self) -> date:
        return self.dateEdit.date().toPyDate()

    def tile_specs(self) -> list[TileSpec]:
        return [tile.spec() for tile in self.findChildren(ActionTile)]

    # --- setters called by the presenter ----------------------------------------------
    def set_version(self, version: str) -> None:
        self.versionLabel.setText(f"v{version}")

    def set_option_values(self, values: Sequence[str]) -> None:
        combo = self.optionCombo
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(combo.placeholderText() or "Select…", None)   # index 0 = nothing chosen
        combo.setItemData(0, QColor(COLORS["muted"]), Qt.ForegroundRole)
        for value in values:
            combo.addItem(value, value)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        set_style_prop(combo, "placeholder", True)

    def set_file_extensions(self, extensions: Sequence[str]) -> None:
        self.fileDropZone.set_extensions(extensions)

    def set_date_message(self, message: DateMessage) -> None:
        self.dateBadge.setText(message.badge)
        self.dateMessage.setText(message.text)
        set_style_prop(self.dateBadge, "tone", message.tone.value)

    def show_file(self, info: FileInfo) -> None:
        self.fileDropZone.show_file(info.name, f"{info.size_label} · modified {info.modified:%d/%m/%Y %H:%M}")
        self.fileDropZone.setToolTip(str(info.path))

    def show_file_error(self, message: str) -> None:
        self.fileDropZone.show_error(message)
        self.fileDropZone.setToolTip("")

    def clear_file(self) -> None:
        self.fileDropZone.clear()
        self.fileDropZone.setToolTip("")

    def set_tile_ready(self, action_id: str) -> None:
        self._tiles[action_id].set_ready()

    def set_tile_blocked(self, action_id: str, missing: Sequence[str]) -> None:
        labels = {"date": self.dateLabel, "option": self.optionLabel, "file": self.fileLabel}
        names = [labels[name].text().lower() if name in labels else name for name in missing]
        self._tiles[action_id].set_blocked("Needs: " + ", ".join(names))

    def set_busy(self, running_action_id: str | None) -> None:
        """Locks the inputs and the other tiles while an action runs; None unlocks the inputs."""
        busy = running_action_id is not None
        for widget in (self.dateEdit, self.todayButton, self.optionCombo, self.fileDropZone):
            widget.setEnabled(not busy)
        if busy:
            for action_id, tile in self._tiles.items():
                if action_id == running_action_id:
                    tile.set_running()
                else:
                    tile.set_locked()
        self._busy = busy

    def set_tile_progress(self, action_id: str, percent: int | None, text: str) -> None:
        self._tiles[action_id].set_progress(percent, text)

    def set_tile_cancelling(self, action_id: str) -> None:
        self._tiles[action_id].set_cancelling()

    def set_status(self, text: str, busy: bool) -> None:
        self.activityPanel.set_status(text, busy)

    def append_activity(self, time_text: str, kind: str, text: str) -> None:
        self.activityPanel.append(time_text, kind, text)

    def set_close_guard(self, guard: Callable[[], bool]) -> None:
        """guard() returns False to keep the window open (e.g. while an action is stopping)."""
        self._close_guard = guard

    # --- internal ---------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._close_guard is not None and not self._close_guard():
            event.ignore()
            return
        super().closeEvent(event)

    def _on_option_index_changed(self, index: int) -> None:
        value = self.optionCombo.itemData(index) if index >= 0 else None
        set_style_prop(self.optionCombo, "placeholder", value is None)
        self.option_changed.emit(value)

    def _on_escape(self) -> None:
        if self._busy:
            self.cancel_requested.emit()

    def _on_activity_collapsed(self, collapsed: bool) -> None:
        panel = self.activityPanel
        if collapsed:
            self._splitter_sizes = self.splitter.sizes()
            panel.layout().activate()   # size of the header alone, now that the list is hidden
            header_height = panel.sizeHint().height()
            panel.setMaximumHeight(header_height)
            self.splitter.setSizes([sum(self._splitter_sizes) - header_height, header_height])
        else:
            panel.setMaximumHeight(16777215)
            if self._splitter_sizes:
                self.splitter.setSizes(self._splitter_sizes)
