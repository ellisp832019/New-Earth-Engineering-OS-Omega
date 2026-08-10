# Workspace Guide

The Workspace Centre gives you a deterministic, read-only view of a project from the NEOS backend.

## What It Shows

- project classification
- integration mode
- contract adapter state
- declared vs observed dependencies
- freshness and staleness
- provenance and evidence coverage
- release-readiness summary
- conservative safety boundary

## Open It In The Desktop App

1. Start the NEOS desktop app.
2. Select a registered project.
3. Open `Workspace` in the navigation.

The Workspace Centre reads the workspace section already embedded in the project payload, so it stays aligned with the service response for the selected project.

## CLI

Examples:

```powershell
neos workspace inventory
neos workspace show demo
neos workspace summary demo
neos workspace classification demo
neos workspace integration demo
neos workspace contracts demo
neos workspace dependencies demo
neos workspace freshness demo
neos workspace provenance demo
neos workspace release demo
neos workspace safety demo
```

Use `--include-non-first-party` on `inventory` when you want vendor, reference, or other non-first-party projects to appear in the list.

## Empty Or Degraded Repositories

The Workspace Centre still renders for repositories with little or no evidence.

- missing scan data becomes `NO_SCAN` or `LIVE`
- missing contract evidence becomes `DEGRADED`
- missing project registration becomes `UNKNOWN` or `NOT_READY`

That makes the workspace useful during early setup and for partially onboarded repositories.

