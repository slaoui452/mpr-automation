"""Where files are, both when running from source and inside the PyInstaller .exe."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from app import config

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_frozen() -> bool:
    """True when running as the PyInstaller .exe."""
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    """A read-only file shipped with the app (.ui, .qss, icons)."""
    base = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return base.joinpath(*parts)


def log_dir() -> Path:
    """logs/ in the project, or %LOCALAPPDATA%/MPR-automation/logs for the .exe."""
    if is_frozen():
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        return root / config.APP_NAME / "logs"
    return PROJECT_ROOT / "logs"
