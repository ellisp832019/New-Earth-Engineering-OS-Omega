# Creating Diagnostics

Observed on 2026-08-07.

## What to collect

For a Windows support bundle, collect:

- the desktop log
- the health response
- the package manifest
- the checksum file

## How to collect it

1. Open `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`.
2. Query `GET /health` from the local service.
3. Open `BUILD_MANIFEST.json`.
4. Open `CHECKSUMS.json`.

## Why this is enough

Those artefacts show:

- what version was shipped
- what hashes were packaged
- whether the shell started the backend
- whether the backend became healthy
- whether the local service ownership and shutdown data are present

## When to create diagnostics

Create diagnostics whenever the app fails to launch, cannot attach to the backend, or appears to show unexpected data after a Windows build.
