"""MPR-automation entry point."""
from __future__ import annotations

import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from app import config
from app.controllers.main_controller import MainController
from app.logging_setup import setup_logging
from app.services.action_service import ActionService
from app.ui import theme
from app.views.main_window import MainWindow


def main() -> int:
    setup_logging()
    logging.getLogger(__name__).info("Starting %s v%s", config.APP_TITLE, config.APP_VERSION)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_TITLE)
    app.setStyle("Fusion")  # consistent rendering of the QSS across Windows versions
    app.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_PT))
    app.setStyleSheet(theme.load_stylesheet())

    window = MainWindow()
    controller = MainController(window, ActionService())
    app.aboutToQuit.connect(controller.shutdown)

    controller.start()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
