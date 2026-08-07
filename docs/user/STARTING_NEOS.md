# Starting NEOS

Observed on 2026-08-07.

## Normal start

Double-click `NEOS.exe`.

The desktop shell will try to attach to an existing local service first and then start the bundled backend if needed.

## Expected result

You should see the startup state transition to connected and then the main NEOS workspace.

## If the app is already running

If another NEOS backend is already healthy on the configured port, the shell should attach to it instead of starting a duplicate service.

## Log location

If startup is slow or fails, inspect:

- `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`
