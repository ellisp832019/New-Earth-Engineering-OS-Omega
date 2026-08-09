# Windows Production Architecture

Observed on 2026-08-07.

## Overview

The Windows desktop release is a two-process system:

1. `NEOS.exe` is the Flutter desktop shell.
2. `neos_engine.exe` is the local Python backend service.

The shell is responsible for launching, attaching to, and shutting down the local service. The backend owns the SQLite database and all repository intelligence APIs.

## Runtime layout

The packaged Windows release uses this structure:

- `NEOS.exe`
- `neos_engine.exe`
- `runtime\neos_engine.exe`
- `data\`
- `assets\`
- `BUILD_MANIFEST.json`
- `CHECKSUMS.json`
- `BUILD_METRICS.json`
- `README.txt`
- `VERSION`

## Startup flow

The shell boots first, loads desktop settings from `%LOCALAPPDATA%\New Earth Engineering OS\desktop-settings.json`, and probes the configured localhost service.

If a healthy backend already exists on the configured port, the shell attaches to it.

If no healthy backend exists, the shell starts the bundled backend and waits for the health endpoint to report `is_neos = true`.

## Local service contract

The backend exposes:

- `GET /health`
- `GET /projects`
- `POST /shutdown`
- `POST /projects/register`
- `POST /projects/{project_id}/scan`
- project summary and semantic read routes under `/projects/{project_id}/...`

The health payload includes the service version, schema version, instance id, owner pid, and started-at timestamp so the shell can reason about lifecycle and ownership.

## Ownership model

When the shell launches the backend, it records:

- the backend process id
- the generated instance id
- the shutdown token
- the local service URI

That lets the shell request a controlled shutdown instead of forcing the process to terminate.

## Diagnostics

The shell writes logs to:

- `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`

The backend health endpoint, package manifest, and checksums provide the primary production diagnostics for local support and release verification.
