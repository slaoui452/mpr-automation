"""Input file zone: drag & drop, Browse… and Ctrl+O.

Its inside (labels, buttons, the empty and loaded pages) is laid out in main_window.ui; this class adds
the behaviour. It only reports the chosen path: the file is validated by file_service.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QFrame, QLabel, QPushButton, QStackedWidget, QWidget

from app.ui.forms_loader import bind_widgets
from app.ui.theme.theme import set_style_prop


class FileDropZone(QFrame):
    file_chosen = pyqtSignal(str)
    cleared = pyqtSignal()

    # Widgets placed inside the zone in main_window.ui
    fileStateStack: QStackedWidget
    fileEmptyPage: QWidget
    fileLoadedPage: QWidget
    fileIcon: QLabel
    fileBrowseButton: QPushButton
    fileHintLabel: QLabel
    fileLoadedIcon: QLabel
    fileNameLabel: QLabel
    fileMetaLabel: QLabel
    fileChangeButton: QPushButton
    fileClearButton: QPushButton
    fileErrorLabel: QLabel

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._extensions: tuple[str, ...] = ()
        self._last_dir = str(Path.home())

    def setup(self) -> None:
        """Called by MainWindow once main_window.ui is loaded: the children only exist from then on."""
        bind_widgets(self, "main_window.ui (inside fileDropZone)")
        self.fileBrowseButton.clicked.connect(self.browse)
        self.fileChangeButton.clicked.connect(self.browse)
        self.fileClearButton.clicked.connect(self.cleared)
        self.clear()

    def set_extensions(self, extensions: Sequence[str]) -> None:
        self._extensions = tuple(ext.lower() for ext in extensions)
        self.fileHintLabel.setText(f"{' · '.join(self._extensions)}  —  Ctrl+O")

    def browse(self) -> None:
        if not self.isEnabled():
            return
        patterns = " ".join(f"*{ext}" for ext in self._extensions) or "*"
        path, _ = QFileDialog.getOpenFileName(self, "Select an Excel file", self._last_dir,
                                              f"Excel files ({patterns});;All files (*)")
        if path:
            self._choose(path)

    def show_file(self, name: str, details: str) -> None:
        self.fileNameLabel.setText(name)
        self.fileMetaLabel.setText(details)
        self.fileStateStack.setCurrentWidget(self.fileLoadedPage)
        self.fileErrorLabel.hide()
        set_style_prop(self, "state", "loaded")

    def show_error(self, message: str) -> None:
        self.fileStateStack.setCurrentWidget(self.fileEmptyPage)
        self.fileErrorLabel.setText(message)
        self.fileErrorLabel.show()
        set_style_prop(self, "state", "error")

    def clear(self) -> None:
        self.fileStateStack.setCurrentWidget(self.fileEmptyPage)
        self.fileErrorLabel.hide()
        set_style_prop(self, "state", "empty")

    def _choose(self, path: str) -> None:
        self._last_dir = str(Path(path).parent)
        self.file_chosen.emit(path)

    # --- drag & drop ------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            suffix = Path(urls[0].toLocalFile()).suffix.lower()
            set_style_prop(self, "dropState", "valid" if suffix in self._extensions else "invalid")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        set_style_prop(self, "dropState", "")
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        set_style_prop(self, "dropState", "")
        event.acceptProposedAction()
        self._choose(event.mimeData().urls()[0].toLocalFile())
