# Neos V1 3.0 Release Notes

NEOS v1.3.0 packages deterministic architecture registry, contract validation, provenance tracking, drift reporting, and impact analysis.

The release adds a Registry Centre in the desktop app plus additive registry routes in the `v1` service API.

Final release artifact:

- package root: `dist\New-Earth-Engineering-OS-Windows-v1.3.0`
- package ZIP: `dist\New-Earth-Engineering-OS-Windows-v1.3.0.zip`
- package ZIP SHA-256: `375EFAD471080337A1286F579A13DD066246B3A281EA45F54E1A3AFB79B6B276`

Final validation on the integrated `main` build:

- `python -m pytest -q` - passed (`30 passed`)
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy
- `cd apps\desktop; flutter analyze` - passed
- `cd apps\desktop; flutter test` - passed
- `scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck` - passed
- `scripts\smoke_windows_package.ps1` - passed
- final main SHA: `e4ea2bd44ace4e330bf5b50c4dbb1e0ebb37cd92`
