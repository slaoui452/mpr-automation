"""Plain data objects shared by the services, the presenter and the view (no Qt)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path

# Input names a tile can list in its `needs` property (set in Qt Designer).
INPUT_NAMES = ("date", "option", "file")


class Tone(str, Enum):
    """Colour of the badge next to the reference date."""
    TODAY = "today"
    PAST = "past"
    FUTURE = "future"


@dataclass(frozen=True)
class DateMessage:
    badge: str   # short text in the coloured box, e.g. "3 DAYS AGO"
    text: str    # text next to it, e.g. "Saturday 26 September 2026"
    tone: Tone


@dataclass(frozen=True)
class FileInfo:
    path: Path
    size_bytes: int
    modified: datetime

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_label(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} bytes"
        if self.size_bytes < 1024 ** 2:
            return f"{self.size_bytes / 1024:.0f} KB"
        return f"{self.size_bytes / 1024 ** 2:.1f} MB"


@dataclass(frozen=True)
class FormState:
    """Snapshot of the inputs. Each action receives the one taken when it was started."""
    reference_date: date
    option: str | None = None
    file: FileInfo | None = None

    def missing(self, needs: tuple[str, ...]) -> list[str]:
        """The inputs from `needs` that are not filled yet, e.g. ["file"]."""
        filled = {"date": self.reference_date is not None,
                  "option": self.option is not None,
                  "file": self.file is not None}
        return [name for name in needs if not filled[name]]


@dataclass(frozen=True)
class TileSpec:
    """What an action tile declares in Qt Designer (its dynamic properties)."""
    widget_name: str             # objectName of the tile, used in error messages
    action_id: str               # name of the ActionService method the tile runs
    title: str
    needs: tuple[str, ...]
    shortcut: str


class ResultStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ActionResult:
    """What an action returns. To report a failure, raise an exception instead."""
    status: ResultStatus
    message: str = ""

    @classmethod
    def ok(cls, message: str = "") -> ActionResult:
        return cls(ResultStatus.OK, message)

    @classmethod
    def warning(cls, message: str) -> ActionResult:
        """Finished, but with something the user should check (shown in amber)."""
        return cls(ResultStatus.WARNING, message)

    @classmethod
    def cancelled(cls, message: str = "") -> ActionResult:
        return cls(ResultStatus.CANCELLED, message)


class Activity(str, Enum):
    """How a line looks in the activity panel. Pass it with a log call:
    logger.info("...", extra={"activity": Activity.SUCCESS})"""
    START = "start"
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    CANCEL = "cancel"
    INFO = "info"
