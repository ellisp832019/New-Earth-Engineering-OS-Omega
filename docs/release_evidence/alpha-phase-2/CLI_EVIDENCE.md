# CLI Evidence

Observed on 2026-08-07.

## Commands and outputs

- `neos doctor` reported `database_schema: 3` and `migration_status: current`.
- `neos feature candidates microgrow-v1 --format json` returned `count: 13`.
- `neos api list microgrow-v1 --format json` returned `count: 33`.
- `neos config list microgrow-v1 --format json` returned `count: 1738`.
- `neos decisions microgrow-v1 --format json` returned `count: 7`.
- `neos trace api-034efa8788777f3cd8552d39 --depth 2 --format json` returned 4 edges and 3 discovered nodes.
- `neos impact api-034efa8788777f3cd8552d39 --depth 2 --format json` reported 1 direct impact and 3 indirect impacts.
- `neos why dec-53b22ae52b0c2cf3edd50e13 --format json` returned the ADR evidence and the rationale text for the HTTP REST decision.
- `neos feature confirm feat-f775897b978921d2a59877ac --format json` on a scratch database copy returned `status: validated` and changed `source` to `operator`.

## Representative outputs

- Feature candidates included `API`, `Climate Control`, `Climate Sensing`, `Device Discovery` and `Device Profiles`.
- API detection found route `/commands/nodes/{node_uid}/pending` in `software/microgrow_hub/app/routers/nodes.py`.
- Configuration detection found `project.latest_revalidation_id` in `project_control/canonical.json`.
- Decision memory captured `ADR-0001-api-style` with HTTP REST selected as the communication model.
