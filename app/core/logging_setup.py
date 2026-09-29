"""Logging: console, rotating file and activity panel, plus hooks so that no error goes unnoticed."""
from __future__ import annotations

import logging
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt5.QtCore import (QObject, QtCriticalMsg, QtDebugMsg, QtFatalMsg, QtInfoMsg, QtWarningMsg,
                          pyqtSignal, qInstallMessageHandler)

from app import config
from app.core.models import Activity

FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(threadName)-10s | %(name)s | %(message)s"


def setup_logging(log_dir: Path) -> Path:
    """Sends every log line to the console and to log_dir/app.log. Returns the log file path."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    formatter = logging.Formatter(FILE_FORMAT)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # PyQt's .ui loader logs every widget and property at DEBUG level: keep only its warnings.
    logging.getLogger("PyQt5.uic").setLevel(logging.WARNING)

    file_handler = RotatingFileHandler(log_file, maxBytes=config.LOG_MAX_BYTES,
                                       backupCount=config.LOG_BACKUP_COUNT, encoding="utf-8")
    file_handler.setLevel(config.LOG_LEVEL_FILE)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if sys.stderr is not None:  # None in the windowed .exe
        console = logging.StreamHandler()
        console.setLevel(config.LOG_LEVEL_FILE)
        console.setFormatter(formatter)
        root.addHandler(console)
    return log_file


def install_exception_hooks() -> None:
    """Logs uncaught exceptions instead of letting PyQt5 abort the app, and routes Qt's own warnings."""
    def on_uncaught(exc_type, exc, tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        logging.getLogger("uncaught").critical(
            "Unexpected error: %s: %s", exc_type.__name__, exc,
            exc_info=(exc_type, exc, tb), extra={"activity": Activity.FAILURE})

    sys.excepthook = on_uncaught
    threading.excepthook = lambda args: on_uncaught(args.exc_type, args.exc_value, args.exc_traceback)
    qInstallMessageHandler(_on_qt_message)


_QT_LEVELS = {QtDebugMsg: logging.DEBUG, QtInfoMsg: logging.INFO, QtWarningMsg: logging.WARNING,
              QtCriticalMsg: logging.ERROR, QtFatalMsg: logging.CRITICAL}


def _on_qt_message(msg_type, context, message) -> None:
    logging.getLogger("qt").log(_QT_LEVELS.get(msg_type, logging.WARNING), message)


class _LogBridge(QObject):
    entry = pyqtSignal(str, str, str)   # time, activity kind, text


class ActivityLogHandler(logging.Handler):
    """Forwards log records to the activity panel. Thread-safe: the Qt signal is queued to the UI thread."""

    def __init__(self, level: str | int = config.LOG_LEVEL_PANEL) -> None:
        super().__init__(level)
        self.bridge = _LogBridge()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            kind = Activity(getattr(record, "activity", None) or _kind_for_level(record.levelno))
            text = record.getMessage()
            if record.exc_info:
                text += "  (details in the log file)"
            time_text = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            self.bridge.entry.emit(time_text, kind.value, text)
        except RuntimeError:
            pass  # the panel is already gone (app closing)
        except Exception:  # noqa: BLE001 - a logging handler must never raise
            self.handleError(record)


def _kind_for_level(levelno: int) -> Activity:
    if levelno >= logging.ERROR:
        return Activity.FAILURE
    if levelno >= logging.WARNING:
        return Activity.WARNING
    return Activity.INFO
