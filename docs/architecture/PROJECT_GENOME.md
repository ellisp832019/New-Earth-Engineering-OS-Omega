# Project Genome Architecture

The Project Genome is NEOS's deterministic, repository-wide engineering model.

It is built from scan data, semantic entities, feature maturity, documentation coverage, test evidence, engineering decisions, technology detection, dependency relationships and stored release evidence.

## Model Layers

- Identity and provenance
- Technology profile
- Domain map
- Architecture genome
- Feature maturity model
- Testing genome
- Documentation genome
- Risk and unknown surfaces
- Reuse candidates
- Project health and attention queue

## Data Flow

1. Scan a project into SQLite.
2. Extract semantic entities and relationships.
3. Aggregate the latest scan into a genome snapshot.
4. Persist the genome in `project_genomes`.
5. Render reports and release evidence from the stored snapshot.

## Determinism Rules

- Use the latest stored scan for the project.
- Derive genome values from repository evidence and scan state.
- Store the resulting snapshot with a schema version and source fingerprint.
- Keep the reference repository read-only during evidence generation.

## Release Output

The MicroGrow genome release bundle is stored at `docs/release_evidence/project-genome-v0.3/`.
