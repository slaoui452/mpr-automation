"""SG-style logo mark: red over black, split by a white bar. Drawn in code, so no image file is needed."""
from __future__ import annotations

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget

from app.ui.theme.tokens import COLORS


def paint_logo(painter: QPainter, rect: QRectF, outline: bool = False) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, False)
    half = rect.height() / 2
    painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), half), QColor(COLORS["red"]))
    painter.fillRect(QRectF(rect.left(), rect.top() + half, rect.width(), rect.height() - half),
                     QColor(COLORS["black"]))
    bar_w, bar_h = rect.width() * 0.62, max(1.0, rect.height() * 0.12)
    painter.fillRect(QRectF(rect.center().x() - bar_w / 2, rect.center().y() - bar_h / 2, bar_w, bar_h),
                     QColor(COLORS["white"]))
    if outline:  # keeps the black half visible on the black header
        painter.setPen(QColor(COLORS["white"]))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
    painter.restore()


def logo_pixmap(size: int, outline: bool = False) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    paint_logo(painter, QRectF(0, 0, size, size), outline)
    painter.end()
    return pixmap


def make_logo_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(logo_pixmap(size))
    return icon


class LogoMark(QWidget):
    """In Designer: a QWidget promoted to LogoMark. It paints the mark centred in its area."""

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        side = min(self.width(), self.height())
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        painter = QPainter(self)
        paint_logo(painter, rect, outline=True)
        painter.end()
