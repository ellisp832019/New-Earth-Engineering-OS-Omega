# Adding a Project

Observed on 2026-08-07.

## What a project is

A project is a registered repository that NEOS can scan and analyze locally.

## Add flow

1. Create or locate a project manifest.
2. Register the project with NEOS.
3. Confirm the stored project id.

## CLI workflow

The current CLI entry point supports project registration with:

`python -m neos init-project --manifest PATH`

## What gets stored

Registration records the project metadata in the local SQLite database and normalizes the repository path so later scans can run deterministically.
