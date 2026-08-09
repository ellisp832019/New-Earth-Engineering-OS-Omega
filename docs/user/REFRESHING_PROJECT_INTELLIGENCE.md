# Refreshing Project Intelligence

Observed on 2026-08-07.

## When to refresh

Refresh project intelligence after repository changes, a new commit, or any documentation or configuration update that should be reflected in the project profile.

## Refresh options

The main refresh actions are:

- rescan the project
- rebuild the project summary
- refresh the genome snapshot
- refresh the engineering memory snapshot
- refresh the flight recorder snapshot

## CLI examples

`python -m neos scan --project-id ID --repo PATH`

`python -m neos project-summary --project-id ID`

`python -m neos genome build ID`

`python -m neos memory build ID`

`python -m neos flight snapshot ID`

## Result

A refresh updates the local SQLite-backed intelligence so the desktop shell and API reflect the latest observed repository state.
