"""Application settings: everything that is data rather than layout.

Layout and visible texts live in the .ui files (app/ui/forms), edited with Qt Designer.
"""
from __future__ import annotations

APP_NAME = "MPR-automation"      # also the folder name of the .exe logs (%LOCALAPPDATA%)
APP_VERSION = "1.0.0"            # shown in the header

# --- Option combo box ---------------------------------------------------------
COMBO_VALUES: tuple[str, ...] = ("Option A", "Option B", "Option C")

# --- Input file ---------------------------------------------------------------
EXCEL_EXTENSIONS: tuple[str, ...] = (".xlsx", ".xlsm", ".xls")

# --- Logging ------------------------------------------------------------------
LOG_LEVEL_FILE = "DEBUG"         # logs/app.log and the console
LOG_LEVEL_PANEL = "INFO"         # the activity panel at the bottom of the window
LOG_MAX_BYTES = 1_000_000        # app.log rotates at this size...
LOG_BACKUP_COUNT = 3             # ...and keeps this many old files
