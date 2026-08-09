# Project Identity Evidence

The registry identity model is derived from local evidence rather than from a mutable label.

## Observed identity sources

- manifest project metadata
- git remote metadata
- repository path normalization
- discovered contract files

## Expected behavior

- the same repository yields the same identity
- identity conflicts are surfaced explicitly
- missing evidence produces an unknown or partial state rather than a fabricated answer
