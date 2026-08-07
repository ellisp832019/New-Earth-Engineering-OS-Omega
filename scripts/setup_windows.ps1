$ErrorActionPreference = "Stop"
Write-Host "Setting up New Earth Engineering OS..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python 3.11+ was not found on PATH." }
python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m neos doctor
Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
