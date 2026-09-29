"""File input: read-only path field, Browse button and drag & drop.

The picker only reports the chosen path; validation is done by the controller
(file_service) which then calls `set_file` or `set_error`.
"""
from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.views.style_utils import set_style_property
from app.views.widgets.card import Card


class FilePicker(Card):
    file_selected = pyqtSignal(str)

    def __init__(self, title: str, hint: str, placeholder: str, dialog_filter: str,
                 browse_shortcut: str = "", parent: QWidget | None = None):
        super().__init__(title, hint, parent)
        self._dialog_filter = dialog_filter
        self._last_dir = str(Path.home())
        self.setAcceptDrops(True)

        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText(placeholder)

        self._browse = QPushButton("Browse…")
        self._browse.setProperty("variant", "ghost")
        if browse_shortcut:
            self._browse.setShortcut(QKeySequence(browse_shortcut))
            self._browse.setToolTip(f"Choose a file ({browse_shortcut})")

        self._info = QLabel()
        self._info.setObjectName("FileInfo")
        self._info.hide()

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._path_edit, 1)
        row.addWidget(self._browse)
        self.body.addLayout(row)
        self.body.addWidget(self._info)

        self._browse.clicked.connect(self._open_dialog)

    # --- public API used by the view --------------------------------------
    def set_file(self, path: str, info: str) -> None:
        self._path_edit.setText(path)
        self._path_edit.setToolTip(path)
        set_style_property(self._path_edit, "state", "ok")
        self._show_info(f"✓  {info}", "success")

    def set_error(self, path: str, message: str) -> None:
        self._path_edit.setText(path)
        self._path_edit.setToolTip(path)
        set_style_property(self._path_edit, "state", "error")
        self._show_info(f"✕  {message}", "error")

    def _show_info(self, text: str, level: str) -> None:
        self._info.setText(text)
        set_style_property(self._info, "level", level)
        self._info.show()

    # --- user interactions ------------------------------------------------
    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select a file", self._last_dir, self._dialog_filter)
        if path:
            self._emit(path)

    def _emit(self, path: str) -> None:
        self._last_dir = str(Path(path).parent)
        self.file_selected.emit(path)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile() and self.isEnabled():
            event.acceptProposedAction()
            set_style_property(self, "dragActive", True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        set_style_property(self, "dragActive", False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        set_style_property(self, "dragActive", False)
        event.acceptProposedAction()
        self._emit(event.mimeData().urls()[0].toLocalFile())
