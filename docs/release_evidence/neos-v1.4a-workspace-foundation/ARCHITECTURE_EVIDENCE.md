# Architecture Evidence

- Added `src/neos/workspace.py` as the deterministic composition layer for workspace state.
- Added `/workspace` service endpoints in `src/neos/service/routes.py`.
- Embedded the workspace payload into the existing `/projects/<project_id>` response.
- Added a Workspace Centre view to `apps/desktop/lib/app.dart`.
- Added direct workspace client methods to `apps/desktop/lib/neos_client.dart`.

