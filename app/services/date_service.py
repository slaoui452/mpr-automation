"""Builds the message displayed next to the reference date.

Placeholder rule: past / today / future. Replace with your own business rules.
"""
from __future__ import annotations

import logging
from datetime import date

from app.models import DateMessage, MessageLevel

logger = logging.getLogger(__name__)


def get_date_message(selected: date, today: date | None = None) -> DateMessage:
    today = today or date.today()
    delta = (selected - today).days
    logger.debug("Date message for %s (delta=%d days)", selected, delta)

    # TODO: replace with the real rule (business days, cut-off, holidays, ...).
    if delta == 0:
        return DateMessage("TODAY", "Today — current business day", MessageLevel.TODAY)
    if delta < 0:
        return DateMessage("PAST", f"{_days(-delta)} in the past", MessageLevel.PAST)
    return DateMessage("FUTURE", f"{_days(delta)} in the future", MessageLevel.FUTURE)


def _days(count: int) -> str:
    return f"{count} day" if count == 1 else f"{count} days"
