# Registry Intelligence

This folder documents the deterministic architecture registry layer added in NEOS v1.3.0.

The registry turns repository metadata, manifest data, git state, and explicit contract files into a stable project identity and contract spine.

## Ownership contract

Registry owns:

- contract envelope shaping
- contract validation and drift detection
- provenance reconciliation
- declared-versus-observed comparison
- registry projections and health views
- impact orchestration

Registry does not own:

- repository parsing
- semantic symbol extraction
- feature extraction
- requirement extraction
- hardware parsing
- firmware parsing
- engineering history reconstruction
- canonical portfolio dependency truth
- decision recommendation generation

## Included docs

- `PROJECT_IDENTITY.md`
- `CONTRACT_SPINE_V0_1.md`
- `CONTRACT_VALIDATION.md`
- `CONTRACT_DRIFT.md`
- `PROVENANCE_MODEL.md`

## What it is for

- identify a project deterministically
- expose the project contract surface in a stable shape
- detect drift between declared contracts and discovered evidence
- keep cross-project comparisons read-only
- supply the backend and desktop registry views with a single canonical explanation
