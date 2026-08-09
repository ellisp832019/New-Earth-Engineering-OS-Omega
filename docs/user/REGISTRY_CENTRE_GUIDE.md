# Registry Centre Guide

NEOS v1.3.0 adds a read-only Registry Centre for project identity, contract spine, drift, and impact analysis.

## Open Registry Centre

1. Launch NEOS.
2. Select a project.
3. Open `Registry Centre`.

## What It Shows

- deterministic project identity
- discovered contract sources
- contract spine coverage
- drift signals
- cross-project impact analysis
- identity conflicts
- raw registry payload

## What It Does Not Do

- it does not edit repository files
- it does not auto-fix drift
- it does not replace the source project manifest
- it does not perform remote sync or cloud lookup

## Stale State

If repository files or git metadata change outside NEOS, refresh the project before treating the Registry Centre as current.
