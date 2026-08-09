# Process Cleanup Evidence

Observed on 2026-08-07.

## What was checked

- The desktop smoke harness closed the GUI window.
- The harness then waited for the backend owned by that desktop PID to exit.
- The final check confirmed no matching `neos_engine.exe` process remained.

## Verified outcome

- `desktop_exited: true`
- `owned_backend_still_running: false`

## Interpretation

The cleanup path no longer leaves a stray backend process after the desktop closes.
