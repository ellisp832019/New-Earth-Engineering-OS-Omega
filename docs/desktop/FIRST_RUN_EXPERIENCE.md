# First Run Experience

Observed on 2026-08-07.

## What happens on launch

When the user starts `NEOS.exe`, the shell:

1. Loads or creates the desktop settings file.
2. Probes the local backend port.
3. Attaches to an existing healthy backend if available.
4. Starts the bundled backend if needed.
5. Waits for the service to report healthy.
6. Opens the main shell once the backend is ready.

## User-visible states

The startup screen can show that the app is:

- checking the local service
- starting the local backend
- waiting for health
- connected
- degraded
- failed

## Settings file

The first launch creates `%LOCALAPPDATA%\New Earth Engineering OS\desktop-settings.json` if it does not already exist.

## Default behavior

The desktop shell defaults to:

- `127.0.0.1` for the local service host
- `8765` for the local service port
- automatic refresh enabled
- bundled backend preferred

## Logging

The startup log is written to:

- `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`

That file is the first place to inspect if the shell cannot attach to or launch the backend.
