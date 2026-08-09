# Backend Lifecycle

Observed on 2026-08-07.

## States

The desktop manager currently tracks these lifecycle states:

- `notStarted`
- `starting`
- `waitingForHealth`
- `connected`
- `degraded`
- `failed`
- `stopping`
- `stopped`

## Normal startup

1. Load desktop settings.
2. Probe the configured localhost service.
3. Attach to an existing healthy backend if one is already running.
4. Otherwise launch the bundled backend.
5. Poll `GET /health` until the service is healthy.
6. Mark the shell as connected and persist the resolved port.

## Shutdown

If the shell owns the backend, it sends `POST /shutdown` with the stored shutdown token.

If the controlled shutdown does not complete in time, the manager escalates to a process signal.

## Failure handling

If the backend cannot be launched or does not become healthy within the timeout window, the shell moves into `failed` and surfaces the error message in the startup UI.

If an attached backend stops responding, the shell can retry the bootstrap flow and reconnect to a healthy service.

## Ownership fields

The backend health response and the shell snapshot both carry:

- `instance_id`
- `owner_pid`
- `started_at`
- `service_version`

Those fields make it possible to distinguish an attached service from one started by the current shell session.
