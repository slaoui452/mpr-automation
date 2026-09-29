"""Composition root: the only place that builds things and wires them together.

To plug in real implementations (a DB client, settings, ...), change the construction below,
e.g. MainPresenter(window, ActionService(db=MyDbClient())).
"""
from __future__ import annotations

import logging
import sys

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from app import config
from app.core import paths
from app.core.logging_setup import ActivityLogHandler, install_exception_hooks, setup_logging
from app.presenters.main_presenter import MainPresenter
from app.services.actions import ActionService
from app.ui.main_window import MainWindow
from app.ui.theme.theme import apply_theme

logger = logging.getLogger(__name__)


def run(argv: list[str] | None = None) -> int:
    log_file = setup_logging(paths.log_dir())
    install_exception_hooks()
    logger.debug("Starting %s v%s (frozen: %s)", config.APP_NAME, config.APP_VERSION, paths.is_frozen())

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))  # English names, Monday first

    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)

    try:
        apply_theme(app)
        window = MainWindow(log_file)
        presenter = MainPresenter(window, ActionService())
    except Exception as exc:  # noqa: BLE001 - explain any startup problem instead of vanishing
        logger.critical("Startup failed: %s", exc, exc_info=True)
        QMessageBox.critical(None, f"{config.APP_NAME} can't start", f"{exc}\n\nDetails in {log_file}")
        return 1

    panel_handler = ActivityLogHandler(config.LOG_LEVEL_PANEL)
    panel_handler.bridge.entry.connect(window.append_activity)
    logging.getLogger().addHandler(panel_handler)
    app.aboutToQuit.connect(lambda: logging.getLogger().removeHandler(panel_handler))
    app.aboutToQuit.connect(presenter.shutdown)

    presenter.start()
    window.show()
    return app.exec_()
