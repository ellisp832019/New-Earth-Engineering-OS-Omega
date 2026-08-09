# Firmware Architecture Evidence

The firmware pipeline lives in `src/neos/firmware.py` and is surfaced through `src/neos/core.py`, `src/neos/service/routes.py`, `src/neos/cli.py`, and the desktop Firmware Centre.

## Evidence-backed pipeline
1. discover firmware sources
2. parse build configuration and environments
3. derive environments, targets, and build variants
4. extract tasks, RTOS primitives, interrupts, timers, timing facts, buses, protocols, packets, memory findings, GPIO assignments, compatibility, findings, risks, gaps, and validations
5. materialize a deterministic `FirmwareSnapshot`
6. expose the snapshot via API, CLI, and desktop UI

## Actual observed evidence
- synthetic fixture: 3 environments, 3 targets, 1 task(s), 1 state machine(s)
- MicroGrow: 196 sources, 50 timing facts, 4 buses, compatibility `possible_mismatch`
