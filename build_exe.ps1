# Builds dist\MPR-automation.exe (one file, no console window).
# Usage, from the project root:  powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment not found: $python" }

& $python -m pip install --disable-pip-version-check -q -r (Join-Path $root "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

& $python -m PyInstaller (Join-Path $root "mpr_automation.spec") --clean --noconfirm `
    --distpath (Join-Path $root "dist") --workpath (Join-Path $root "build")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "Built $(Join-Path $root 'dist\MPR-automation.exe')"
