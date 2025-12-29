# Start backend and frontend using local Python 3.11 venv (.venv311)
# Saves PIDs to .server-pids.txt for stop_servers.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPy = Join-Path $root ".venv311\Scripts\python.exe"
$pidFile = Join-Path $root ".server-pids.txt"

if (!(Test-Path $venvPy)) {
    Write-Error ".venv311 not found. Run: py -3.11 -m venv .venv311; .venv311\\Scripts\\python.exe -m pip install -r backend\\requirements.txt"
}

function Start-App {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$WorkingDir,
        [Parameter(Mandatory = $true)][string]$CommandArgs
    )
    if ([string]::IsNullOrWhiteSpace($CommandArgs)) {
        throw "Argument list for $Name is empty."
    }
    Write-Host "Starting $Name..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath $venvPy -ArgumentList $CommandArgs -WorkingDirectory $WorkingDir -PassThru
    Write-Host "  PID $($proc.Id)" -ForegroundColor Green
    return $proc.Id
}

$pids = @()
$pids += Start-App -Name "Backend (8000)" -WorkingDir (Join-Path $root "backend") -CommandArgs "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$pids += Start-App -Name "Frontend (3000)" -WorkingDir (Join-Path $root "frontend") -CommandArgs "-m http.server 3000"

$pids | Out-File -FilePath $pidFile -Encoding ascii
Write-Host "PIDs saved to $pidFile" -ForegroundColor Yellow
Write-Host "Backend: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:3000" -ForegroundColor Green
