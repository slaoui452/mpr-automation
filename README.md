# MPR-automation

PyQt5 desktop tool with a Société Générale look. Pick a **reference date**, an **option** and an
**Excel file**, then run one of the **action tiles**. Every run and log line shows up in the
**activity panel** at the bottom.

The UI, the wiring, the background threads and the logging are done. You write the business logic
in `app/services/` and change the look in **Qt Designer**.

---

## 1. Run it

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```
```bash
.venv\Scripts\python.exe main.py
```
In PyCharm: interpreter `.venv\Scripts\python.exe`, then run `main.py`.

---

## 2. How the code is organised (layered MVP)

```
main.py                       entry point → app.bootstrap.run()
app/
├── bootstrap.py              builds and wires everything (the only place that creates objects)
├── config.py                 data settings: COMBO_VALUES, EXCEL_EXTENSIONS, log levels, version
├── core/                     infrastructure, no business logic
│   ├── models.py             FormState, FileInfo, DateMessage, ActionResult, TileSpec
│   ├── tasks.py              TaskContext: progress + cancel, handed to every action (no Qt)
│   ├── task_runner.py        runs one action at a time in a QThread
│   ├── logging_setup.py      console + rotating file + activity panel, uncaught-error hooks
│   ├── paths.py              file locations, from source or inside the .exe
│   └── errors.py             FileValidationError, UiContractError, ConfigError
├── services/                 ← YOUR LOGIC (never imports PyQt)
│   ├── actions.py            action_1 / action_2 / action_3
│   ├── date_service.py       the message under the date
│   └── file_service.py       checks on the chosen file
├── presenters/
│   └── main_presenter.py     the only module that knows both the view and the services
└── ui/                       no business logic
    ├── main_window.py        loads the .ui, exposes signals and setters (passive view)
    ├── forms_loader.py       loads .ui files + the startup check (see §4)
    ├── forms/                ← OPEN THESE IN QT DESIGNER
    │   ├── main_window.ui    the whole window, every static text, the 3 tiles
    │   └── action_tile.ui    the inside of one tile (shared by every tile)
    ├── widgets/              promoted widgets: logo_mark, file_drop_zone, action_tile, activity_panel
    └── theme/                tokens.py (colours), styles.qss (rules), theme.py, icons/
tools/make_icon.py            regenerates the .exe icon
mpr_automation.spec           PyInstaller recipe      build_exe.ps1   builds the .exe
```

```
 user ──► widget ──► MainWindow signal ──► MainPresenter ──► service (your code)
                          ▲                      │
                          └──── setters ◄────────┘
