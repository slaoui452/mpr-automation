"""Reference date picker with a live message badge."""
from __future__ import annotations

from datetime import date

from PyQt5.QtCore import QDate, pyqtSignal
from PyQt5.QtWidgets import QDateEdit, QHBoxLayout, QLabel, QWidget

from app.models import DateMessage
from app.views.style_utils import set_style_property
from app.views.widgets.card import Card


class DateField(Card):
    date_changed = pyqtSignal(object)  # datetime.date

    def __init__(self, title: str, hint: str, display_format: str, parent: QWidget | None = None):
        super().__init__(title, hint, parent)

        self._edit = QDateEdit()
        self._edit.setCalendarPopup(True)
        self._edit.setDisplayFormat(display_format)
        self._edit.setDate(QDate.currentDate())
        self._edit.setMinimumWidth(170)
        self._edit.setToolTip("Pick a date (type it or open the calendar)")

        self._badge = QLabel()
        self._badge.setObjectName("Badge")
        self._message = QLabel()
        self._message.setObjectName("DateMessage")

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(self._edit)
        row.addSpacing(8)
        row.addWidget(self._badge)
        row.addWidget(self._message, 1)
        self.body.addLayout(row)

        self._edit.dateChanged.connect(lambda qdate: self.date_changed.emit(qdate.toPyDate()))

    def date(self) -> date:
        return self._edit.date().toPyDate()

    def set_message(self, message: DateMessage) -> None:
        self._badge.setText(message.badge)
        self._message.setText(message.text)
        set_style_property(self._badge, "level", message.level.value)
