param(
    [switch]$SkipValidation
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$buildRoot = Join-Path $root 'build\backend'
$workRoot = Join-Path $root 'build\pyinstaller'
$entry = Join-Path $root 'scripts\backend_entry.py'

if (-not $SkipValidation) {
    python -m pytest -q
    python -m ruff check src tests
    python -m mypy src
}

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw 'PyInstaller is not available on PATH.'
}

New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

pyinstaller --noconfirm --clean --onefile --noconsole --name neos_engine --distpath $buildRoot --workpath $workRoot --specpath $workRoot --paths (Join-Path $root 'src') $entry
