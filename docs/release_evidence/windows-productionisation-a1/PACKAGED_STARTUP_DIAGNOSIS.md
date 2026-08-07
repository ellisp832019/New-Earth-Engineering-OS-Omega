# Packaged Startup Diagnosis

Observed on 2026-08-07.

## Root cause

The packaged desktop was launching the backend on an ephemeral port and relying on stdout-driven discovery to recover the actual service URI.

The desktop settings and startup probe were still centered on the configured service port, which left the startup flow fragile and capable of spawning repeated backend attempts before the service handshake stabilized.

## Evidence observed

The desktop log showed:

- repeated `Checking local NEOS service at 127.0.0.1:8765`
- repeated `Starting local NEOS backend...`
- backend launches reporting `NEOS service listening on http://127.0.0.1:<random_port>`

That pattern is consistent with an unstable startup handshake rather than a simple hard-coded port typo.

## Repair

The desktop startup path now:

- uses a deterministic service port
- waits for the real health endpoint on that port
- treats early backend exit as a startup failure
- exposes the startup reason through the UI snapshot
