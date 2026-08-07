# Architecture Delta

Observed on 2026-08-07.

## Database

- Schema version advanced to `3`.
- New semantic tables store symbols, symbol locations, relationships, dependencies, features, feature evidence, engineering decisions, decision evidence, API endpoints, configuration keys and impact findings.
- Migration status now reports `current` from `neos doctor`.

## Core engine

- `scan_project` now performs deterministic semantic extraction after raw scan collection.
- `context_bundle` now emits v2-style facts, inferences, provenance, unknowns, limitations and warnings.
- `trace`, `impact`, `why`, `feature`, `decision`, `api` and `config` query helpers are available from `neos.core`.

## CLI

- The CLI now exposes semantic inventory and traceability commands alongside the original Alpha scan commands.
- `neos doctor` now reports the database schema version and migration status.

## Security

- Repository text is treated as untrusted input in context generation.
- The scan path remains read-only for the scanned repository.
