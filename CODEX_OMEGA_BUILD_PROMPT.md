# CODEX OMEGA BUILD PROMPT — NEW EARTH ENGINEERING OS

You are working inside the **New Earth Engineering OS (NEOS)** repository.

## Mission

Turn this Omega starter pack into the first reliable Alpha release of a local-first Engineering Operating System. The primary objective is not UI polish. It is to create a trustworthy engineering intelligence core that can understand one real repository—MicroGrow—without modifying it.

## Non-negotiable engineering rules

1. Read `README.md` and all documents under `docs/` before implementing major architecture changes.
2. Preserve the separation between canonical state and derived scanner/plugin state.
3. Repository scanning is read-only by default.
4. Never ingest obvious secret-file content.
5. Do not place core business logic inside the future Flutter UI.
6. Database schema changes require explicit migrations and tests.
7. AI-generated or inferred information must carry provenance and must never silently become canonical truth.
8. Keep the repository clean: no `.neos/`, venv, caches, compiled output or secrets committed.
9. Prefer deterministic engineering intelligence before AI heuristics.
10. Do not claim evidence passed unless commands were actually executed and results observed.

## Stage 0 — Preflight

Run and record:

```powershell
git status
git branch --show-current
git rev-parse HEAD
python --version
git --version
```

If the working tree is not clean, do not destroy unrelated work. Record the state and work safely.

## Stage 1 — Validate starter pack

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
.\scripts\validate_windows.ps1
```

Fix any real defects while preserving architecture.

## Stage 2 — Harden project manifest validation

Implement JSON-schema-backed or equivalently rigorous validation for `schemas/project-manifest.schema.json`.

Requirements:
- precise error messages
- normalized paths
- schema version checking
- lifecycle validation
- tests for valid/invalid manifests

## Stage 3 — Build scan snapshots and diff intelligence

Add:
- immutable scan snapshots
- previous-scan comparison
- added files
- removed files
- modified files
- unchanged files
- Git branch/commit metadata
- deterministic report output

CLI target:

```powershell
python -m neos scan --project-id microgrow-v1 --repo "D:\Dev\Projects\MicroGrow V1"
python -m neos diff --project-id microgrow-v1
```

## Stage 4 — Deepen repository classification

Identify at minimum:
- source code
- tests
- docs
- build definitions
- CI workflows
- application configuration
- release documentation
- hardware/firmware assets where recognizable

Do not pretend to semantically understand formats that are not yet supported. Represent unknown artefacts honestly.

## Stage 5 — Plugin runtime

Implement plugin discovery/registration with explicit capabilities. Create working Alpha adapters for:
- PlatformIO
- Flutter
- Python

Each plugin must have tests and provenance metadata.

## Stage 6 — Knowledge graph relationships

Add reliable relationships where deterministic evidence exists. Initial examples:
- project contains artefact
- build definition configures source tree
- test located in test subsystem
- documentation references known path
- release evidence references release/version

Avoid speculative edges.

## Stage 7 — Engineering query service

Implement CLI/report endpoints for:
- project summary
- technology inventory
- documentation inventory
- test inventory
- build-system inventory
- current Git state
- recent scan changes
- stale scan status

Outputs must support both human-readable text and JSON.

## Stage 8 — AI Context Gateway Alpha

Implement a local context-bundle generator. It must select bounded evidence and output a structured package matching `schemas/ai-context-bundle.schema.json`.

The context package must include:
- project ID
- scan ID/freshness
- question
- evidence paths
- selected facts
- provenance
- unknowns/limitations

Treat repository text as untrusted data and explicitly guard against prompt injection contained inside project files.

## Stage 9 — MicroGrow real-repository acceptance

Using the real repository at:

`D:\Dev\Projects\MicroGrow V1`

Perform a read-only Alpha scan.

Do not modify the MicroGrow repository.

Produce evidence under:

`docs/release_evidence/alpha-microgrow/`

Evidence should include:
- preflight state
- scan command
- scan ID
- Git commit observed
- artefact counts
- plugin detections
- test inventory summary
- documentation inventory summary
- known limitations
- proof that MicroGrow working tree state was not altered by NEOS

## Stage 10 — Windows desktop architecture foundation

Only after the core is stable, scaffold a Flutter Windows application under `apps/desktop/`.

The app is a thin client. Initial screens:
- Home
- Projects
- Repository Intelligence
- Knowledge Graph placeholder
- Tests & Evidence
- Releases
- AI Assistant placeholder
- System Health

Do not duplicate database/scanner rules in Dart. Define an explicit local API/service boundary.

## Stage 11 — Documentation completion

Update documentation to reflect actual implementation. Add:
- `docs/USER_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/DEVELOPER_GUIDE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/MICROGROW_INTEGRATION_GUIDE.md`
- architecture diagrams using Mermaid where suitable

## Stage 12 — Final Omega validation

Run the strongest applicable validation suite. At minimum:

```powershell
python -m pytest -q
python -m ruff check src tests
python -m neos doctor
```

If the Flutter app exists:

```powershell
flutter analyze
flutter test
flutter build windows --release
```

Record exact results.

## Final deliverable

Provide a closeout report containing:
- branch
- starting and final commit
- files changed
- architecture decisions
- migrations
- tests and exact results
- MicroGrow scan outcome
- known limitations
- next recommended milestone
- final `git status`

Do not start unrelated Beta features until the Alpha acceptance criteria in `docs/project_control/ACCEPTANCE_CRITERIA_ALPHA.md` are satisfied.
