"""Runs one action at a time in a background QThread and reports back through signals."""
from __future__ import annotations

import logging
import threading
from typing import Callable

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.core.models import ActionResult, FormState
from app.core.tasks import TaskCancelled, TaskContext

logger = logging.getLogger(__name__)

ActionFn = Callable[[FormState, TaskContext], object]


class _TaskThread(QThread):
    progressed = pyqtSignal(object, str)   # percent (int | None), text
    succeeded = pyqtSignal(object)         # ActionResult
    failed = pyqtSignal(object)            # the exception raised by the action

    def __init__(self, fn: ActionFn, state: FormState, name: str, parent: QObject) -> None:
        super().__init__(parent)
        self._fn = fn
        self._state = state
        self._name = name
        self.context = TaskContext(self.progressed.emit)

    def run(self) -> None:
        threading.current_thread().name = self._name   # log lines show which action wrote them
        try:
            result = _as_result(self._fn(self._state, self.context), self._name)
        except TaskCancelled:
            result = ActionResult.cancelled()
        except BaseException as exc:  # noqa: BLE001 - every failure is reported to the UI
            self.failed.emit(exc)
            return
        self.succeeded.emit(result)


def _as_result(value: object, name: str) -> ActionResult:
    if isinstance(value, ActionResult):
        return value
    if value is None:
        return ActionResult.ok()
    if isinstance(value, str):
        return ActionResult.ok(value)
    raise TypeError(f"{name}() returned {type(value).__name__!r} instead of an ActionResult (or a str).")


class TaskRunner(QObject):
    """Starts actions in a background thread, one at a time. Signals arrive in the UI thread."""
    progressed = pyqtSignal(object, str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: _TaskThread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(self, fn: ActionFn, state: FormState, name: str) -> None:
        if self._thread is not None:
            raise RuntimeError("An action is already running.")
        thread = _TaskThread(fn, state, name, parent=self)
        thread.progressed.connect(self.progressed)
        thread.succeeded.connect(self.succeeded)
        thread.failed.connect(self.failed)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        thread.start()

    def cancel(self) -> None:
        if self._thread is not None:
            self._thread.context.cancel()

    def shutdown(self, timeout_ms: int = 3000) -> None:
        """Called when the app quits: asks the action to stop and waits for it a little."""
        thread = self._thread
        if thread is None:
            return
        thread.context.cancel()
        if not thread.wait(timeout_ms):
            logger.warning("The running action ignored the cancel request; stopping it forcibly.")
            thread.terminate()
            thread.wait()

    def _on_thread_finished(self) -> None:
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.deleteLater()
        self.finished.emit()
