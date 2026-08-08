# Windows Build Evidence

Observed build commands:

- `flutter build windows --release`
- `powershell -ExecutionPolicy Bypass -File .\\scripts\\package_windows.ps1 -SkipRepoCleanCheck`

Observed build outputs:

- `apps\\desktop\\build\\windows\\x64\\runner\\Release\\desktop.exe`
- `build\\backend\\neos_engine.exe`
- `dist\\New-Earth-Engineering-OS-Windows-v1.1.0\\NEOS.exe`
- `dist\\New-Earth-Engineering-OS-Windows-v1.1.0\\neos_engine.exe`
- `dist\\New-Earth-Engineering-OS-Windows-v1.1.0.zip`

Final package metadata:

- NEOS version: `1.1.0`
- database schema: `11`
- API version: `v1`
- git SHA: `6a7a231e0dd3095342390d6de7585d5eb3d68de6`
- build timestamp UTC: `2026-08-08T11:37:09.5775049Z`
