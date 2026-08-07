# Service Health Evidence

Observed on 2026-08-07.

## Contract

The backend health endpoint returns:

- `service_name`
- `service_version`
- `api_version`
- `schema_version`
- `instance_id`
- `owner_pid`
- `started_at`
- `host`
- `port`

## Acceptance intent

The desktop should wait for `GET /health` to respond successfully on the exact service port chosen for the session.

## Repair impact

The desktop no longer depends on stdout port discovery as the only source of truth for startup readiness.
