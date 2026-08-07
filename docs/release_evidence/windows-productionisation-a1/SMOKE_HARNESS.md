# Smoke Harness

Observed on 2026-08-07.

## Added scripts

- `scripts/smoke_windows_backend.ps1`
- `scripts/smoke_windows_package.ps1`

## What they verify

- `smoke_windows_backend.ps1` starts the bundled backend, waits for `http://127.0.0.1:8765/health`, and can optionally post `/shutdown` and wait for process exit.
- `smoke_windows_package.ps1` launches `NEOS.exe`, waits for the window, requests a close, waits for desktop exit, and verifies that the owned backend no longer runs.

## Safety

- Both scripts avoid broad process cleanup.
- Both scripts only target the process trees they start.
- The package smoke waits briefly for the backend watchdog to finish cleanup before failing.
