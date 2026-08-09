# Flight Transitions

A transition explains what changed between two snapshots.

## Transition content

- before
- after
- observed changes
- unchanged areas
- possible causes
- related decisions
- related commits
- related experiments
- related risks
- confidence
- unknowns

## Causal language

NEOS uses careful language:

- `observed_change`
- `associated_decision`
- `preceding_event`
- `possible_cause`
- `confirmed_cause`

The recorder should never invent causal certainty when the evidence only supports temporal proximity.
