# Stop backend and frontend started by start_servers.ps1

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root ".server-pids.txt"

if (!(Test-Path $pidFile)) {
    Write-Host "No pid file found ($pidFile)." -ForegroundColor Yellow
    exit 0
}

$pids = Get-Content $pidFile | Where-Object { $_ -match '^[0-9]+$' }
if (-not $pids) {
    Write-Host "PID file empty." -ForegroundColor Yellow
    exit 0
}

foreach ($pid in $pids) {
    Write-Host "Stopping PID $pid" -ForegroundColor Cyan
    Stop-Process -Id $pid -Force
}

Remove-Item $pidFile -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green
