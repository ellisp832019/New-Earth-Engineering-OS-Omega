# Test Results

Observed on 2026-08-08.

## Passed

- `python -m pytest -q`
- `python -m ruff check src tests`
- `python -m mypy src\neos`
- `flutter analyze`
- `flutter test`
- `flutter build windows --release`
- `scripts/build_backend.ps1 -SkipValidation`
- `scripts/package_windows.ps1 -SkipRepoCleanCheck`
- `scripts/smoke_windows_backend.ps1 -ShutdownAfterCheck`
- `scripts/smoke_windows_package.ps1`

## Package contents observed

- `NEOS.exe`
- `neos_engine.exe`
- `runtime\neos_engine.exe`
- `BUILD_MANIFEST.json`
- `CHECKSUMS.json`
- `BUILD_METRICS.json`
- `README.txt`
- `VERSION`
- `New-Earth-Engineering-OS-Windows-v1.0.0.zip`

## Notes

The final packaged desktop smoke completed successfully and verified that the owned backend exited after the GUI closed.
