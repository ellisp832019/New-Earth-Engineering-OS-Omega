# Hardware Centre Guide

NEOS v1.1.0 adds a read-only Hardware Centre for hardware and physical engineering evidence.

## Open Hardware Centre

1. Launch NEOS.
2. Select a project with hardware evidence in the left navigation.
3. Open `Hardware Centre`.

## What It Shows

- hardware summary counts
- board inventory
- component inventory
- pin mappings
- validation evidence
- risks and gaps
- raw hardware payload

## What It Does Not Do

- it does not edit hardware files
- it does not generate PCB layouts
- it does not validate electrical safety or manufacturing readiness
- it does not replace the project source of truth

## Empty State

If a project does not contain hardware artefacts, the Hardware Centre shows empty-state counts and the raw payload so you can see what was or was not discovered.

## Stale State

If hardware files change outside NEOS, rescan or refresh the project before treating the Hardware Centre as current.

## Notes

- Hardware discovery is deterministic and file-based.
- The feature is intentionally read-only.
- The desktop UI only reflects what the backend discovers from the project repository.
