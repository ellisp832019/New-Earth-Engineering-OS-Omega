param(
    [switch]$SkipRepoCleanCheck,
    [switch]$SkipZip
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$desktopRoot = Join-Path $root 'apps\desktop'
$releaseRoot = Join-Path $desktopRoot 'build\windows\x64\runner\Release'
$backendRoot = Join-Path $root 'build\backend'
$packageRoot = Join-Path $root 'dist\New-Earth-Engineering-OS-Windows-v1.1.0'
$packageRuntime = Join-Path $packageRoot 'runtime'
$packageData = Join-Path $packageRoot 'data'
$packageAssets = Join-Path $packageRoot 'assets'
$manifestPath = Join-Path $packageRoot 'BUILD_MANIFEST.json'
$checksumsPath = Join-Path $packageRoot 'CHECKSUMS.json'
$metricsPath = Join-Path $packageRoot 'BUILD_METRICS.json'
$zipPath = Join-Path $root 'dist\New-Earth-Engineering-OS-Windows-v1.1.0.zip'

function Get-JsonVersionInfo {
    param([string]$Command, [string[]]$Args)
    $output = & $Command @Args
    return $output
}

if (-not $SkipRepoCleanCheck) {
    $status = git -C $root status --short
    if ($status) {
        throw "Working tree is not clean. Use -SkipRepoCleanCheck for local packaging runs."
    }
}

$buildTimer = [System.Diagnostics.Stopwatch]::StartNew()

python -m pytest -q
python -m ruff check src tests
python -m mypy src\neos

Push-Location $desktopRoot
try {
    flutter analyze
    flutter test
    flutter build windows --release
}
finally {
    Pop-Location
}

& (Join-Path $root 'scripts\build_backend.ps1') -SkipValidation

if (Test-Path $packageRoot) {
    Remove-Item $packageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $packageRoot, $packageRuntime, $packageData, $packageAssets | Out-Null

Copy-Item -Path (Join-Path $releaseRoot '*') -Destination $packageRoot -Recurse -Force

$desktopExe = Join-Path $packageRoot 'desktop.exe'
$neosExe = Join-Path $packageRoot 'NEOS.exe'
if (Test-Path $desktopExe) {
    Copy-Item $desktopExe $neosExe -Force
    Remove-Item $desktopExe -Force
}

$backendExe = Join-Path $backendRoot 'neos_engine.exe'
if (-not (Test-Path $backendExe)) {
    throw "Backend executable not found at $backendExe"
}
Copy-Item $backendExe (Join-Path $packageRoot 'neos_engine.exe') -Force
Copy-Item $backendExe (Join-Path $packageRuntime 'neos_engine.exe') -Force

Set-Content -Path (Join-Path $packageRoot 'VERSION') -Value "1.1.0"
Set-Content -Path (Join-Path $packageRoot 'README.txt') -Value @"
New Earth Engineering OS

Launch NEOS.exe to start the engineering workstation.
The app will probe or launch the local backend automatically.
"@

$flutterVersion = flutter --version --machine | ConvertFrom-Json
$pythonVersion = python --version 2>&1
$gitSha = git -C $root rev-parse HEAD
$gitBranch = git -C $root branch --show-current
$timestamp = (Get-Date).ToUniversalTime().ToString('o')

$fileList = @(
    'NEOS.exe',
    'neos_engine.exe',
    'runtime\neos_engine.exe'
)

$hashes = foreach ($relative in $fileList) {
    $path = Join-Path $packageRoot $relative
    if (Test-Path $path) {
        $hash = Get-FileHash -Algorithm SHA256 $path
        [pscustomobject]@{
            file = $relative
            sha256 = $hash.Hash
            bytes = (Get-Item $path).Length
        }
    }
}

$manifest = [pscustomobject]@{
    neos_version = '1.1.0'
    git_sha = $gitSha
    git_branch = $gitBranch
    build_timestamp_utc = $timestamp
    flutter_version = $flutterVersion.frameworkVersion
    dart_version = $flutterVersion.dartSdkVersion
    python_version = ($pythonVersion -replace '^Python ', '')
    database_schema = 11
    api_version = 'v1'
    files = $hashes
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath
$hashes | ConvertTo-Json -Depth 6 | Set-Content -Path $checksumsPath

$metrics = [pscustomobject]@{
    package_root = $packageRoot
    build_seconds = [math]::Round($buildTimer.Elapsed.TotalSeconds, 2)
    neos_exe = (Get-Item $neosExe).Length
    backend_exe = (Get-Item (Join-Path $packageRoot 'neos_engine.exe')).Length
}
$metrics | ConvertTo-Json -Depth 4 | Set-Content -Path $metricsPath

if (-not $SkipZip) {
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $packageRoot '*') -DestinationPath $zipPath -Force
}

Write-Host "Packaged NEOS at $packageRoot"
