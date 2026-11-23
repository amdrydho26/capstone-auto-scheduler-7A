# Script Runner PowerShell untuk Penjadwalan Otomatis STI
$pythonPath = "..\code\backend\venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "[ERROR] Virtual environment tidak ditemukan di $pythonPath" -ForegroundColor Red
    exit 1
}

& $pythonPath "run_scheduler.py"
