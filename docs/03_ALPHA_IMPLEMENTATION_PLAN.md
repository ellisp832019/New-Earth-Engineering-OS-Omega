# Alpha Implementation Plan

## Alpha mission

Understand one repository completely enough to answer deterministic engineering questions and generate high-quality AI context.

## Workstream A — Canonical project model
- Project manifest schema
- Project registry database
- repository roots
- technology labels
- lifecycle and version metadata

## Workstream B — Repository intelligence
- deterministic scanner
- ignore rules
- file hashing
- artefact classification
- Git metadata capture
- scan snapshots
- scan diff

## Workstream C — Knowledge graph
- node contract
- edge contract
- provenance
- stable IDs
- basic relationships: project CONTAINS artefact, artefact OF_TYPE category, scan OBSERVED artefact

## Workstream D — Engineering queries
First deterministic queries:
- project summary
- artefact inventory
- technology inventory
- documentation inventory
- test inventory
- configuration inventory
- changed-since-last-scan

## Workstream E — AI context
Generate context bundles containing:
- question
- relevant nodes
- relevant edges
- evidence paths
- project metadata
- freshness timestamp
- explicit unknowns

## Workstream F — Validation
Acceptance criteria:
- no writes to scanned repo
- reproducible scans
- stable hashes
- no accidental ingestion of common secrets
- tests pass on Windows
- CLI errors are actionable
- scan of MicroGrow completes successfully

## Exit gate
Alpha cannot be declared complete solely because the UI looks good. It must pass the acceptance suite in `docs/08_TESTING_AND_VALIDATION.md`.
