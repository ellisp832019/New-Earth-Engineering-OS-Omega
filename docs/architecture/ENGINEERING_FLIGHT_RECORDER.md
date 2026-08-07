# Engineering Flight Recorder

NEOS v0.5 adds an engineering flight recorder so the system can answer not only what exists now, but how the project arrived here.

## Design goals

- Deterministic
- Evidence-backed
- Immutable
- Rewindable
- Useful without an LLM

## Canonical state

A flight snapshot references the canonical NEOS state rather than duplicating everything:

- repository scan
- semantic graph
- project genome
- engineering memory
- features
- tests
- APIs
- configuration
- decisions
- risks
- maturity
- unknowns

## Core model

- `FlightSnapshot` records one immutable engineering state
- `FlightEvent` records a normalized change type
- `FlightTransition` compares two snapshots
- `FlightTimeline` merges snapshots, commits, decisions, experiments, milestones and regressions
- `FlightIncident` records evidence-backed regressions or failures
- `FlightCheckpoint` marks explicit engineering waypoints

## State hashing

Flight state is hashed with canonical JSON serialization so equivalent engineering state produces equivalent hashes.

## Important rule

The recorder is not a Git log viewer. Git is one evidence source among several.
