# Architecture Evidence

- Added `src/neos/workspace.py` as the deterministic composition layer for workspace state.
- Added `/workspace` service endpoints in `src/neos/service/routes.py`.
- Embedded the workspace payload into the existing `/projects/<project_id>` response.
- Added a Workspace Centre view to `apps/desktop/lib/app.dart`.
- Added direct workspace client methods to `apps/desktop/lib/neos_client.dart`.
- Workspace reads remain side-effect free and do not refresh Portfolio Intelligence implicitly.
- Project safety summaries now preserve `TRUE` / `FALSE` / `UNKNOWN` provenance.
- Dependency reconciliation now consumes persisted project-relationship evidence read-only.
