"""Exceptions whose message is meant for the user."""


class AppError(Exception):
    """Base class for errors the app explains to the user."""


class FileValidationError(AppError):
    """The chosen file can't be used. The message is shown in the file drop zone."""


class UiContractError(AppError):
    """A .ui file lacks a widget the code needs (renamed or deleted in Qt Designer)."""


class ConfigError(AppError):
    """Invalid settings, e.g. a tile whose actionId has no method in ActionService."""
