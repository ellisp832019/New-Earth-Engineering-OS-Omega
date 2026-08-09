# Windows Productionisation v1.0.0 Acceptance

Observed on 2026-08-08.

## Acceptance checks

- Packaged Windows desktop launches from `dist\New-Earth-Engineering-OS-Windows-v1.0.0\NEOS.exe`.
- The desktop connects to the bundled backend and reports healthy service state.
- Closing the desktop window triggers an owned-backend shutdown path.
- The backend no longer remains running after the desktop exits.
- Backend-only smoke validates the service shutdown route directly.
- The Windows smoke harness captures both health and cleanup evidence.

## Result

All checks passed in this session.
