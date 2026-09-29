"""Central logging: console + rotating file, plus a hook for uncaught exceptions."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app import config

_FORMAT = "%(asctime)s | %(levelname)-8s | %(threadName)-10s | %(name)s | %(message)s"


def setup_logging() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL)
    root.addHandler(console)
    root.addHandler(file_handler)

    # PyQt5 aborts the process on an exception raised inside a slot unless a hook is set.
    sys.excepthook = _log_uncaught_exception


def _log_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("uncaught").critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
