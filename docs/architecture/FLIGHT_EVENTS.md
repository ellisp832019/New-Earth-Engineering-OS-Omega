# Flight Events

Flight events are normalized labels for observed engineering changes.

## Event families

- commit
- feature_added
- feature_removed
- feature_status_changed
- symbol_added
- symbol_removed
- dependency_added
- dependency_removed
- api_added
- api_removed
- config_changed
- test_added
- test_removed
- decision_added
- decision_superseded
- assumption_invalidated
- experiment_completed
- risk_added
- risk_resolved
- maturity_changed
- release_created
- milestone_reached

## Event rules

- Events must cite source and target snapshots
- Events should carry evidence paths or record ids
- Confidence should reflect evidence quality
- Events can be produced deterministically from snapshot diffs
