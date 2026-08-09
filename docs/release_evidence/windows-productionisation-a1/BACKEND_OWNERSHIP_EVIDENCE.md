# Backend Ownership Evidence

Observed on 2026-08-07.

## Ownership model

The packaged desktop starts the bundled backend with `--owner-pid` and `--shutdown-token`.

The service health response exposes:

- `owner_pid`
- `instance_id`
- `status`
- `service_name`
- `schema_version`

## Evidence collected

- Backend smoke reported a healthy service on `127.0.0.1:8765` before shutdown.
- The shutdown smoke completed with `alive: false` and `listener: false`.
- Packaged desktop smoke reported `owned_backend_still_running: false` after the GUI exited.

## Interpretation

The backend is now tied to desktop ownership instead of being left behind after the GUI closes.
