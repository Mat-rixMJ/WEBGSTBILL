# Database Restore Script for WebGST
# Restores database from backup

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  WebGST Database Restore" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

if (!(Test-Path $BackupFile)) {
    Write-Host "✗ Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

# Extract backup
$TempDir = "$env:TEMP\webgst_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"
Write-Host "Extracting backup..." -ForegroundColor Yellow
Expand-Archive -Path $BackupFile -DestinationPath $TempDir

# Restore SQLite database
if (Test-Path "$TempDir\webgst.db") {
    Write-Host "Restoring SQLite database..." -ForegroundColor Yellow
    
    # Backup current database
    if (Test-Path "D:\WEBGST\backend\webgst.db") {
        $BackupCurrent = "D:\WEBGST\backend\webgst.db.backup_$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item "D:\WEBGST\backend\webgst.db" $BackupCurrent
        Write-Host "Current database backed up to: $BackupCurrent" -ForegroundColor Yellow
    }
    
    # Restore
    Copy-Item "$TempDir\webgst.db" "D:\WEBGST\backend\webgst.db" -Force
    Write-Host "✓ SQLite database restored" -ForegroundColor Green
}

# Restore PostgreSQL database (uncomment if using PostgreSQL)
# if (Test-Path "$TempDir\webgst_pg.dump") {
#     Write-Host "Restoring PostgreSQL database..." -ForegroundColor Yellow
#     $env:PGPASSWORD = "your_password"
#     & pg_restore -h localhost -U webgst_user -d webgst_db -c "$TempDir\webgst_pg.dump"
#     Write-Host "✓ PostgreSQL database restored" -ForegroundColor Green
# }

# Clean up
Remove-Item -Recurse -Force $TempDir

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Restore completed successfully!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
