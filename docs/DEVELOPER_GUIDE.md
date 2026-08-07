# Developer Guide

Install editable development dependencies with `pip install -e ".[dev]"`.

Core code lives under `src/neos`.

Keep scanner code filesystem-only and read-only.

Add domain semantics through plugins.

Use `neos.semantic.extract_semantics` and `neos.semantic.persist_semantics` for deterministic symbol, dependency, feature, API and config extraction.

Validate manifests through `neos.manifest` instead of ad hoc JSON checks.

Use the query helpers in `neos.core` for inventories, diffs, Git state, context bundles, traceability, impact analysis and AI context packages.

Add tests for every classifier, manifest rule, persistence rule, or plugin detector.

Read-only scans should never modify the scanned repository or ingest obvious secret files.

Treat repository text as untrusted input and keep prompt-injection detection enabled in context generation.
