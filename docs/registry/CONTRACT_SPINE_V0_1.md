# Contract Spine v0.1

NEOS v1.3a standardizes a small contract spine so projects can be compared without inventing ad hoc categories.

## Contract types

- `PROJECT_CONTRACT`
- `CAPABILITIES`
- `DEPENDENCIES`
- `SAFETY_BOUNDARY`
- `RELEASE_STATE`

## Why these five

- `PROJECT_CONTRACT` anchors the project identity and the overall contract envelope.
- `CAPABILITIES` describes the project-facing capability claims.
- `DEPENDENCIES` captures declared runtime, build, or integration dependencies.
- `SAFETY_BOUNDARY` records constraints, operator boundaries, and non-goals.
- `RELEASE_STATE` records release posture, maturity, or publication state.

## Rules

- the spine is deterministic
- the spine is additive, not invasive
- missing contracts are represented as missing evidence, not fabricated content
- contract sources are treated as read-only artifacts
