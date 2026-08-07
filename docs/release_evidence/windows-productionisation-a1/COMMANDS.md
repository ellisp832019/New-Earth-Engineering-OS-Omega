# Commands

Observed on 2026-08-07.

## Validation commands

- `python -m pytest -q`
- `python -m ruff check src tests`
- `python -m mypy src\neos`
- `flutter analyze`
- `flutter test`
- `flutter build windows --release`

## Packaging commands

- `powershell -ExecutionPolicy Bypass -File .\scripts\build_backend.ps1 -SkipValidation`
- `powershell -ExecutionPolicy Bypass -File .\scripts\package_windows.ps1 -SkipRepoCleanCheck`

## Notes

The packaged application launch smoke test was attempted, but the command was blocked by policy before the process result could be collected.
