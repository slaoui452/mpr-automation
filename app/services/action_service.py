"""Business actions triggered by the three buttons.

These methods run in a worker thread: never touch Qt widgets from here.
Return a short message (shown in the status bar) or raise an exception
(shown in an error dialog and logged with its traceback).
"""
from __future__ import annotations

import logging

from app.models import FormState

logger = logging.getLogger(__name__)


class ActionService:

    def action_1(self, state: FormState) -> str:
        logger.info("action_1 called with %s", state)
        # TODO: implement Action 1. Note: available even if the form is incomplete.
        return "Action 1 completed (stub)."

    def action_2(self, state: FormState) -> str:
        logger.info("action_2 called with %s", state)
        # TODO: implement Action 2.
        return "Action 2 completed (stub)."

    def action_3(self, state: FormState) -> str:
        logger.info("action_3 called with %s", state)
        # TODO: implement Action 3 (main action).
        return "Action 3 completed (stub)."
