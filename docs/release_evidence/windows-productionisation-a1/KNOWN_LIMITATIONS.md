# Known Limitations

Observed on 2026-08-07.

## Current state

The code path now uses a fixed localhost service port and a bounded shutdown path.

## Operational note

The packaged smoke still depends on a local Windows GUI session and localhost networking.

The harness proves process cleanup and service health, but it does not perform pixel-level UI assertions.
