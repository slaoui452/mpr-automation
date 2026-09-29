"""Static application configuration.

Everything a non-developer might want to tweak (titles, labels, list values,
shortcuts, file filters) lives here, so the views and services stay generic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --- Application --------------------------------------------------------------
APP_TITLE = "MPR-automation"
APP_COMPANY = "SOCIÉTÉ GÉNÉRALE"
APP_VERSION = "0.1.0"

WINDOW_MIN_SIZE = (720, 560)
WINDOW_DEFAULT_SIZE = (820, 600)

# --- Paths --------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = "DEBUG"

# --- Date field ---------------------------------------------------------------
DATE_LABEL = "Reference date"
DATE_HINT = "The message updates as soon as you pick a date."
DATE_DISPLAY_FORMAT = "dd/MM/yyyy"

# --- Combo box ----------------------------------------------------------------
COMBO_LABEL = "Option"
COMBO_HINT = "Choose the value to apply."
COMBO_PLACEHOLDER = "Select…"
COMBO_VALUES = ("Option A", "Option B", "Option C")

# --- File input ---------------------------------------------------------------
FILE_LABEL = "Input file"
FILE_HINT = "Excel files only. Drag & drop a file here or click Browse."
FILE_PLACEHOLDER = "No file selected"
FILE_BROWSE_SHORTCUT = "Ctrl+O"
EXCEL_EXTENSIONS = (".xlsx", ".xlsm", ".xls", ".xlsb", ".xltx", ".xltm")
FILE_DIALOG_FILTER = "Excel files ({})".format(" ".join(f"*{ext}" for ext in EXCEL_EXTENSIONS))


# --- Actions ------------------------------------------------------------------
@dataclass(frozen=True)
class ActionSpec:
    id: str                          # must match a handler registered in MainController
    label: str
    tooltip: str
    shortcut: str
    variant: str                     # "ghost" | "secondary" | "primary" (see styles.qss)
    requires_complete_input: bool    # disabled until date + option + file are valid


ACTIONS = (
    ActionSpec("action_1", "Action 1", "Run action 1", "Ctrl+1", "ghost", False),
    ActionSpec("action_2", "Action 2", "Run action 2", "Ctrl+2", "secondary", True),
    ActionSpec("action_3", "Action 3", "Run action 3 (main action)", "Ctrl+3", "primary", True),
)


def action_by_id(action_id: str) -> ActionSpec:
    for spec in ACTIONS:
        if spec.id == action_id:
            return spec
    raise KeyError(f"Unknown action id: {action_id!r}")
