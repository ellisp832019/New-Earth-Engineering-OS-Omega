# Test Results

## Python

- `python -m pytest -q` - 16 passed
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy, schema 7

## Flutter

- `flutter analyze` - passed
- `flutter test` - passed
- `flutter build windows --release` - passed

## Packaging

- `powershell -ExecutionPolicy Bypass -File .\scripts\package_windows.ps1 -SkipRepoCleanCheck` - passed
- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck` - passed
- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_package.ps1` - passed

## MicroGrow Proof

- branch: `planning/microgrow-v1-firmware-target-dependency-lock`
- HEAD: `0f9df32862bfb74f0acba8c4c1aa84d5a17c8363`
- status: clean
- diff: empty
