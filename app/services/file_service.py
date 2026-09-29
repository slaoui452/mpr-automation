"""Validation of the file chosen by the user."""
from __future__ import annotations

import logging
from pathlib import Path

from app import config
from app.models import FileInfo

logger = logging.getLogger(__name__)


class FileValidationError(ValueError):
    """Raised when the selected file cannot be used. The message is shown to the user."""


def validate_file(path: str | Path, allowed_extensions=config.EXCEL_EXTENSIONS) -> FileInfo:
    file_path = Path(path)
    logger.debug("Validating file %s", file_path)

    if not file_path.exists():
        raise FileValidationError("The file does not exist.")
    if not file_path.is_file():
        raise FileValidationError("Please select a file, not a folder.")
    if file_path.suffix.lower() not in allowed_extensions:
        raise FileValidationError(
            f"Unsupported file type '{file_path.suffix or 'none'}'. "
            f"Expected an Excel file ({', '.join(allowed_extensions)})."
        )

    # TODO: add content checks here (expected sheets, columns, not locked, ...).
    return FileInfo(path=file_path, size_bytes=file_path.stat().st_size)
