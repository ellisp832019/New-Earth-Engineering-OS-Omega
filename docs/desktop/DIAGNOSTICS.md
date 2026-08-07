# Diagnostics

Observed on 2026-08-07.

## Primary checks

The main diagnostics sources are:

- `GET /health`
- `BUILD_MANIFEST.json`
- `CHECKSUMS.json`
- `%LOCALAPPDATA%\New Earth Engineering OS\logs\neos-desktop.log`

## Service health

The health response reports:

- service version
- schema version
- instance id
- owner pid
- started-at timestamp
- readiness and service status fields

## Desktop log

The desktop log shows:

- whether the shell found an existing backend
- whether it launched the bundled backend
- whether health checks succeeded
- whether shutdown completed cleanly
- any connection or process-launch failures

## Support workflow

If a release looks unhealthy, collect these items in order:

1. The desktop log tail.
2. The service health payload.
3. The package manifest.
4. The checksum file.

Those four artefacts are enough to separate launch problems from packaging problems and backend runtime failures.
