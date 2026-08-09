# Backend Smoke

Observed command:

- `powershell -ExecutionPolicy Bypass -File .\\scripts\\smoke_windows_backend.ps1 -ShutdownAfterCheck`

Observed result:

- backend launched from `dist\\New-Earth-Engineering-OS-Windows-v1.1.0`
- localhost health succeeded
- service identity reported `NEOS Local Service`
- product version reported `1.1.0`
- schema version reported `11`
- shutdown token worked
- backend exited cleanly
- no owned backend remained running

The script returned the expected transport-level disconnect after shutdown request, which is normal for this harness.
