"""What an action receives to report progress and to notice a cancel request (no Qt)."""
from __future__ import annotations

import threading
from typing import Callable

ProgressCallback = Callable[[int | None, str], None]


class TaskCancelled(Exception):
    """Raised by TaskContext.raise_if_cancelled(). The run then ends as 'cancelled', not 'failed'."""


class TaskContext:
    """Handed to every action. Safe to use from the background thread."""

    def __init__(self, on_progress: ProgressCallback | None = None) -> None:
        self._on_progress = on_progress or (lambda percent, text: None)
        self._cancel = threading.Event()

    @property
    def cancelled(self) -> bool:
        """True once the user clicked Cancel or pressed Esc. Check it between steps."""
        return self._cancel.is_set()

    def raise_if_cancelled(self) -> None:
        """Stops the action right here if a cancel was requested (handy in deep code)."""
        if self._cancel.is_set():
            raise TaskCancelled()

    def progress(self, percent: int | None = None, text: str = "") -> None:
        """Updates the tile: percent from 0 to 100 (None = moving bar without a figure) and a short text."""
        if percent is not None:
            percent = max(0, min(100, int(percent)))
        self._on_progress(percent, text)

    def cancel(self) -> None:
        """Called by the app when the user asks to cancel."""
        self._cancel.set()
