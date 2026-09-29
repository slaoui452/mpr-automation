# PyInstaller recipe for MPR-automation: one .exe file, no console window.
# Build with build_exe.ps1, or: .venv\Scripts\python.exe -m PyInstaller mpr_automation.spec --clean --noconfirm
from pathlib import Path

ROOT = Path(SPECPATH)  # noqa: F821 - SPECPATH is provided by PyInstaller

# Files read at runtime. Add new folders of data files here.
datas = [
    (str(ROOT / "app" / "ui" / "forms" / "*.ui"), "app/ui/forms"),
    (str(ROOT / "app" / "ui" / "theme" / "styles.qss"), "app/ui/theme"),
    (str(ROOT / "app" / "ui" / "theme" / "icons" / "*.svg"), "app/ui/theme/icons"),
]

# uic imports the promoted widgets named in the .ui files at runtime, which PyInstaller can't see.
# Add a line here for each new promoted widget module.
hiddenimports = [
    "app.ui.widgets.logo_mark",
    "app.ui.widgets.file_drop_zone",
    "app.ui.widgets.action_tile",
    "app.ui.widgets.activity_panel",
]

a = Analysis(  # noqa: F821
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MPR-automation",
    icon=str(ROOT / "app" / "ui" / "theme" / "icons" / "app.ico"),
    console=False,
    upx=False,
)
