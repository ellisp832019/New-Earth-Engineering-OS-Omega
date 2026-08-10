# ADR-0005: NEOS Governance Validator

## Status
Accepted

## Context
NEOS needs a deterministic way to compare the declared Platform Core architecture with the observed NEOS estate without modifying Platform Core itself.

The governance layer must remain read-only, preserve the `UNKNOWN` safety posture where evidence is incomplete, and keep NEOS platform authority separate from the workspace and dashboard surfaces.

## Decision
Add a dedicated NEOS governance validator that:

- Reads a configured Platform Core root or equivalent root path.
- Compares declared systems, repositories, dependencies, interfaces, and services against the observed NEOS estate.
- Produces deterministic findings and snapshots from read-only inputs.
- Exposes the same governance view through the Python API, CLI, and HTTP service.

## Consequences
- Platform Core stays canonical and untouched by the validator.
- Governance output is reproducible from the same declared and observed estate state.
- Workspace and portfolio reads remain read-only.
- No actuator, flashing, deployment, or second-contract authority is introduced.

## Notes
This ADR records the governance validator added for the NEOS architecture governance phase and is intentionally narrower than the broader workspace foundation work.
