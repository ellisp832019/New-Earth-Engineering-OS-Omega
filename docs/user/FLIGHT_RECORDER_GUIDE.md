# Flight Recorder Guide

The flight recorder answers, "How did the project get here?"

## Common commands

```powershell
neos flight snapshot microgrow-v1 --json
neos flight snapshots microgrow-v1 --json
neos flight state microgrow-v1 --at latest --json
neos flight diff microgrow-v1 FROM_REF TO_REF --json
neos flight timeline microgrow-v1 --json
neos flight replay microgrow-v1 --from FROM_REF --to TO_REF --json
neos flight incidents microgrow-v1 --json
neos flight regressions microgrow-v1 --json
```

## Mental model

- Snapshot: one immutable engineering state
- Diff: what changed between two states
- Timeline: what happened over time
- Replay: ordered transitions between two states
- Incidents and regressions: evidence-backed warning signals
