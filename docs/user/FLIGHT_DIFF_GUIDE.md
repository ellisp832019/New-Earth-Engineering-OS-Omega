# Flight Diff Guide

`neos flight diff` compares two historical engineering states.

## Example

```powershell
neos flight diff microgrow-v1 SNAPSHOT_A SNAPSHOT_B --json
```

## Output highlights

- added
- removed
- modified
- unchanged where useful

The diff spans files, symbols, dependencies, features, tests, APIs, configuration, decisions, risks, unknowns, maturity and health.
