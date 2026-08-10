# API Evidence

The HTTP service exposes read-only governance endpoints:

- `GET /governance`
- `GET /governance/status`
- `GET /governance/findings`
- `GET /governance/snapshot`
- `GET /governance/project/<project_id>`

Query parameters:

- `platform_core_root=<path>`
- `estate_root=<path>` repeated as needed

These endpoints do not modify Platform Core or the observed estate.
