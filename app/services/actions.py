"""The action tiles' logic: one method per tile. YOUR CODE GOES HERE.

A tile runs the method whose name is the tile's `actionId` (set in Qt Designer).
Each method:
  - receives `state` (reference_date, option, file) and `task` (progress + cancel),
  - returns an ActionResult (or a plain str, shown as a success message),
  - raises an exception to report a failure (message in the activity panel, traceback in the log).
It runs in a background thread: never touch a widget from here.
"""
from __future__ import annotations

import logging
import time

from app.core.models import ActionResult, FormState
from app.core.tasks import TaskContext

logger = logging.getLogger(__name__)


class ActionService:

    def __init__(self) -> None:
        # Give the service what it needs here (DB client, settings, ...), then build it
        # with those arguments in app/bootstrap.py.
        pass

    def action_1(self, state: FormState, task: TaskContext) -> ActionResult:
        """Action 1. Needs (set in Designer): date."""
        # TODO: replace this demo with the real logic.
        return _demo_run(task, "Action 1")

    def action_2(self, state: FormState, task: TaskContext) -> ActionResult:
        """Action 2. Needs (set in Designer): date, option."""
        # TODO: replace this demo with the real logic.
        return _demo_run(task, "Action 2")

    def action_3(self, state: FormState, task: TaskContext) -> ActionResult:
        """Action 3. Needs (set in Designer): date, option, file."""
        # TODO: replace this demo with the real logic, e.g. read state.file.path with pandas.
        return _demo_run(task, "Action 3")


def _demo_run(task: TaskContext, label: str, steps: int = 20, step_seconds: float = 0.1) -> ActionResult:
    """About 2 s of fake work, so the progress bar and Cancel can be tried before the real logic exists."""
    for step in range(1, steps + 1):
        if task.cancelled:
            return ActionResult.cancelled()
        time.sleep(step_seconds)
        task.progress(step * 100 // steps, f"Step {step}/{steps}")
    return ActionResult.ok(f"{label} demo finished. Replace it in app/services/actions.py")
