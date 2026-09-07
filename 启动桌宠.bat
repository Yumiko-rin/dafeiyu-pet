@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "桌宠.py"
) else (
    start "" pythonw "桌宠.py"
)
