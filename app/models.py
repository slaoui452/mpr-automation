"""Plain data objects shared between the controller, the services and the view.

No Qt imports here: these objects travel freely between threads.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path


class MessageLevel(str, Enum):
    """Visual level of the date message (maps to the badge colour in styles.qss)."""
    TODAY = "today"
    PAST = "past"
    FUTURE = "future"


class StatusLevel(str, Enum):
    """Visual level of the status bar message (maps to styles.qss)."""
    INFO = "info"
    BUSY = "busy"
    SUCCESS = "success"
    ERROR = "error"


@dataclass(frozen=True)
class DateMessage:
    badge: str          # short label shown in the coloured badge, e.g. "TODAY"
    text: str           # full sentence shown next to the badge
    level: MessageLevel


@dataclass(frozen=True)
class FileInfo:
    path: Path
    size_bytes: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_label(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{self.size_bytes} B"


@dataclass(frozen=True)
class FormState:
    """Snapshot of every user input, handed to the action services."""
    reference_date: date
    option: str | None
    file: FileInfo | None

    @property
    def is_complete(self) -> bool:
        return self.option is not None and self.file is not None
