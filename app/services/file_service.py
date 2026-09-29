"""Checks the file chosen in the drop zone before any action can use it."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app import config
from app.core.errors import FileValidationError
from app.core.models import FileInfo

logger = logging.getLogger(__name__)


def validate_file(path: str | Path, allowed_extensions: Iterable[str] = config.EXCEL_EXTENSIONS) -> FileInfo:
    """Returns the file's details, or raises FileValidationError with a message for the user."""
    file = Path(path)
    logger.debug("Validating %s", file)
    allowed = tuple(ext.lower() for ext in allowed_extensions)

    if file.suffix.lower() not in allowed:
        raise FileValidationError(f"'{file.name}' isn't an Excel file. Use {', '.join(allowed)}.")
    if not file.is_file():
        raise FileValidationError(f"'{file.name}' can't be found. It may have been moved or deleted.")
    stat = file.stat()
    if stat.st_size == 0:
        raise FileValidationError(f"'{file.name}' is empty.")

    # TODO: add your own checks here, for example expected sheets or required columns:
    #     raise FileValidationError("Sheet 'Data' is missing.")

    return FileInfo(path=file, size_bytes=stat.st_size, modified=datetime.fromtimestamp(stat.st_mtime))
