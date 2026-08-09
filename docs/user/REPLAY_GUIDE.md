# Replay Guide

Replay gives a deterministic sequence of engineering transitions between two snapshots.

## Example

```powershell
neos flight replay microgrow-v1 --from SNAPSHOT_A --to SNAPSHOT_B --json
```

## What it is for

- reviewing the sequence of changes
- understanding the order of events
- preparing a future visual replay UI

Replay is a data product, not an animation system.
