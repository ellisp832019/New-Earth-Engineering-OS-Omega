# Architecture Impact Analysis

NEOS v1.3.0 adds deterministic architecture impact analysis on top of the registry and contract spine.

## Purpose

Impact analysis helps answer:

- what else might change if this project changes
- where contract drift could create risk
- how one project relates to another project by capability, dependency, or identity

## Inputs

- registry snapshot
- discovered contracts
- project identity
- optional peer project snapshot
- optional peer repository path

## Output shape

- relationship score
- shared contract types
- delta summary
- drift indicators
- read-only comparison notes

## Operating rules

- no writes to the target or peer repository
- no network dependency
- no hidden mutation of the scanned repo
- no speculation presented as fact
