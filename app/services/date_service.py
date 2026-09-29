"""Builds the message shown under the reference date.

Starter rule: how far the date is from today ("TODAY", "YESTERDAY", "3 DAYS AGO", "IN 2 DAYS").
Replace get_date_message() with your own rules (business days, cut-offs, holidays, ...).
"""
from __future__ import annotations

import logging
from datetime import date

from app.core.models import DateMessage, Tone

logger = logging.getLogger(__name__)

# English names, whatever the Windows language settings are.
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_MONTHS = ("January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December")


def get_date_message(selected: date, today: date | None = None) -> DateMessage:
    today = today or date.today()
    delta = (selected - today).days
    logger.debug("Date message for %s (%+d days)", selected, delta)
    text = long_date(selected)

    if delta == 0:
        return DateMessage("TODAY", text, Tone.TODAY)
    if delta == -1:
        return DateMessage("YESTERDAY", text, Tone.PAST)
    if delta == 1:
        return DateMessage("TOMORROW", text, Tone.FUTURE)
    if delta < 0:
        return DateMessage(f"{-delta} DAYS AGO", text, Tone.PAST)
    return DateMessage(f"IN {delta} DAYS", text, Tone.FUTURE)


def long_date(value: date) -> str:
    """'Tuesday 29 September 2026'"""
    return f"{_WEEKDAYS[value.weekday()]} {value.day} {_MONTHS[value.month - 1]} {value.year}"
