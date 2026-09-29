"""Base card: a white, square-cornered panel with a title, an optional hint and a body."""
from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Card(QFrame):

    def __init__(self, title: str, hint: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")

        self._title = QLabel(title.upper())
        self._title.setObjectName("CardTitle")
        font = self._title.font()
        font.setLetterSpacing(font.AbsoluteSpacing, 0.8)
        self._title.setFont(font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(self._title)

        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("CardHint")
            hint_label.setWordWrap(True)
            layout.addWidget(hint_label)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        layout.addLayout(self.body)
