"""Connects the window to the services: the only module that knows both sides.

    view signal ──► presenter ──► service ──► presenter ──► view setter
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, replace
from datetime import date
from typing import Callable

from PyQt5.QtCore import QObject

from app import config
from app.core.errors import ConfigError, FileValidationError
from app.core.models import INPUT_NAMES, Activity, ActionResult, FormState, ResultStatus, TileSpec
from app.core.task_runner import TaskRunner
from app.services import date_service, file_service
from app.services.actions import ActionService
from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


@dataclass
class _Run:
    spec: TileSpec
    started: float
    cancelling: bool = False


class MainPresenter(QObject):

    def __init__(self, view: MainWindow, actions: ActionService, runner: TaskRunner | None = None) -> None:
        super().__init__()
        self._view = view
        specs = view.tile_specs()
        self._handlers = _resolve_handlers(specs, actions)
        self._tiles = {spec.action_id: spec for spec in specs}
        self._runner = runner or TaskRunner(self)
        self._state = FormState(reference_date=view.current_date())
        self._run: _Run | None = None
        self._close_when_done = False
        self._connect()

    def start(self) -> None:
        self._view.set_version(config.APP_VERSION)
        self._view.set_option_values(config.COMBO_VALUES)
        self._view.set_file_extensions(config.EXCEL_EXTENSIONS)
        self._on_date_changed(self._state.reference_date)
        self._view.set_status("Ready", busy=False)
        logger.info("%s v%s started", config.APP_NAME, config.APP_VERSION)

    def shutdown(self) -> None:
        self._runner.shutdown()

    def _connect(self) -> None:
        view, runner = self._view, self._runner
        view.date_changed.connect(self._on_date_changed)
        view.option_changed.connect(self._on_option_changed)
        view.file_chosen.connect(self._on_file_chosen)
        view.file_cleared.connect(self._on_file_cleared)
        view.action_requested.connect(self._on_action_requested)
        view.cancel_requested.connect(self._on_cancel_requested)
        view.set_close_guard(self._can_close)
        runner.progressed.connect(self._on_progress)
        runner.succeeded.connect(self._on_succeeded)
        runner.failed.connect(self._on_failed)
        runner.finished.connect(self._on_finished)

    # --- inputs ---------------------------------------------------------------
    def _on_date_changed(self, selected: date) -> None:
        self._state = replace(self._state, reference_date=selected)
        self._view.set_date_message(date_service.get_date_message(selected))
        self._refresh_tiles()

    def _on_option_changed(self, option: str | None) -> None:
        logger.debug("Option: %s", option)
        self._state = replace(self._state, option=option)
        self._refresh_tiles()

    def _on_file_chosen(self, path: str) -> None:
        try:
            info = file_service.validate_file(path, config.EXCEL_EXTENSIONS)
        except FileValidationError as exc:
            logger.info("File rejected: %s", exc)
            self._state = replace(self._state, file=None)
            self._view.show_file_error(str(exc))
        else:
            logger.info("File loaded: %s (%s)", info.name, info.size_label)
            self._state = replace(self._state, file=info)
            self._view.show_file(info)
        self._refresh_tiles()

    def _on_file_cleared(self) -> None:
        logger.debug("File removed")
        self._state = replace(self._state, file=None)
        self._view.clear_file()
        self._refresh_tiles()

    def _refresh_tiles(self) -> None:
        if self._run is not None:
            return  # every tile stays locked while an action runs
        for spec in self._tiles.values():
            missing = self._state.missing(spec.needs)
            if missing:
                self._view.set_tile_blocked(spec.action_id, missing)
            else:
                self._view.set_tile_ready(spec.action_id)

    # --- actions --------------------------------------------------------------
    def _on_action_requested(self, action_id: str) -> None:
        spec = self._tiles.get(action_id)
        if spec is None or self._run is not None or self._state.missing(spec.needs):
            return
        self._run = _Run(spec, time.monotonic())
        logger.info("%s started", spec.title, extra={"activity": Activity.START})
        logger.debug("%s input: %s", spec.title, self._state)
        self._view.set_busy(action_id)
        self._view.set_status(f"{spec.title} running…", busy=True)
        self._runner.start(self._handlers[action_id], self._state, name=action_id)

    def _on_progress(self, percent: int | None, text: str) -> None:
        run = self._run
        if run is None or run.cancelling:
            return
        self._view.set_tile_progress(run.spec.action_id, percent, text)
        suffix = f" — {percent}%" if percent is not None else "…"
        self._view.set_status(f"{run.spec.title} running{suffix}", busy=True)

    def _on_cancel_requested(self) -> None:
        run = self._run
        if run is None or run.cancelling:
            return
        run.cancelling = True
        logger.debug("Cancel requested for %s", run.spec.title)
        self._runner.cancel()
        self._view.set_tile_cancelling(run.spec.action_id)
        self._view.set_status(f"Cancelling {run.spec.title}…", busy=True)

    def _on_succeeded(self, result: ActionResult) -> None:
        run = self._run
        if run is None:
            return
        took = _duration(time.monotonic() - run.started)
        detail = f" — {result.message}" if result.message else ""
        if result.status is ResultStatus.CANCELLED:
            logger.info("%s cancelled after %s%s", run.spec.title, took, detail,
                        extra={"activity": Activity.CANCEL})
        elif result.status is ResultStatus.WARNING:
            logger.warning("%s finished in %s with a warning%s", run.spec.title, took, detail,
                           extra={"activity": Activity.WARNING})
        else:
            logger.info("%s completed in %s%s", run.spec.title, took, detail,
                        extra={"activity": Activity.SUCCESS})

    def _on_failed(self, error: BaseException) -> None:
        run = self._run
        title = run.spec.title if run else "Action"
        took = _duration(time.monotonic() - run.started) if run else "?"
        logger.error("%s failed after %s — %s", title, took, str(error) or type(error).__name__,
                     exc_info=error, extra={"activity": Activity.FAILURE})

    def _on_finished(self) -> None:
        self._run = None
        self._view.set_busy(None)
        self._refresh_tiles()
        self._view.set_status("Ready", busy=False)
        if self._close_when_done:
            self._view.close()

    # --- closing --------------------------------------------------------------
    def _can_close(self) -> bool:
        """Closing during a run cancels it first; the window closes once the action has stopped."""
        if self._run is None or self._close_when_done:
            return True
        self._close_when_done = True
        logger.info("Closing once %s has stopped…", self._run.spec.title)
        self._on_cancel_requested()
        return False


def _resolve_handlers(specs: list[TileSpec], actions: object) -> dict[str, Callable]:
    """Maps each tile to its ActionService method. Lists every problem at once, so a bad
    actionId or needs value set in Qt Designer is reported clearly at startup."""
    problems: list[str] = []
    handlers: dict[str, Callable] = {}
    service = type(actions).__name__
    if not specs:
        problems.append("main_window.ui contains no ActionTile.")
    for spec in specs:
        where = f"Tile '{spec.widget_name}'"
        if not spec.action_id:
            problems.append(f"{where} has no actionId.")
            continue
        if spec.action_id in handlers:
            problems.append(f"{where}: actionId '{spec.action_id}' is already used by another tile.")
            continue
        unknown = [name for name in spec.needs if name not in INPUT_NAMES]
        if unknown:
            problems.append(f"{where}: unknown needs {', '.join(unknown)} (allowed: {', '.join(INPUT_NAMES)}).")
        handler = None if spec.action_id.startswith("_") else getattr(actions, spec.action_id, None)
        if not callable(handler):
            problems.append(f"{where}: actionId '{spec.action_id}' has no method {service}.{spec.action_id}() "
                            "in app/services/actions.py.")
            continue
        handlers[spec.action_id] = handler
    if problems:
        raise ConfigError("The action tiles don't match the code:\n• " + "\n• ".join(problems))
    return handlers


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} s"
    return f"{int(seconds // 60)} min {int(seconds % 60):02d} s"
