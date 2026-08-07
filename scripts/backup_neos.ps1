$ErrorActionPreference = "Stop"
if (-not (Test-Path ".neos\neos.db")) { throw "No .neos\neos.db database found." }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path "backups" | Out-Null
Copy-Item ".neos\neos.db" "backups\neos-$stamp.db"
Write-Host "Backup created: backups\neos-$stamp.db"
