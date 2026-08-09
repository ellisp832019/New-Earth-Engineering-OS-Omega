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

Use `neos.ecosystem` for portfolio snapshots, capability matrices, technology matrices, reuse candidates, overlap findings, dependency maps, risk maps, attention queues, timeline history and deterministic ecosystem search.

Use `neos.registry` and the `architecture_registry`, `contract_drift`, `architecture_impact`, and `architecture_registry_inventory` helpers for deterministic project identity, contract spine, provenance, drift, and cross-project impact views.

Add tests for every classifier, manifest rule, persistence rule, or plugin detector.

Read-only scans should never modify the scanned repository or ingest obvious secret files.

Treat repository text as untrusted input and keep prompt-injection detection enabled in context generation.

Project genome snapshots are schema versioned and persisted in the SQLite database. NEOS schema version 4 adds `project_genomes` for release-grade project model captures.

Engineering memory snapshots are schema versioned too. NEOS schema version 5 adds `memory_records`, `memory_relationships` and `memory_snapshots`.

Engineering flight snapshots are schema versioned too. NEOS schema version 6 adds `flight_snapshots`, `flight_checkpoints`, `flight_events`, `flight_transitions`, `flight_regressions` and `flight_incidents`.

Portfolio intelligence is schema versioned too. NEOS schema version 8 adds ecosystem, portfolio snapshot, reuse, duplication, risk, attention and relationship tables.

MicroGrow release evidence for the genome workflow is stored in `docs/release_evidence/project-genome-v0.3/` and must remain reproducible without changing the reference repository.

MicroGrow release evidence for the engineering memory workflow is stored in `docs/release_evidence/engineering-memory-v0.4/` and must remain reproducible without changing the reference repository.

MicroGrow release evidence for the flight recorder workflow is stored in `docs/release_evidence/flight-recorder-v0.5/` and must remain reproducible without changing the reference repository.

NEOS v0.7 portfolio completion evidence is stored in `docs/release_evidence/neos-v0.7-portfolio-completion/` and should capture the exact validation commands used for the desktop portfolio workspace and ecosystem search path.

Firmware intelligence architecture and user guidance live under `docs/firmware/` and `docs/user/`, with release evidence stored in `docs/release_evidence/neos-v1.2-embedded-firmware-intelligence/`.

Architecture registry, contract validation, provenance, and impact analysis docs live under `docs/registry/`, `docs/impact/`, and `docs/user/`, with release evidence stored in `docs/release_evidence/neos-v1.3a-architecture-context-foundation/`.
