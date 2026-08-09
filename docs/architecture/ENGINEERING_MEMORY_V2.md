# Engineering Memory V2

Engineering Memory is NEOS's evidence-backed history layer.

It is not a chat log and not a free-form narrative. It is a structured model of engineering intent, change, validation and consequence.

## Canonical record types

- DecisionRecord
- AssumptionRecord
- ExperimentRecord
- ObservationRecord
- OutcomeRecord
- LessonRecord
- MilestoneRecord
- ChangeRecord

## Design rules

- Only ingest explicit, high-confidence evidence.
- Keep provenance on every record.
- Link memory snapshots to a project, scan and genome snapshot.
- Prefer deterministic extraction over inference.
- Distinguish facts, decisions, assumptions, experiments, observations, outcomes, lessons, milestones, changes and unknowns.

## Storage

NEOS schema version 5 adds:

- `memory_records`
- `memory_relationships`
- `memory_snapshots`

## Queries

- `neos memory build PROJECT_ID`
- `neos memory timeline PROJECT_ID`
- `neos memory diff PROJECT_ID`
- `neos memory trace ENTITY_ID`
- `neos why ENTITY_ID`

