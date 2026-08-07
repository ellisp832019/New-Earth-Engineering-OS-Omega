# Desktop Shutdown Diagnosis

Observed on 2026-08-07.

## Problem

The packaged Windows desktop could start successfully and connect to the bundled backend, but closing the GUI did not reliably stop the owned backend process.

## Root cause

The original close path allowed the native window to disappear before the backend shutdown completed, so the backend could outlive the desktop process.

## Fixes applied

- The Flutter bootstrap now requests a bounded shutdown of the owned backend before exit.
- The Windows runner now intercepts `WM_CLOSE` and routes it through a Dart exit request instead of destroying the window immediately.
- The backend now watches its `--owner-pid` and exits if the desktop disappears unexpectedly.
- The package smoke harness waits for backend cleanup before failing.

## Result

The desktop shutdown path is now deterministic enough for the packaged smoke to prove both window exit and backend cleanup.
