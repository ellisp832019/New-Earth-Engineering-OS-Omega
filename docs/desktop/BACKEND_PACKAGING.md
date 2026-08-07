# Backend Packaging

Observed on 2026-08-07.

## Build entry point

The backend release entry point is `scripts/backend_entry.py`.

That wrapper prepends the repository `src/` directory to `sys.path` and then calls `neos.cli:main`.

## Build command

`scripts/build_backend.ps1` produces a frozen Windows executable with PyInstaller.

The script:

- builds from the repository root
- includes `src/` on the module search path
- emits `build\backend\neos_engine.exe`
- can skip validation for local rebuilds

## Why the source path matters

The frozen backend must import the real `neos` package from `src/neos`, not the top-level repository shim.

The final backend build includes `--paths src` so PyInstaller resolves the packaged application code correctly.

## Release artifact

The packaged backend is copied into:

- the package root as `neos_engine.exe`
- `runtime\neos_engine.exe`

The duplicate copy keeps the runtime layout stable for the shell and for portable distribution.

## Validation

The backend build is expected to pass:

- pytest
- ruff
- mypy
- Windows packaging

The release bundle also records the backend executable hash and byte size in the manifest and checksum files.
