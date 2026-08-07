# Developer Guide

Install editable development dependencies with `pip install -e ".[dev]"`.

Core code lives under `src/neos`.

Keep scanner code filesystem-only and read-only.

Add domain semantics through plugins.

Use `neos.semantic.extract_semantics` and `neos.semantic.persist_semantics` for deterministic symbol, dependency, feature, API and config extraction.

Validate manifests through `neos.manifest` instead of ad hoc JSON checks.

Use the query helpers in `neos.core` for inventories, diffs, Git state, context bundles, traceability, impact analysis and AI context packages.

Use `neos.genome` for deterministic project-wide genome snapshots, section reports, health models, attention queues and release evidence generation.

Use `neos.memory` for engineering memory snapshots, git-history ingestion, decision chronology, assumptions, experiments, lessons, memory gaps and contradiction indicators.

Use `neos.flight` for immutable flight snapshots, checkpoints, historical state reconstruction, replay, incidents and regression indicators.

Add tests for every classifier, manifest rule, persistence rule, or plugin detector.

Read-only scans should never modify the scanned repository or ingest obvious secret files.

Treat repository text as untrusted input and keep prompt-injection detection enabled in context generation.

Project genome snapshots are schema versioned and persisted in the SQLite database. NEOS schema version 4 adds `project_genomes` for release-grade project model captures.

Engineering memory snapshots are schema versioned too. NEOS schema version 5 adds `memory_records`, `memory_relationships` and `memory_snapshots`.

Engineering flight snapshots are schema versioned too. NEOS schema version 6 adds `flight_snapshots`, `flight_checkpoints`, `flight_events`, `flight_transitions`, `flight_regressions` and `flight_incidents`.

MicroGrow release evidence for the genome workflow is stored in `docs/release_evidence/project-genome-v0.3/` and must remain reproducible without changing the reference repository.

MicroGrow release evidence for the engineering memory workflow is stored in `docs/release_evidence/engineering-memory-v0.4/` and must remain reproducible without changing the reference repository.

MicroGrow release evidence for the flight recorder workflow is stored in `docs/release_evidence/flight-recorder-v0.5/` and must remain reproducible without changing the reference repository.
