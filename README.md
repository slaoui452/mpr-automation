# MPR-automation

PyQt5 desktop application with a Société Générale look. It has:

- a **reference date** picker, with a message that updates when the date changes
- an **option** combo box
- an **Excel file** input (Browse button or drag & drop)
- **3 action buttons**, whose logic you implement

The UI, the wiring and the threading are already done. You only write the business logic in `app/services/`.

---

## 1. Running the app

### Requirements
- Python 3.10+ (developed with 3.12)
- PyQt5 5.15

### First-time setup
```bash
python -m venv .venv
```
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Start
```bash
.venv\Scripts\python.exe main.py
```

In PyCharm, set the project interpreter to `.venv\Scripts\python.exe`, then run `main.py`.

Logs are written to the console and to `logs/app.log`. That file rotates at 1 MB and keeps 3 backups.

---

## 2. Project structure

```
main.py                          Entry point: logging, theme, window, controller
requirements.txt
app/
  config.py                      Titles, labels, combo values, file types, actions, shortcuts
  models.py                      Plain data objects: FormState, FileInfo, DateMessage, levels
  logging_setup.py               Console + rotating file logging, uncaught-exception hook
  controllers/
    main_controller.py           Connects the view signals to the services, and service results back to the view
  services/                      YOUR LOGIC GOES HERE (no Qt imports)
    action_service.py            action_1 / action_2 / action_3
    date_service.py              Message shown next to the date
    file_service.py              Validation of the selected file
  workers/
    task_worker.py               Runs a function in a QThread (keeps the UI responsive)
  views/                         Pure UI: no business logic
    main_window.py               Composes the widgets, exposes signals and setters
    style_utils.py
    widgets/                     header_bar, card, date_field, combo_field, file_picker, action_bar
  ui/
    theme.py                     Colour palette (SG red / black / white)
    styles.qss                   Stylesheet ($tokens are replaced from theme.py)
    assets/                      Icons used by the stylesheet
logs/                            Created at runtime
```

### How it fits together

```
 User ──► View (widgets) ──signal──► MainController ──► services (your code)
                ▲                         │
                └──────── setters ◄───────┘  (status, messages, errors)
```

- **Views** only display things and emit signals. They never call services.
- **Services** contain the logic. They never import PyQt, so you can test them on their own.
- **The controller** is the only place that knows both sides.

---

## 3. Implementing the button logic

Open `app/services/action_service.py`:

```python
class ActionService:

    def action_1(self, state: FormState) -> str:
        logger.info("action_1 called with %s", state)
        # TODO: implement Action 1.
        return "Action 1 completed (stub)."
```

### What you receive: `FormState`
| Field | Type | Notes |
|---|---|---|
| `state.reference_date` | `datetime.date` | Always set |
| `state.option` | `str \| None` | `None` while the combo still shows "Select…" |
| `state.file` | `FileInfo \| None` | Already validated by `file_service`. Use `state.file.path` (a `pathlib.Path`), `.name` and `.size_bytes` |
| `state.is_complete` | `bool` | `True` when both the option and the file are set |

> Actions 2 and 3 only run when `is_complete` is true.
> Action 1 can run with an incomplete form, so check for `None` before using `option` or `file`.
> You can change this per action with `requires_complete_input` in `config.py`.

### What you return, or raise
- **Return a string.** It is shown in green in the status bar, for example `return f"{n} rows extracted"`.
- **Raise an exception.** The app shows an error dialog, prints the message in red in the status bar, and logs the full traceback to `logs/app.log`.

```python
def action_3(self, state: FormState) -> str:
    import pandas as pd  # add pandas + openpyxl to requirements.txt if you use them

    df = pd.read_excel(state.file.path, sheet_name=0)
    if df.empty:
        raise ValueError("The selected file contains no data.")

    filtered = df[df["Date"] == pd.Timestamp(state.reference_date)]
    output = state.file.path.with_name(f"extract_{state.option}_{state.reference_date:%Y%m%d}.xlsx")
    filtered.to_excel(output, index=False)
    return f"{len(filtered)} rows written to {output.name}"
```

