# CLI Reference

`neos doctor` validates the runtime and schema state.

`neos init-project --manifest PATH` validates a manifest, normalizes repository paths, and registers or updates a project.

`neos scan --project-id ID --repo PATH` performs a read-only filesystem scan, captures Git metadata, and persists immutable observations.

`neos project-summary --project-id ID` prints observed project inventory.

`neos technology-inventory --project-id ID` lists detected technologies and plugin signals.

`neos documentation-inventory --project-id ID` lists documentation artefacts.

`neos test-inventory --project-id ID` lists test artefacts.

`neos build-inventory --project-id ID` lists build and CI artefacts.

`neos scan-diff --project-id ID` compares the latest two raw scans.

`neos git-state --project-id ID` reports current Git state for the project repo.

`neos stale-scan-status --project-id ID` reports whether the latest scan is still fresh.

`neos context-bundle --project-id ID --question "..."` generates a bounded AI context package with provenance.

Semantic repository intelligence commands:

`neos symbols --project-id ID` lists extracted symbols.

`neos symbol show SYMBOL_ID` shows a single symbol and its primary location.

`neos feature list PROJECT_ID` lists semantic feature candidates.

`neos feature candidates PROJECT_ID` lists heuristic feature candidates.

`neos feature show FEATURE_ID` shows a feature and its evidence rows.

`neos feature confirm FEATURE_ID` converts a candidate to operator-validated state.

`neos decisions PROJECT_ID` lists engineering decisions for a project.

`neos decision show DECISION_ID` shows a single decision and its evidence.

`neos api list PROJECT_ID` lists detected API endpoints.

`neos config list PROJECT_ID` lists detected configuration keys.

`neos dependencies ENTITY_ID` lists direct dependency relationships.

`neos trace ENTITY_ID` walks the relationship graph around an entity.

`neos impact ENTITY_ID` summarizes likely impact areas.

`neos why ENTITY_ID` shows supporting evidence and related decisions.

`neos version` prints the NEOS version.

Most read commands accept `--format text|json`.

Global option: `--db PATH` selects a different SQLite database.
