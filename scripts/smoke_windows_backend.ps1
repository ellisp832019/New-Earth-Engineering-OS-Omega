param(
    [string]$PackageRoot = (Join-Path $PSScriptRoot '..\dist\New-Earth-Engineering-OS-Windows-v1.3.0'),
    [string]$Port = '8765',
    [int]$TimeoutSeconds = 45,
    [switch]$ShutdownAfterCheck
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$packagePath = (Resolve-Path $PackageRoot).Path
$backendExe = Join-Path $packagePath 'neos_engine.exe'
if (-not (Test-Path $backendExe)) {
    throw "Backend executable not found: $backendExe"
}

$runRoot = Join-Path $env:TEMP ('neos-backend-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$dbPath = Join-Path $runRoot 'neos.db'
$stdoutPath = Join-Path $runRoot 'stdout.log'
$stderrPath = Join-Path $runRoot 'stderr.log'
$instanceId = [guid]::NewGuid().ToString('N')
$shutdownToken = [guid]::NewGuid().ToString('N')
$portNumber = [int]$Port

$args = @(
    'service', 'start',
    '--db', $dbPath,
    '--host', '127.0.0.1',
    '--port', $Port,
    '--instance-id', $instanceId,
    '--owner-pid', $PID.ToString(),
    '--shutdown-token', $shutdownToken
)

$process = Start-Process `
    -FilePath $backendExe `
    -ArgumentList $args `
    -WorkingDirectory $packagePath `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath

$deadline = (Get-Date).ToUniversalTime().AddSeconds($TimeoutSeconds)
$health = $null
while ((Get-Date).ToUniversalTime() -lt $deadline) {
    if ($process.HasExited) {
        break
    }
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
        if ($health.status -eq 'healthy') {
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

$listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $portNumber -State Listen -ErrorAction SilentlyContinue
$exitCode = $null
if ($process.HasExited) {
    $exitCode = $process.ExitCode
}

$summary = [pscustomobject]@{
    package_root = $packagePath
    backend_exe = $backendExe
    pid = $process.Id
    alive = -not $process.HasExited
    exit_code = $exitCode
    port = $portNumber
    listener = [bool]$listener
    db_path = $dbPath
    service_name = $health.service_name
    api_version = $health.api_version
    schema_version = $health.schema_version
    instance_id = $health.instance_id
    owner_pid = $health.owner_pid
}

if ($null -eq $health -or $health.status -ne 'healthy') {
    Write-Host '--- STDOUT ---'
    if (Test-Path $stdoutPath) {
        Get-Content $stdoutPath
    }
    Write-Host '--- STDERR ---'
    if (Test-Path $stderrPath) {
        Get-Content $stderrPath
    }
    exit 1
}

if ($ShutdownAfterCheck) {
    try {
        Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/shutdown" -ContentType 'application/json' -Body (@{ shutdown_token = $shutdownToken } | ConvertTo-Json) | Out-Null
    } catch {
        Write-Host "Shutdown request returned an expected transport error: $($_.Exception.Message)"
    }
    $shutdownDeadline = (Get-Date).ToUniversalTime().AddSeconds(15)
    while ((Get-Date).ToUniversalTime() -lt $shutdownDeadline -and -not $process.HasExited) {
        Start-Sleep -Milliseconds 250
    }
    if (-not $process.HasExited) {
        Write-Host '--- STDOUT ---'
        if (Test-Path $stdoutPath) {
            Get-Content $stdoutPath
        }
        Write-Host '--- STDERR ---'
        if (Test-Path $stderrPath) {
            Get-Content $stderrPath
        }
        Write-Host 'Backend did not exit after shutdown.'
        exit 1
    }
}

if (-not $process.HasExited -and -not $ShutdownAfterCheck) {
    Write-Host "Backend is still running on port $Port with PID $($process.Id)."
}

$summary = [pscustomobject]@{
    package_root = $packagePath
    backend_exe = $backendExe
    pid = $process.Id
    alive = -not $process.HasExited
    exit_code = if ($process.HasExited) { $process.ExitCode } else { $null }
    port = $portNumber
    listener = [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $portNumber -State Listen -ErrorAction SilentlyContinue)
    db_path = $dbPath
    service_name = $health.service_name
    api_version = $health.api_version
    schema_version = $health.schema_version
    instance_id = $health.instance_id
    owner_pid = $health.owner_pid
}

$summary | ConvertTo-Json -Depth 6

exit 0
