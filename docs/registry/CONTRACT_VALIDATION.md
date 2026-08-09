# Contract Validation

Validation checks whether discovered evidence matches the expected contract spine.

## Validation focus

- contract type coverage
- shape consistency
- provenance presence
- manifest and git consistency
- identity conflicts

## Validation outcome model

- `ok` when the expected contract type is present and coherent
- `missing` when a contract type is not discovered
- `conflict` when multiple identity or contract candidates disagree
- `unknown` when the evidence is insufficient to decide

## Design posture

Validation is conservative. It should fail softly, explain the gap, and avoid asserting certainty where the repository does not provide it.
