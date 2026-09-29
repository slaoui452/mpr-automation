"""Activity & log panel: every run and every log line (INFO and above), newest at the bottom."""
from __future__ import annotations

import html
from pathlib import Path

from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import QFrame, QLabel, QPlainTextEdit, QPushButton, QToolButton, QWidget

from app.core.models import Activity
from app.ui.forms_loader import bind_widgets
from app.ui.theme.theme import icon_path, set_style_prop
from app.ui.theme.tokens import COLORS, MONO_FAMILY

MAX_LINES = 5000

_LOOK = {  # activity kind: (symbol, symbol colour, text colour)
    Activity.START.value: ("▶", COLORS["text"], COLORS["text"]),
    Activity.SUCCESS.value: ("✓", COLORS["success"], COLORS["text"]),
    Activity.WARNING.value: ("!", COLORS["warning"], COLORS["warning"]),
    Activity.FAILURE.value: ("✕", COLORS["error"], COLORS["error"]),
    Activity.CANCEL.value: ("■", COLORS["muted"], COLORS["text"]),
    Activity.INFO.value: ("·", COLORS["muted"], COLORS["muted"]),
}


class ActivityPanel(QFrame):
    collapsed_changed = pyqtSignal(bool)

    # Widgets placed inside the panel in main_window.ui
    activityStatusDot: QFrame
    activityStatusLabel: QLabel
    activityOpenLogButton: QPushButton
    activityClearButton: QPushButton
    activityToggleButton: QToolButton
    activityLog: QPlainTextEdit

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._log_file: Path | None = None
        self._collapsed = False

    def setup(self, log_file: Path | None) -> None:
        """Called by MainWindow once main_window.ui is loaded: the children only exist from then on."""
        bind_widgets(self, "main_window.ui (inside activityPanel)")
        self._log_file = log_file
        self.activityLog.setMaximumBlockCount(MAX_LINES)
        self.activityOpenLogButton.setEnabled(log_file is not None)
        self.activityOpenLogButton.clicked.connect(self.open_log_file)
        self.activityClearButton.clicked.connect(self.activityLog.clear)
        self.activityToggleButton.clicked.connect(lambda: self.set_collapsed(not self._collapsed))
        self._update_toggle()

    def append(self, time_text: str, kind: str, text: str) -> None:
        symbol, symbol_color, text_color = _LOOK.get(kind, _LOOK[Activity.INFO.value])
        body = html.escape(text).replace("\n", "<br>")
        self.activityLog.appendHtml(
            f'<span style="color:{COLORS["muted"]}; font-family:{MONO_FAMILY}">{time_text}</span>'
            f'&nbsp;&nbsp;<span style="color:{symbol_color}">{symbol}</span>'
            f'&nbsp;&nbsp;<span style="color:{text_color}">{body}</span>')
        if kind == Activity.FAILURE.value and self._collapsed:
            self.set_collapsed(False)

    def set_status(self, text: str, busy: bool) -> None:
        self.activityStatusLabel.setText(text)
        set_style_prop(self.activityStatusDot, "busy", busy)

    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.activityLog.setVisible(not collapsed)
        self._update_toggle()
        self.collapsed_changed.emit(collapsed)
        if not collapsed:
            scroll_bar = self.activityLog.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def open_log_file(self) -> None:
        if self._log_file is not None and self._log_file.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._log_file)))

    def _update_toggle(self) -> None:
        icon, tip = (("chevron_up.svg", "Show the activity list") if self._collapsed
                     else ("chevron_down.svg", "Hide the activity list"))
        self.activityToggleButton.setIcon(QIcon(icon_path(icon)))
        self.activityToggleButton.setToolTip(tip)
