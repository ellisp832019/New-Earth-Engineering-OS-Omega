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

`neos why ENTITY_ID --json` returns the same answer as JSON.

`neos memory build PROJECT_ID` builds and stores a deterministic engineering memory snapshot.

`neos memory show PROJECT_ID` shows the latest stored engineering memory snapshot.

`neos memory timeline PROJECT_ID` prints the deterministic engineering memory timeline.

`neos memory diff PROJECT_ID` compares the latest engineering memory snapshot to the previous one.

`neos memory decisions PROJECT_ID` prints decision memory records.

`neos memory assumptions PROJECT_ID` prints assumption memory records.

`neos memory experiments PROJECT_ID` prints experiment memory records.

`neos memory lessons PROJECT_ID` prints lesson memory records.

`neos memory milestones PROJECT_ID` prints milestone memory records.

`neos memory gaps PROJECT_ID` prints memory gap findings.

`neos memory contradictions PROJECT_ID` prints conservative contradiction indicators.

`neos memory trace ENTITY_ID` walks the memory relationship graph around an entity.

Flight recorder commands:

`neos flight checkpoint create PROJECT_ID` creates a deterministic engineering checkpoint from the current or referenced state.

`neos flight checkpoints PROJECT_ID` lists stored checkpoints.

`neos flight snapshot PROJECT_ID` creates a deterministic flight snapshot from canonical NEOS state.

`neos flight snapshots PROJECT_ID` lists stored flight snapshots.

`neos flight show SNAPSHOT_ID` shows a stored flight snapshot by id.

`neos flight state PROJECT_ID --at REF` reconstructs the historical engineering state at a snapshot or commit reference.

`neos flight diff PROJECT_ID FROM TO` compares two historical engineering states.

`neos flight timeline PROJECT_ID` merges snapshots, commits, decisions, experiments, milestones and regressions.

`neos flight replay PROJECT_ID --from REF --to REF` produces an ordered engineering transition sequence.

`neos flight incidents PROJECT_ID` lists regression-backed incidents.

`neos flight regressions PROJECT_ID` lists deterministic regression indicators.

All flight commands accept `--json`.

`neos genome build PROJECT_ID` builds and stores a deterministic project genome snapshot.

`neos genome show PROJECT_ID` shows the latest stored genome snapshot.

`neos genome summary PROJECT_ID` prints a compact project genome summary.

`neos genome export PROJECT_ID` exports the stored genome payload.

`neos genome diff PROJECT_ID` compares the latest genome snapshot to the previous one.

`neos genome domains PROJECT_ID` prints the domain map.

`neos genome risks PROJECT_ID` prints the risk genome.

`neos genome unknowns PROJECT_ID` prints the unknown surface map.

`neos genome health PROJECT_ID` prints the project health model.

`neos genome attention PROJECT_ID` prints the current attention queue.

`neos report project PROJECT_ID` renders the project genome report in markdown by default or JSON with `--json`.

Portfolio commands:

`neos ecosystem summary` builds the deterministic portfolio snapshot and prints the aggregate analysis.

`neos ecosystem projects` lists registered projects in portfolio order.

`neos ecosystem capabilities` prints the capability matrix for the selected portfolio scope.

`neos ecosystem technologies` prints the technology matrix for the selected portfolio scope.

`neos ecosystem reuse` prints reuse candidates across the selected portfolio scope.

`neos ecosystem duplication` prints overlap and duplication findings.

`neos ecosystem dependencies` prints cross-project dependency edges.

`neos ecosystem risks` prints portfolio risks.

`neos ecosystem unknowns` prints unresolved surface area.

`neos ecosystem attention` prints the portfolio attention queue.

`neos ecosystem timeline` prints portfolio snapshot history.

`neos ecosystem search QUERY` ranks portfolio entities by the deterministic ecosystem search index.

`neos ecosystem trace ENTITY_ID` traces a portfolio entity through the portfolio relationship graph.

`neos report ecosystem` renders the portfolio report in markdown by default or JSON with `--json`.

Registry and contract commands:

`neos registry inventory` prints the architecture registry inventory across registered projects.

`neos registry show PROJECT_ID` prints the architecture registry snapshot for one project.

`neos registry drift PROJECT_ID` prints contract drift, provenance gaps, and identity conflicts.

`neos registry impact PROJECT_ID` prints cross-project impact analysis for the selected project.

`neos registry impact PROJECT_ID --peer-project-id OTHER_ID` compares two registered projects directly.

`neos registry impact PROJECT_ID --peer-repo-path PATH` compares a project against an unregistered local repository path.

`neos version` prints the NEOS version.

Most read commands accept `--format text|json`.

Operator index:

- `neos memory build PROJECT_ID`
- `neos memory timeline PROJECT_ID`
- `neos memory diff PROJECT_ID`
- `neos flight snapshot PROJECT_ID`
- `neos flight state PROJECT_ID --at REF`
- `neos flight diff PROJECT_ID FROM TO`
- `neos flight timeline PROJECT_ID`
- `neos flight replay PROJECT_ID --from REF --to REF`

Global option: `--db PATH` selects a different SQLite database.
