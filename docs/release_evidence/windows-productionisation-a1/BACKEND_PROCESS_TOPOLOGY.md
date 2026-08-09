# Backend Process Topology

Observed on 2026-08-07.

## Intended topology

The desktop owns one backend instance at a time.

The packaged session should consist of:

- `NEOS.exe`
- one intended `neos_engine.exe` service process

## Observed failure pattern

The failure logs showed repeated backend launches during startup.

That is not the desired steady-state topology and points to a startup handshake problem rather than a backend feature problem.

## Policy

The desktop must not spawn uncontrolled duplicate backend processes.

Retry should be single-flight and shutdown must only target the owned backend instance.
