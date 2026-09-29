"""Main window: composes the widgets, re-exposes their signals and offers setters.

No business logic here. The controller listens to the signals and calls the setters.
"""
from __future__ import annotations

from datetime import date

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox, QStatusBar,
                             QVBoxLayout, QWidget)

from app import config
from app.models import DateMessage, FileInfo, StatusLevel
from app.views.style_utils import set_style_property
from app.views.widgets.action_bar import ActionBar
from app.views.widgets.combo_field import ComboField
from app.views.widgets.date_field import DateField
from app.views.widgets.file_picker import FilePicker
from app.views.widgets.header_bar import AccentLine, HeaderBar, make_logo_icon


class MainWindow(QMainWindow):
    date_changed = pyqtSignal(object)    # datetime.date
    option_changed = pyqtSignal(object)  # str | None
    file_selected = pyqtSignal(str)
    action_triggered = pyqtSignal(str)   # action id

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._busy = False
        self.setWindowTitle(config.APP_TITLE)
        self.setWindowIcon(make_logo_icon())
        self.setMinimumSize(*config.WINDOW_MIN_SIZE)
        self.resize(*config.WINDOW_DEFAULT_SIZE)
        self._build_ui()
        self._connect_signals()

    # --- construction -----------------------------------------------------
    def _build_ui(self) -> None:
        self.date_field = DateField(config.DATE_LABEL, config.DATE_HINT, config.DATE_DISPLAY_FORMAT)
        self.combo_field = ComboField(config.COMBO_LABEL, config.COMBO_HINT,
                                      config.COMBO_PLACEHOLDER, config.COMBO_VALUES)
        self.file_picker = FilePicker(config.FILE_LABEL, config.FILE_HINT, config.FILE_PLACEHOLDER,
                                      config.FILE_DIALOG_FILTER, config.FILE_BROWSE_SHORTCUT)
        self.action_bar = ActionBar(config.ACTIONS)

        content = QWidget()
        content.setObjectName("Content")
        content.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(14)
        content_layout.addWidget(self.date_field)
        content_layout.addWidget(self.combo_field)
        content_layout.addWidget(self.file_picker)
        content_layout.addStretch(1)

        footer = QWidget()
        footer.setObjectName("Footer")
        footer.setAttribute(Qt.WA_StyledBackground, True)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(32, 14, 32, 14)
        footer_layout.addWidget(self.action_bar)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(HeaderBar(config.APP_TITLE, config.APP_COMPANY, config.APP_VERSION))
        root_layout.addWidget(AccentLine())
        root_layout.addWidget(content, 1)
        root_layout.addWidget(footer)
        self.setCentralWidget(root)

        self._status_label = QLabel()
        self._status_label.setObjectName("StatusLabel")
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.addWidget(self._status_label, 1)
        self.setStatusBar(status_bar)

    def _connect_signals(self) -> None:
        self.date_field.date_changed.connect(self.date_changed)
        self.combo_field.value_changed.connect(self.option_changed)
        self.file_picker.file_selected.connect(self.file_selected)
        self.action_bar.action_triggered.connect(self.action_triggered)

    # --- getters ----------------------------------------------------------
    def current_date(self) -> date:
        return self.date_field.date()

    def current_option(self) -> str | None:
        return self.combo_field.value()

    # --- setters (called by the controller) -------------------------------
    def set_date_message(self, message: DateMessage) -> None:
        self.date_field.set_message(message)

    def set_file_info(self, info: FileInfo) -> None:
        self.file_picker.set_file(str(info.path), f"{info.name} · {info.size_label}")

    def set_file_error(self, path: str, message: str) -> None:
        self.file_picker.set_error(path, message)

    def set_inputs_complete(self, complete: bool) -> None:
        self.action_bar.set_inputs_complete(complete)

    def set_busy(self, action_id: str | None) -> None:
        busy = action_id is not None
        for widget in (self.date_field, self.combo_field, self.file_picker):
            widget.setEnabled(not busy)
        self.action_bar.set_busy(action_id)
        if busy and not self._busy:
            QApplication.setOverrideCursor(Qt.BusyCursor)
        elif not busy and self._busy:
            QApplication.restoreOverrideCursor()
        self._busy = busy

    def show_status(self, text: str, level: StatusLevel = StatusLevel.INFO) -> None:
        self._status_label.setText(text)
        set_style_property(self._status_label, "level", level.value)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
