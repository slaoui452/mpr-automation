"""Glue between the view and the services.

The only module that knows both sides: view signals -> services -> view setters.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Callable

from PyQt5.QtCore import QObject, QThread, pyqtSlot

from app import config
from app.models import FileInfo, FormState, StatusLevel
from app.services import date_service, file_service
from app.services.action_service import ActionService
from app.views.main_window import MainWindow
from app.workers.task_worker import TaskWorker, start_worker

logger = logging.getLogger(__name__)

ActionHandler = Callable[[FormState], str]


class MainController(QObject):

    def __init__(self, view: MainWindow, action_service: ActionService, parent: QObject | None = None):
        super().__init__(parent)
        self._view = view
        self._handlers: dict[str, ActionHandler] = {
            "action_1": action_service.action_1,
            "action_2": action_service.action_2,
            "action_3": action_service.action_3,
        }
        self._check_handlers()

        # Current form state
        self._reference_date: date = view.current_date()
        self._option: str | None = view.current_option()
        self._file: FileInfo | None = None

        # Running task
        self._thread: QThread | None = None
        self._worker: TaskWorker | None = None
        self._running_action: config.ActionSpec | None = None

        self._connect_signals()

    def start(self) -> None:
        self._on_date_changed(self._reference_date)
        self._refresh_availability()
        self._view.show_status("Ready")
        logger.info("Controller started")

    def shutdown(self) -> None:
        if self._thread is not None:
            logger.warning("Application closing while '%s' is running; waiting for it",
                           self._running_action.id if self._running_action else "?")
            self._thread.quit()
            self._thread.wait(5000)

    # --- wiring -----------------------------------------------------------
    def _check_handlers(self) -> None:
        configured = {spec.id for spec in config.ACTIONS}
        missing = configured - self._handlers.keys()
        if missing:
            raise RuntimeError(f"No handler registered for action(s): {sorted(missing)}")

    def _connect_signals(self) -> None:
        self._view.date_changed.connect(self._on_date_changed)
        self._view.option_changed.connect(self._on_option_changed)
        self._view.file_selected.connect(self._on_file_selected)
        self._view.action_triggered.connect(self._on_action_triggered)

    # --- input handlers ---------------------------------------------------
    @pyqtSlot(object)
    def _on_date_changed(self, selected: date) -> None:
        self._reference_date = selected
        self._view.set_date_message(date_service.get_date_message(selected))
        logger.debug("Date changed: %s", selected)

    @pyqtSlot(object)
    def _on_option_changed(self, option: str | None) -> None:
        self._option = option
        logger.debug("Option changed: %s", option)
        self._refresh_availability()

    @pyqtSlot(str)
    def _on_file_selected(self, path: str) -> None:
        try:
            self._file = file_service.validate_file(path)
        except file_service.FileValidationError as exc:
            self._file = None
            logger.info("Rejected file %s: %s", path, exc)
            self._view.set_file_error(path, str(exc))
            self._view.show_status("Invalid file", StatusLevel.ERROR)
        else:
            logger.info("File selected: %s", self._file.path)
            self._view.set_file_info(self._file)
            self._view.show_status(f"File loaded: {self._file.name}", StatusLevel.SUCCESS)
        self._refresh_availability()

    def _build_state(self) -> FormState:
        return FormState(reference_date=self._reference_date, option=self._option, file=self._file)

    def _refresh_availability(self) -> None:
        self._view.set_inputs_complete(self._build_state().is_complete)

    # --- actions ----------------------------------------------------------
    @pyqtSlot(str)
    def _on_action_triggered(self, action_id: str) -> None:
        if self._thread is not None:
            logger.warning("Ignored '%s': another action is running", action_id)
            return

        spec = config.action_by_id(action_id)
        state = self._build_state()
        if spec.requires_complete_input and not state.is_complete:
            self._view.show_status("Please complete all fields first.", StatusLevel.ERROR)
            return

        logger.info("Running %s with %s", action_id, state)
        self._running_action = spec
        self._view.set_busy(action_id)
        self._view.show_status(f"{spec.label} running…", StatusLevel.BUSY)

        worker = TaskWorker(self._handlers[action_id], state)
        worker.succeeded.connect(self._on_action_succeeded)
        worker.failed.connect(self._on_action_failed)
        self._worker = worker
        self._thread = start_worker(worker)
        self._thread.finished.connect(self._on_thread_finished)

    @pyqtSlot(object)
    def _on_action_succeeded(self, result: object) -> None:
        label = self._running_action.label if self._running_action else "Action"
        self._view.show_status(str(result) if result else f"{label} completed.", StatusLevel.SUCCESS)

    @pyqtSlot(object)
    def _on_action_failed(self, error: object) -> None:
        label = self._running_action.label if self._running_action else "Action"
        self._view.show_status(f"{label} failed: {error}", StatusLevel.ERROR)
        self._view.show_error(f"{label} failed", f"{error}\n\nSee {config.LOG_FILE} for details.")

    @pyqtSlot()
    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._running_action = None
        self._view.set_busy(None)
