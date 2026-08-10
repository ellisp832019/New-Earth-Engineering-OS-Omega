# NEOS Governance Validator

The NEOS governance validator compares the declared Platform Core architecture with the observed NEOS estate in a read-only, deterministic way.

## What it checks

- Declared canonical repositories against observed NEOS projects.
- Repository identity mismatches in path and remote.
- Placeholder, planned, embedded, legacy, and reference classifications.
- Dependency evidence from Platform Core and NEOS snapshots.
- Contract visibility for declared interfaces.
- Duplicate first-party ownership of sensitive capabilities.
- Unregistered NEOS-style repositories in the configured estate roots.

## Surfaces

### CLI

```bash
python -m neos governance status
python -m neos governance findings
python -m neos governance project <project_id>
python -m neos governance report
python -m neos governance snapshot
```

Each command accepts:

- `--platform-core-root <path>`
- `--estate-root <path>` repeated as needed
- `--json`

### HTTP API

Read-only GET endpoints:

- `/governance`
- `/governance/status`
- `/governance/findings`
- `/governance/snapshot`
- `/governance/project/<project_id>`

Query parameters:

- `platform_core_root=<path>`
- `estate_root=<path>` repeated as needed

## Safety model

- Platform Core is never modified.
- The validator does not introduce actuator or deployment authority.
- Workspace reads do not write portfolio or intelligence state.
- Safety `UNKNOWN` is preserved whenever evidence is incomplete.

## Validation

The governance test suite exercises:

- core rule coverage
- deterministic snapshot generation
- CLI and HTTP governance surfaces
