# Neos V1 3.0 Release Notes

NEOS v1.3.0 packages deterministic architecture registry, contract validation, provenance tracking, drift reporting, and impact analysis.

The release adds a Registry Centre in the desktop app plus additive registry routes in the `v1` service API.

Final release artifact:

- package root: `dist\New-Earth-Engineering-OS-Windows-v1.3.0`
- package ZIP: `dist\New-Earth-Engineering-OS-Windows-v1.3.0.zip`
- package ZIP SHA-256: `29E0CE878B62D6A2CC8CE05B2BA569EF5F74A95001A8473CE7998E325298584F`

Final validation on the integrated `main` build:

- `python -m pytest -q` - passed (`30 passed`)
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy
- `cd apps\desktop; flutter analyze` - passed
- `cd apps\desktop; flutter test` - passed
- `scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck` - passed
- `scripts\smoke_windows_package.ps1` - passed
