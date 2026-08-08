# Windows Packaging

Observed on 2026-08-07.

## Packaging script

`scripts/package_windows.ps1` creates the portable Windows release bundle.

## Build sequence

The script performs these steps:

1. Run backend tests and static checks.
2. Run Flutter analyze, Flutter tests, and a Windows release build.
3. Build the frozen backend executable.
4. Assemble the portable package under `dist\New-Earth-Engineering-OS-Windows-v1.0.0`.
5. Copy the desktop shell and backend into the package.
6. Write release metadata files.
7. Optionally produce a zip archive.

## Package contents

The release folder contains:

- `NEOS.exe`
- `neos_engine.exe`
- `runtime\neos_engine.exe`
- `assets\`
- `data\`
- `BUILD_MANIFEST.json`
- `CHECKSUMS.json`
- `BUILD_METRICS.json`
- `README.txt`
- `VERSION`

## Metadata files

`BUILD_MANIFEST.json` records the version, git metadata, toolchain versions, schema version, API version, and release file hashes.

`CHECKSUMS.json` records the file checksums and sizes for the shipped executables.

`BUILD_METRICS.json` records the package root, total build time, and executable sizes.

## Release expectations

The package is intended to be portable. A user can unzip the folder and launch `NEOS.exe` without a separate install step.
