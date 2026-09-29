"""Black header with the SG-style logo mark (red over black, split by a white bar)."""
from __future__ import annotations

from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui import theme


def paint_logo(painter: QPainter, rect: QRectF, outline: bool = False) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, False)
    half = rect.height() / 2
    painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), half), QColor(theme.RED))
    painter.fillRect(QRectF(rect.left(), rect.top() + half, rect.width(), rect.height() - half),
                     QColor(theme.BLACK))
    bar_w, bar_h = rect.width() * 0.62, max(2.0, rect.height() * 0.12)
    painter.fillRect(QRectF(rect.center().x() - bar_w / 2, rect.center().y() - bar_h / 2, bar_w, bar_h),
                     QColor(theme.WHITE))
    if outline:  # keeps the black half visible on a black background
        painter.setPen(QPen(QColor(theme.WHITE), 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
    painter.restore()


def make_logo_icon(size: int = 64) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    paint_logo(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


class LogoMark(QWidget):

    def __init__(self, size: int = 34, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        paint_logo(painter, QRectF(self.rect()), outline=True)
        painter.end()


class HeaderBar(QWidget):

    def __init__(self, title: str, company: str, version: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setAttribute(Qt.WA_StyledBackground, True)

        company_label = QLabel(company)
        company_label.setObjectName("AppCompany")
        font = company_label.font()
        font.setLetterSpacing(font.AbsoluteSpacing, 1.5)
        company_label.setFont(font)

        title_label = QLabel(title)
        title_label.setObjectName("AppTitle")

        texts = QVBoxLayout()
        texts.setSpacing(0)
        texts.addWidget(company_label)
        texts.addWidget(title_label)

        version_label = QLabel(f"v{version}")
        version_label.setObjectName("AppVersion")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(14)
        layout.addWidget(LogoMark())
        layout.addLayout(texts)
        layout.addStretch(1)
        layout.addWidget(version_label, 0, Qt.AlignBottom)


class AccentLine(QFrame):
    """Thin SG-red line under the header."""

    def __init__(self, height: int = 3, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AccentLine")
        self.setFixedHeight(height)
