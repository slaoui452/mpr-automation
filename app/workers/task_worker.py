"""Generic worker that runs any callable in a QThread, keeping the UI responsive."""
from __future__ import annotations

import logging
from typing import Any, Callable

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class TaskWorker(QObject):
    succeeded = pyqtSignal(object)   # return value of the callable
    failed = pyqtSignal(object)      # the raised exception
    finished = pyqtSignal()          # always emitted last

    def __init__(self, fn: Callable[..., Any], *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    @pyqtSlot()
    def run(self) -> None:
        name = getattr(self._fn, "__qualname__", repr(self._fn))
        logger.debug("Worker started: %s", name)
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - reported to the UI, never swallowed
            logger.exception("Worker failed: %s", name)
            self.failed.emit(exc)
        else:
            logger.debug("Worker succeeded: %s", name)
            self.succeeded.emit(result)
        finally:
            self.finished.emit()


def start_worker(worker: TaskWorker) -> QThread:
    """Move `worker` to a new thread, start it and clean both up when done.

    Connect to the worker's signals *before* calling this function.
    The caller must keep a reference to the returned thread until it finishes.
    """
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
