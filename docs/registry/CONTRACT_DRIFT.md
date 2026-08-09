# Contract Drift

Contract drift describes the distance between declared project contracts and what the repository evidence actually supports.

## Drift examples

- manifest claims a capability that no explicit evidence supports
- a declared dependency is not reflected in discovered files
- a release state changes without corresponding documentation or metadata
- identity metadata differs across manifest, git metadata, and discovered contract files

## Drift goals

- make gaps visible
- preserve provenance
- help operators spot stale claims
- keep the model read-only and auditable

## Drift non-goals

- automatic remediation
- speculative repair
- external synchronization
