# New Earth Engineering OS (NEOS)

> Omega-standard starter repository for a local-first engineering intelligence platform.

NEOS is designed to become the intelligence layer above engineering repositories, documentation, tests, releases, hardware evidence and future AI agents. The first target is intentionally narrow: **understand one repository completely**, then scale to a multi-project engineering operating system.

## What this pack contains

- Foundational vision and system architecture
- Product requirements and acceptance criteria
- Governance, security, privacy and local-first rules
- Project manifest and knowledge graph schemas
- A working Python CLI/core skeleton using SQLite
- Repository scanning and project indexing
- Basic knowledge graph node/edge persistence
- Semantic repository intelligence for symbols, features, API routes, config keys and decisions
- Deterministic project genome snapshots, reports and release evidence packs
- Engineering memory snapshots, timeline queries and rationale tracing
- Engineering flight recorder snapshots, rewindable state diffs and replayable timelines
- Portfolio workspace for cross-project capability, technology, reuse, overlap, risk and search views
- Deterministic ecosystem search across the registered project portfolio
- Deterministic decision intelligence for next actions, release readiness, reuse, architecture and scenarios
- Deterministic requirements and architecture intelligence with trace, gaps, verification and operator review
- Plugin SDK contract and example plugin
- Sample MicroGrow project manifest
- Tests and validation scripts
- Windows setup and run scripts
- CI workflow
- ADRs, threat model, risk register and release process
- Engineering OS desktop application specification
- Alpha → Beta → v1.0 roadmap
- Codex implementation/handoff prompt
- Phase 2 evidence packs for semantic intelligence and read-only MicroGrow acceptance

## Omega Alpha objective

**NEOS Alpha succeeds when it can inspect one real repository and produce a trustworthy, queryable engineering model of that repository.**

## Quick start — Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
.\.venv\Scripts\Activate.ps1
python -m neos doctor
python -m neos init-project --manifest examples\microgrow\project.neos.json
python -m neos scan --project-id microgrow-v1 --repo "D:\Dev\Projects\MicroGrow V1"
python -m neos project-summary --project-id microgrow-v1
python -m neos genome build microgrow-v1 --json
python -m neos report project microgrow-v1 --json
python -m neos memory build microgrow-v1 --json
python -m neos memory timeline microgrow-v1 --json
python -m neos flight snapshot microgrow-v1 --json
python -m neos flight timeline microgrow-v1 --json
python -m neos ecosystem summary --json
python -m neos ecosystem search "shared capability" --json
```

## Quick start — cross-platform

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m neos doctor
python -m neos init-project --manifest examples/microgrow/project.neos.json
python -m neos scan --project-id microgrow-v1 --repo /path/to/repo
python -m neos project-summary --project-id microgrow-v1
python -m neos genome build microgrow-v1 --json
python -m neos report project microgrow-v1 --json
python -m neos memory build microgrow-v1 --json
python -m neos memory timeline microgrow-v1 --json
python -m neos flight snapshot microgrow-v1 --json
python -m neos flight timeline microgrow-v1 --json
python -m neos ecosystem summary --json
python -m neos ecosystem search "shared capability" --json
```

## Recommended reading order

1. `docs/00_START_HERE.md`
2. `docs/01_VISION_AND_PRODUCT_STRATEGY.md`
3. `docs/02_SYSTEM_ARCHITECTURE.md`
4. `docs/03_ALPHA_IMPLEMENTATION_PLAN.md`
5. `docs/04_DATA_MODEL_AND_KNOWLEDGE_GRAPH.md`
6. `docs/05_PLUGIN_ARCHITECTURE.md`
7. `docs/06_DESKTOP_APP_SPECIFICATION.md`
8. `docs/07_SECURITY_AND_LOCAL_FIRST.md`
9. `docs/08_TESTING_AND_VALIDATION.md`
10. `docs/09_ROADMAP.md`
11. `CODEX_OMEGA_BUILD_PROMPT.md`

The NEOS v0.3 MicroGrow genome evidence bundle lives in `docs/release_evidence/project-genome-v0.3/`.

The NEOS v0.4 MicroGrow engineering memory evidence bundle lives in `docs/release_evidence/engineering-memory-v0.4/`.

The NEOS v0.5 MicroGrow flight-recorder evidence bundle lives in `docs/release_evidence/flight-recorder-v0.5/`.

The NEOS v0.7 portfolio-intelligence completion evidence bundle lives in `docs/release_evidence/neos-v0.7-portfolio-completion/`.

The NEOS v0.8 engineering decision-intelligence evidence bundle lives in `docs/release_evidence/neos-v0.8-decision-intelligence/`.

The NEOS v0.9 requirements-and-architecture-intelligence evidence bundle lives in `docs/release_evidence/neos-v0.9-requirements-architecture-intelligence/`.

## Operator index

- `neos memory build PROJECT_ID` builds a deterministic engineering memory snapshot.
- `neos memory timeline PROJECT_ID` shows the memory timeline.
- `neos memory diff PROJECT_ID` compares the latest two memory snapshots.
- `neos flight snapshot PROJECT_ID` stores a deterministic flight snapshot.
- `neos flight state PROJECT_ID --at REF` reconstructs state at a snapshot or commit reference.
- `neos flight diff PROJECT_ID FROM TO` compares two historical engineering states.
- `neos flight timeline PROJECT_ID` merges snapshots, commits, decisions, experiments, milestones and regressions.
- `neos flight replay PROJECT_ID --from REF --to REF` produces an ordered transition sequence.

## Repository status

This package is a **foundation**, not a finished NEOS product. The included core is deliberately small, testable and auditable so the platform can grow without becoming a monolith.
