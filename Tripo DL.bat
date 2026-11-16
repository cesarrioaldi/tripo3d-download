@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" tripo_app.py
) else (
    start "" pythonw tripo_app.py
)
