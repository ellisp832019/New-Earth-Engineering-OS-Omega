# Project Identity

NEOS derives a stable project identity from repository-local evidence instead of from mutable display names.

## Identity inputs

- manifest project id and title, when available
- git remote and commit metadata
- repository path normalization
- discovered project contract documents

## Identity output

The identity record is intended to answer:

- what project this is
- how the project is named in local evidence
- whether multiple identity candidates conflict
- whether the current repository is consistent with its own declared metadata

## Design rules

- deterministic
- read-only
- derived from local evidence only
- tolerant of missing data
- explicit about conflicts instead of silently choosing a winner
