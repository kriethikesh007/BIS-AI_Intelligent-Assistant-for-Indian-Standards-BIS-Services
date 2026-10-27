@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    echo [BIS-AI] Starting server with virtualenv Python...
    ".venv\Scripts\python.exe" app.py
) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    echo [BIS-AI] Starting server with Python 3.13...
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
) else (
    echo [BIS-AI] Trying system python...
    python app.py
)
pause
