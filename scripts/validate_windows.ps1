$ErrorActionPreference = "Stop"
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m ruff check src tests
& .\.venv\Scripts\python.exe -m neos doctor
Write-Host "Validation passed."
