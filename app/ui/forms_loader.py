"""Loads the Qt Designer .ui files and checks they contain the widgets the code expects."""
from __future__ import annotations

import typing

from PyQt5 import uic
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget

from app.core.errors import UiContractError
from app.core.paths import resource_path

FORMS_DIR = ("app", "ui", "forms")


def load_form(form_name: str, instance: QWidget) -> None:
    """Builds the widgets of forms/<form_name> inside `instance`. No compile step: edit, save, rerun."""
    uic.loadUi(str(resource_path(*FORMS_DIR, form_name)), instance)


def bind_widgets(owner: QWidget, form_name: str) -> None:
    """Checks that every widget annotated on the owner's class exists in the form, with the right type.

    Class-level annotations such as `dateEdit: QDateEdit` are the contract with Qt Designer: each name
    is the objectName of a widget in the .ui file. Renaming or deleting one in Designer then gives a
    clear error at startup instead of an AttributeError later.
    """
    problems = []
    for name, expected in _widget_annotations(type(owner)).items():
        found = owner.findChild(QObject, name)
        if found is None:
            problems.append(f"no widget named '{name}' (expected a {expected.__name__})")
        elif not isinstance(found, expected):
            problems.append(f"'{name}' is a {type(found).__name__}, expected a {expected.__name__}")
        else:
            setattr(owner, name, found)
    if problems:
        details = "\n".join(f"  • {problem}" for problem in problems)
        raise UiContractError(f"{form_name} doesn't match {type(owner).__name__}:\n{details}\n"
                              "Restore the objectName in Qt Designer (Object Inspector), "
                              "or update the annotations in the class.")


def _widget_annotations(cls: type) -> dict[str, type]:
    hints = typing.get_type_hints(cls)
    return {name: hint for name, hint in hints.items()
            if isinstance(hint, type) and issubclass(hint, QObject) and not name.startswith("_")}
