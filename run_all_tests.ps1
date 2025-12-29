# ═══════════════════════════════════════════════════════════
# WEBGST - ONE-GO TEST RUNNER (PowerShell)
# ═══════════════════════════════════════════════════════════
# Run all backend tests with a single command
#
# Usage: .\run_all_tests.ps1

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $root ".venv311\Scripts\python.exe"
$backendDir = Join-Path $root "backend"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  WEBGST - COMPREHENSIVE TEST SUITE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path $venvPy)) {
    Write-Host "❌ ERROR: .venv311 not found" -ForegroundColor Red
    Write-Host "   Run: py -3.11 -m venv .venv311" -ForegroundColor Yellow
    Write-Host "   Then: .venv311\Scripts\pip install -r backend\requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if pytest is installed
Write-Host "Checking test dependencies..." -ForegroundColor Yellow
$checkPytest = & $venvPy -c "import pytest; print('OK')" 2>&1
if ($checkPytest -notmatch "OK") {
    Write-Host "❌ pytest not installed. Installing..." -ForegroundColor Red
    & $venvPy -m pip install pytest pytest-cov httpx
}

Write-Host "✓ Test dependencies ready" -ForegroundColor Green
Write-Host ""

# Change to backend directory
Push-Location $backendDir

Write-Host "Running comprehensive test suite..." -ForegroundColor Cyan
Write-Host ""

# Run all tests with pytest
& $venvPy -m pytest tests/run_all_tests.py -v --tb=short

$exitCode = $LASTEXITCODE

Pop-Location

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
} else {
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ❌ SOME TESTS FAILED - FIX ISSUES BEFORE PRODUCTION" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Red
}
Write-Host ""

exit $exitCode
