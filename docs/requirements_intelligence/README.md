# Requirements and Architecture Intelligence

This folder documents the v0.9 NEOS pass that adds deterministic requirements and architecture intelligence.

## Scope

- requirements are extracted deterministically from project text and documentation
- AI remains read-only and advisory
- canonical requirement creation still requires operator confirmation unless an explicit canonical source already exists
- architecture components, implementation evidence, tests, validation and releases are traced back to requirement candidates

## Entry points

- `python -m neos requirements intelligence build --project-id <id>`
- `python -m neos requirements intelligence inventory --project-id <id>`
- `python -m neos requirements intelligence trace <requirement_id>`
- Windows desktop `Requirements Intelligence` surface

## Evidence

Use `docs/release_evidence/neos-v0.9-requirements-architecture-intelligence/` for closeout commands, validation output, and review notes.
