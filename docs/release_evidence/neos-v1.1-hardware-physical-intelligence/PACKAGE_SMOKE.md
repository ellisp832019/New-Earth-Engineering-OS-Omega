# Package Smoke

Observed command:

- `powershell -ExecutionPolicy Bypass -File .\\scripts\\smoke_windows_package.ps1`

Observed result:

- `NEOS.exe` launched from `dist\\New-Earth-Engineering-OS-Windows-v1.1.0`
- backend health succeeded
- service version reported `1.1.0`
- desktop closed cleanly
- owned backend exited cleanly
- no orphan backend remained

The package smoke passed against the final `v1.1.0` bundle.
