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

`neos version` prints the NEOS version.

Most read commands accept `--format text|json`.

Global option: `--db PATH` selects a different SQLite database.
