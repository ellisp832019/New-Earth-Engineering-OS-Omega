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
python -m neos governance local-ai-runtime
```

Each command accepts:

- `--platform-core-root <path>`
- `--estate-root <path>` repeated as needed
- `--json`

The Local AI Runtime observation command also accepts:

- `--gaia-root <path>`
- `--runtime-root <path>`
- `--runtime-base-url <url>`
- `--gaia-base-url <url>`

### HTTP API

Read-only GET endpoints:

- `/governance`
- `/governance/status`
- `/governance/findings`
- `/governance/snapshot`
- `/governance/project/<project_id>`
- `/governance/local-ai-runtime`

Query parameters:

- `platform_core_root=<path>`
- `estate_root=<path>` repeated as needed

The Local AI Runtime observation endpoint also accepts:

- `gaia_root=<path>`
- `runtime_root=<path>`
- `runtime_base_url=<url>`
- `gaia_base_url=<url>`

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
