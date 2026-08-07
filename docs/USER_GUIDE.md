# User Guide

## 1. Install
Run `scripts/setup_windows.ps1` from PowerShell.

## 2. Register a project
`python -m neos init-project --manifest <manifest>`

## 3. Scan
`python -m neos scan --project-id <id> --repo <path>`

## 4. Inspect
`python -m neos project-summary --project-id <id>`

## 5. Back up
Run `scripts/backup_neos.ps1`.

## Understanding outputs
The current Alpha skeleton reports observed repository artefacts. Counts are derived facts, not manually curated feature truth. Future versions will add scan diff, feature relationships and evidence intelligence.