### Rules
1. **Do not touch widgets** from an action. It runs in a background thread, so return a value instead.
2. **Long work is fine.** The UI stays responsive, the inputs are locked, and the button shows "Running…".
3. Only **one action runs at a time**. Clicks made during a run are ignored.
4. If you need dependencies such as a DB client or config, give them to `ActionService` through `__init__` and build it in `main.py`:
   ```python
   controller = MainController(window, ActionService(db=MyDbClient()))
   ```

### Renaming buttons or changing their behaviour (`app/config.py`)
```python
ACTIONS = (
    ActionSpec("action_1", "Action 1", "Run action 1", "Ctrl+1", "ghost",     False),
    ActionSpec("action_2", "Action 2", "Run action 2", "Ctrl+2", "secondary", True),
    ActionSpec("action_3", "Action 3", "Run action 3 (main action)", "Ctrl+3", "primary", True),
)
#           id          label       tooltip         shortcut  style        requires_complete_input
```
Styles: `primary` (SG red, for the main action), `secondary` (black), `ghost` (outlined).

### Adding a 4th button
1. `config.py`: add `ActionSpec("action_4", "Export", "Export results", "Ctrl+4", "ghost", True)`.
2. `action_service.py`: add `def action_4(self, state: FormState) -> str: ...`.
3. `main_controller.py`: add `"action_4": action_service.action_4,` to `self._handlers`.

If step 3 is missing, the app refuses to start and names the action that has no handler.

---

## 4. Other customisation points

### Date message (`app/services/date_service.py`)
`get_date_message(selected)` must return `DateMessage(badge, text, level)`:
- `badge`: short text shown in the coloured box, for example `"TODAY"`
- `text`: the sentence next to it
- `level`: `MessageLevel.TODAY` (red), `PAST` (black) or `FUTURE` (grey)

The current rule is only past, today or future. Replace it with your own, for example business days or holidays.

### File validation (`app/services/file_service.py`)
Add checks at the `TODO`, such as expected sheets or required columns.
`raise FileValidationError("Sheet 'Data' is missing.")` shows the message in red under the field and keeps the action buttons disabled.
Allowed extensions are set by `EXCEL_EXTENSIONS` in `config.py`.

### Combo box values (`app/config.py`)
Edit `COMBO_LABEL`, `COMBO_PLACEHOLDER` and `COMBO_VALUES`.

### Labels, title, window size (`app/config.py`)
Every visible text is in `config.py`.

### Colours and style
- Colours: `app/ui/theme.py`
- Rules: `app/ui/styles.qss`. Use `$red`, `$black` and the other colour names defined in `theme.py`. Do not write a literal `$` anywhere else in the file, including comments.

---

## 5. Debugging

- **Logs:** every module has its own logger (`logging.getLogger(__name__)`). Each line shows the time, level, thread and module:
  ```
  14:55:15 | INFO | Dummy-1 | app.services.action_service | action_3 called with FormState(...)
  ```
  `Dummy-1` means the line came from the worker thread.
- **Log level:** `LOG_LEVEL` in `config.py` (`"DEBUG"`, `"INFO"`, and so on).
- **Crashes:** uncaught exceptions are logged as `CRITICAL` instead of silently killing the app.
- **Breakpoints:** PyCharm breakpoints in the services work on the main thread. For code in the worker thread (`action_*`), turn on **Settings → Build, Execution, Deployment → Python Debugger → "PyQt compatible"**. Alternatively, call the service directly from a script or test:
  ```python
  from datetime import date
  from pathlib import Path
  from app.models import FormState, FileInfo
  from app.services.action_service import ActionService

  f = Path("sample.xlsx")
  print(ActionService().action_3(FormState(date.today(), "Option A", FileInfo(f, f.stat().st_size))))
  ```

---

## 6. Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Browse for a file |
| `Ctrl+1` / `Ctrl+2` / `Ctrl+3` | Action 1 / 2 / 3 |
| `Tab` | Move between fields |
