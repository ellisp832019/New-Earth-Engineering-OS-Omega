# Troubleshooting Windows

Observed on 2026-08-07.

## The app will not open

Check whether the release folder still contains:

- `NEOS.exe`
- `neos_engine.exe`

If either file is missing, the package is incomplete.

## The backend does not start

Inspect the log file:

- `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`

Then confirm that the service health endpoint responds on the configured localhost port.

## The app opens but shows a failure state

This usually means one of the following:

- the backend process could not launch
- the service never became healthy
- the port was already in use
- the package was built without the backend executable in the expected path

## The app seems stale

If the desktop shell attaches to an existing backend, it may reuse the current healthy service rather than start a new one. Restart the local backend if you want a fresh session.

## What to send for help

Include:

1. The log tail.
2. The package manifest.
3. The checksum file.
4. The exact steps you ran.
