# Installing NEOS on Windows

Observed on 2026-08-07.

## What to download

Use the Windows release bundle from `dist\New-Earth-Engineering-OS-Windows-v1.1.0` or the equivalent zipped package.

## Install steps

1. Unzip the release folder to a local drive.
2. Keep `NEOS.exe` and `neos_engine.exe` in the same package directory.
3. Launch `NEOS.exe`.

## What the installer does not require

There is no separate database installer and no external backend service is required for the default local setup.

## First launch

The first launch creates the local settings file and starts or attaches to the backend automatically.

## Troubleshooting

If the app does not start, check the desktop log at `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log` and verify that the package still contains both executables.
