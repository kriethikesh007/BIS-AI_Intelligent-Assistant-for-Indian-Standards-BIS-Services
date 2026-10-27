# BIS-AI PowerShell Launcher
$venvPython = "$PSScriptRoot\.venv\Scripts\python.exe"
$appDataPython = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"

if (Test-Path $venvPython) {
    Write-Host "[BIS-AI] Starting server with virtualenv Python at $venvPython..." -ForegroundColor Green
    & $venvPython app.py
} elseif (Test-Path $appDataPython) {
    Write-Host "[BIS-AI] Starting server with Python 3.13 at $appDataPython..." -ForegroundColor Green
    & $appDataPython app.py
} else {
    Write-Host "[BIS-AI] Trying system 'python'..." -ForegroundColor Yellow
    python app.py
}
