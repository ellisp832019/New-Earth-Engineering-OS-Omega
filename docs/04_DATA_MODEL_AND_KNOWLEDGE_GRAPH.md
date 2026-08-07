# Data Model and Knowledge Graph

## Design objectives

The graph must be understandable, migration-friendly and provenance-first.

## Node types — initial
- project
- repository
- artefact
- source_file
- documentation
- test
- configuration
- build_definition
- release
- requirement
- decision
- feature
- hardware_component
- experiment
- evidence
- scan

## Edge examples
- PROJECT_CONTAINS_ARTEFACT
- ARTEFACT_REFERENCES_ARTEFACT
- TEST_VERIFIES_FEATURE
- IMPLEMENTATION_SATISFIES_REQUIREMENT
- DECISION_AFFECTS_COMPONENT
- RELEASE_INCLUDES_FEATURE
- EVIDENCE_SUPPORTS_CLAIM
- SCAN_OBSERVED_ARTEFACT

## Provenance

Every derived entity should eventually answer:
- where did this fact come from?
- when was it observed?
- which scanner/plugin produced it?
- what confidence is assigned?
- is the source still current?

## Stable identity

File artefacts use project ID + normalized repository-relative path as their initial stable identity. Semantic objects such as features and decisions should use persistent IDs stored in project-controlled metadata.

## Canonical versus derived state

Canonical state is human-owned or explicitly accepted. Derived state is scanner/plugin generated. Never silently convert a derived inference into canonical truth.

## Graph evolution

Use additive migrations. Avoid encoding UI layout assumptions into graph tables.

## Phase 2 semantic tables

Phase 2 adds deterministic semantic tables for symbols, symbol locations, relationships, dependencies, features, feature evidence, engineering decisions, decision evidence, API endpoints, configuration keys and impact findings.
