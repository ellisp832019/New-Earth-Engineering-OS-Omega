# Developer Guide

Install editable development dependencies with `pip install -e ".[dev]"`.

Core code lives under `src/neos`.

Keep scanner code filesystem-only and read-only.

Add domain semantics through plugins.

Validate manifests through `neos.manifest` instead of ad hoc JSON checks.

Use the query helpers in `neos.core` for inventories, diffs, Git state, and context bundles.

Add tests for every classifier, manifest rule, persistence rule, or plugin detector.

Read-only scans should never modify the scanned repository or ingest obvious secret files.
