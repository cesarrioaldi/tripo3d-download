@echo off
rem Installer for Windows.  Double-click or run: install.bat
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install it from https://python.org  ^(tick "Add python.exe to PATH"^)
    pause
    exit /b 1
)

if not exist .venv (
    python -m venv .venv || (echo Failed to create venv & pause & exit /b 1)
)
call .venv\Scripts\python.exe -m pip install --upgrade pip -q
call .venv\Scripts\python.exe -m pip install -r requirements.txt -q

echo.
echo Done. Launching GUI...
start "" "%~dp0Tripo DL.bat"
