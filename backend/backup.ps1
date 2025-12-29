# Automated Backup Script for WebGST
# Backs up database and application files
# Schedule with Windows Task Scheduler or cron

$BackupDir = "D:\WEBGST_Backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = "$BackupDir\backup_$Timestamp"

# Create backup directory
New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  WebGST Backup - $Timestamp" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Backup SQLite database (if using SQLite)
if (Test-Path "D:\WEBGST\backend\webgst.db") {
    Write-Host "Backing up SQLite database..." -ForegroundColor Yellow
    Copy-Item "D:\WEBGST\backend\webgst.db" "$BackupPath\webgst.db"
    Write-Host "✓ SQLite backup complete" -ForegroundColor Green
}

# Backup PostgreSQL database (if using PostgreSQL)
# Uncomment and configure these lines for PostgreSQL
# $env:PGPASSWORD = "your_password"
# Write-Host "Backing up PostgreSQL database..." -ForegroundColor Yellow
# & pg_dump -h localhost -U webgst_user -d webgst_db -F c -f "$BackupPath\webgst_pg.dump"
# Write-Host "✓ PostgreSQL backup complete" -ForegroundColor Green

# Backup .env file
Write-Host "Backing up configuration..." -ForegroundColor Yellow
Copy-Item "D:\WEBGST\backend\.env" "$BackupPath\.env"

# Backup invoice attachments (if any)
if (Test-Path "D:\WEBGST\backend\uploads") {
    Copy-Item -Recurse "D:\WEBGST\backend\uploads" "$BackupPath\uploads"
}

Write-Host "✓ Configuration backup complete" -ForegroundColor Green

# Compress backup
Write-Host "Compressing backup..." -ForegroundColor Yellow
Compress-Archive -Path "$BackupPath\*" -DestinationPath "$BackupPath.zip"
Remove-Item -Recurse -Force $BackupPath

Write-Host "✓ Backup compressed" -ForegroundColor Green

# Delete old backups (keep last 30 days)
Write-Host "Cleaning old backups..." -ForegroundColor Yellow
Get-ChildItem -Path $BackupDir -Filter "backup_*.zip" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

Write-Host "✓ Old backups cleaned" -ForegroundColor Green

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Backup completed successfully!" -ForegroundColor Green
Write-Host "Location: $BackupPath.zip" -ForegroundColor Cyan
Write-Host "Size: $((Get-Item "$BackupPath.zip").Length / 1MB) MB" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Optional: Upload to cloud storage
# Example: Upload to Azure Blob Storage, AWS S3, etc.
# Uncomment and configure for cloud backup
# Write-Host "Uploading to cloud storage..." -ForegroundColor Yellow
# az storage blob upload --account-name <account> --container-name backups --file "$BackupPath.zip" --name "backup_$Timestamp.zip"