```
- The **view** only displays things and emits signals. It never calls a service.
- **Services** hold the logic and never import PyQt, so you can run and test them on their own.
- The **presenter** is the glue: it listens to the view, calls the services and updates the view.
- **bootstrap.py** is the only place that builds objects. To swap a stub for a real implementation, change one line there.

---

## 3. Writing an action

A tile runs the `ActionService` method whose name is the tile's `actionId` (set in Designer).
Open `app/services/actions.py`:

```python
def action_3(self, state: FormState, task: TaskContext) -> ActionResult:
    import pandas as pd                       # add pandas + openpyxl to requirements.txt

    task.progress(10, "Reading the file…")
    df = pd.read_excel(state.file.path)
    if df.empty:
        raise ValueError("The file contains no data.")        # → red line + traceback in the log

    rows = df[df["Date"] == pd.Timestamp(state.reference_date)]
    for i, (_, row) in enumerate(rows.iterrows(), 1):
        if task.cancelled:                                     # user clicked Cancel or pressed Esc
            return ActionResult.cancelled()
        task.progress(i * 100 // len(rows), f"Row {i}/{len(rows)}")
        ...
    return ActionResult.ok(f"{len(rows)} rows extracted")      # → green line in the activity panel
```

**What you receive**

| | Type | Notes |
|---|---|---|
| `state.reference_date` | `datetime.date` | always set |
| `state.option` | `str \| None` | `None` if the tile doesn't need `option` and none is chosen |
| `state.file` | `FileInfo \| None` | already validated; `.path` (Path), `.name`, `.size_bytes`, `.modified` |
| `task.progress(percent, text)` | | updates the tile; `percent=None` gives a moving bar |
| `task.cancelled` / `task.raise_if_cancelled()` | | cancel is cooperative: check it between steps |

**What you return**: `ActionResult.ok("…")`, `ActionResult.warning("…")` (amber), `ActionResult.cancelled()`,
or a plain `str` (treated as ok). **To report a failure, raise an exception.**

**Rules**
1. Actions run in a background thread: **never touch a widget** from an action. Return a result instead.
2. One action runs at a time. The inputs and the other tiles are locked meanwhile.
3. Use `logging.getLogger(__name__)` in your services: INFO lines appear in the activity panel too.
4. Dependencies (DB client, settings…) go through `ActionService.__init__`, built in `app/bootstrap.py`.

**Try an action without the UI** (in a script or the PyCharm console):
```python
from datetime import date
from pathlib import Path
from app.core.models import FormState
from app.core.tasks import TaskContext
from app.services.actions import ActionService
from app.services.file_service import validate_file

state = FormState(date.today(), "Option A", validate_file(Path("sample.xlsx")))
print(ActionService().action_3(state, TaskContext(lambda p, t: print(p, t))))
```

---

## 4. Editing the UI in Qt Designer

Designer (Qt 5.15.2, same Qt as the venv) comes with Anaconda (command for cmd):
```bat
"%USERPROFILE%\anaconda3\Library\bin\designer.exe" app\ui\forms\main_window.ui
```
*PyCharm tip:* Settings → Tools → External Tools → `+`, Program = the path above, Arguments = `$FilePath$`.
Then right-click any `.ui` file → External Tools → Designer.

There's **no compile step**: the `.ui` files are loaded at runtime. Save in Designer, then rerun `main.py`.

**What you'll see in Designer**: layout and texts in the default Qt look. The SG styling (`styles.qss`) is applied
only when the app runs. The promoted widgets (logo, drop zone, tiles, activity panel) show as plain frames.

**The action tiles**: each is a `QFrame` promoted to `ActionTile`. Click one and look at *Dynamic Properties*
in the Property Editor:

| Property | Example | Meaning |
|---|---|---|
| `actionId` | `action_3` | the `ActionService` method to run |
| `title` | `Extract` | shown in capitals on the tile, and used in the activity panel |
| `description` | `Pulls the rows…` | one short sentence |
| `needs` | `date, option, file` | inputs required before the tile unlocks ("Needs: …" otherwise) |
| `shortcut` | `Ctrl+3` | keyboard shortcut, shown on the tile |

**Add a 4th action**: copy-paste a tile in Designer, set `actionId = action_4` and its texts, then write
`action_4()` in `actions.py`. Nothing else to change (fix the tab order with Edit → Edit Tab Order if you like).

**Styling roles**: most widgets have a dynamic property `role` (`card`, `fieldLabel`, `link`, `secondary`,
`sectionTitle`, `badge`, `kbd`, …). `styles.qss` styles by role, so a new label with `role = hint` looks like the
other hints. To restyle, change a colour in `tokens.py` or a rule in `styles.qss` (colours are written `$red`,
`$border`…; write a literal dollar sign as `$$`).

**Filled in by the code at runtime** (what Designer shows there is only a sample): `versionLabel`
(`APP_VERSION`), `optionCombo` items (`COMBO_VALUES`; the placeholder text comes from Designer), `fileHintLabel`
(`EXCEL_EXTENSIONS`), `dateBadge` / `dateMessage` (date service), the file name, size and error labels, and the
tile progress and "Needs" texts.

**Startup check**: the widgets the code uses are declared as annotations at the top of `MainWindow`,
`FileDropZone`, `ActivityPanel` and `ActionTile` (e.g. `dateEdit: QDateEdit`). If a `.ui` edit renames or deletes
one of them, or a tile has an unknown `actionId` / `needs`, the app refuses to start and names the exact problem,
instead of failing later with an obscure `AttributeError`.

---

## 5. Other settings

| What | Where |
|---|---|
| Combo values | `COMBO_VALUES` in `app/config.py` |
| Accepted file types | `EXCEL_EXTENSIONS` in `app/config.py` |
| Extra file checks (sheets, columns…) | `app/services/file_service.py`: `raise FileValidationError("…")` shows the message in the drop zone |
| Date message rules | `app/services/date_service.py`: return `DateMessage(badge, text, tone)` with tone `TODAY` (red), `PAST` (black) or `FUTURE` (grey) |
| Colours / fonts | `app/ui/theme/tokens.py` |
| Log levels | `LOG_LEVEL_FILE`, `LOG_LEVEL_PANEL` in `app/config.py` |

---

## 6. Debugging

- **Log file**: `logs/app.log` (from source) or `%LOCALAPPDATA%\MPR-automation\logs\app.log` (the .exe). It
  rotates at 1 MB and keeps 3 old files. Each line shows time, level, thread and module:
  ```
  2026-09-29 16:51:45 | INFO     | action_3   | app.services.actions | Reading MPR_2026-09.xlsx
  ```
  Lines written from an action carry the action's name as the thread name.
- **Activity panel**: INFO and above, plus every run with its outcome and duration. Failures show the message
  there and the full traceback in the log file ("Open log file"). The panel reopens itself on an error.
- **Nothing dies silently**: uncaught exceptions are logged instead of letting PyQt5 close the app, and Qt's own
  warnings (e.g. a bad `styles.qss` rule) go to the log under the logger `qt`.
- **Breakpoints in actions** (background thread): in PyCharm, enable *Settings → Build, Execution, Deployment →
  Python Debugger → PyQt compatible*, or call the action directly from a script (see §3).

---

## 7. Build the .exe

```bash
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```
This produces `dist\MPR-automation.exe` (one file, no console window). It installs `requirements-dev.txt`
(PyInstaller) first. When you add data files or a new promoted widget module, add them to
`mpr_automation.spec`. To regenerate the icon: `.venv\Scripts\python.exe tools\make_icon.py`.

---

## 8. Keyboard

| Keys | Action |
|---|---|
| `Ctrl+1` / `Ctrl+2` / `Ctrl+3` | run a tile (set per tile in Designer) |
| `Enter` / `Space` | run the focused tile |
| `Esc` | cancel the running action |
| `Ctrl+O` | choose a file |
| `Tab` | move between fields and tiles |

---

## 9. Previous version

The first version is kept in git under the tag `v0.1-legacy`:
```bash
git diff v0.1-legacy --stat
```
