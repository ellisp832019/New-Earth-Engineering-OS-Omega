# Project Genome User Guide

The Project Genome gives you a single, deterministic view of a project's architecture, technology stack, feature maturity, testing posture, documentation posture, risks, unknowns and reuse opportunities.

## Common Commands

- `python -m neos genome build PROJECT_ID`
- `python -m neos genome show PROJECT_ID`
- `python -m neos genome summary PROJECT_ID`
- `python -m neos genome domains PROJECT_ID`
- `python -m neos genome risks PROJECT_ID`
- `python -m neos genome unknowns PROJECT_ID`
- `python -m neos genome health PROJECT_ID`
- `python -m neos genome attention PROJECT_ID`
- `python -m neos report project PROJECT_ID`

## What To Look For

- `summary` for a compact overview.
- `domains` for subsystem grouping.
- `risks` and `unknowns` for current gaps.
- `health` and `attention` for what needs work next.
- `report project` for a markdown readout you can archive or share.

## MicroGrow Evidence

The NEOS v0.3 MicroGrow genome release bundle lives in `docs/release_evidence/project-genome-v0.3/`.
