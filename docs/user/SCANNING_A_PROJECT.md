# Scanning a Project

Observed on 2026-08-07.

## Scan workflow

After registering a project, run a scan against the repository path.

## CLI workflow

`python -m neos scan --project-id ID --repo PATH`

## What the scan does

The scan is read-only. It captures repository observations and writes the raw scan data into the local database for later summaries, semantic extraction, memory snapshots, and flight records.

## Good practice

Always scan the exact repository revision you want to analyze so the stored results stay reproducible.
