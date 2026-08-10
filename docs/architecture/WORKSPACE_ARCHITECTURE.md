# Workspace Architecture

NEOS v1.4A adds a deterministic Workspace Centre as a composition layer over the existing registry, genome, memory, flight, hardware, firmware, and decision-intelligence systems.

## Goals

- classify projects deterministically
- expose a stable workspace API for desktop, CLI, and service clients
- separate declared, observed, and reconciled models
- keep first-party filtering explicit and conservative
- support empty or degraded repositories without failing the request

## Core Model

The workspace layer returns a single JSON object with these major sections:

- `identity`
- `summary`
- `classification`
- `integration`
- `contract`
- `repository`
- `declared`
- `observed`
- `reconciled`
- `dependencies`
- `requirements`
- `decisions`
- `memory`
- `flight`
- `hardware`
- `firmware`
- `release`
- `safety`
- `evidence`
- `drift`
- `impact`
- `freshness`
- `provenance`
- `attention`

## Deterministic Classification

The classification layer resolves a project into one of these states:

- `FIRST_PARTY_ACTIVE`
- `FIRST_PARTY_PLANNED`
- `FIRST_PARTY_INCOMPLETE`
- `EXPERIMENTAL`
- `LEGACY`
- `REFERENCE`
- `VENDOR`
- `FORK`
- `ARCHIVED`
- `UNKNOWN`

The resolver prefers explicit manifest signals first, then scan and registry evidence, and only falls back to conservative defaults when the repository provides no stronger signal.

Workspace reads are side-effect free. They do not implicitly refresh Portfolio Intelligence or create new portfolio snapshots, scans, registry rows, memory rows, flight rows, or contract mutations.

## Integration And Readiness

Workspace integration is summarized as:

- `CONTRACTED`
- `OBSERVED`
- `DEGRADED`

Workspace readiness is summarized as:

- `READY`
- `READY_WITH_GAPS`
- `NOT_READY`
- `UNKNOWN`

The service keeps the lower-level release-readiness model intact and adds a workspace-specific summary for the desktop and CLI.

## Contract Adapter

The Platform Core contract adapter exposes the registry contract spine in a stable shape and keeps the declared manifest, discovered contract sources, and contract drift visible together.

This does not grant deployment, flashing, or actuator authority. The adapter is read-only and presentation-focused.

## Freshness And Provenance

Freshness compares the live Git state to the latest stored scan when both are available.

Provenance records where the workspace answered from:

- manifest declarations
- registry evidence
- scan evidence
- persisted project-relationship evidence
- live Git state
- derived summaries

## Service API

The backend exposes:

- `GET /workspace`
- `GET /workspace/<project_id>`
- `GET /workspace/<project_id>/summary`
- `GET /workspace/<project_id>/classification`
- `GET /workspace/<project_id>/integration`
- `GET /workspace/<project_id>/contracts`
- `GET /workspace/<project_id>/dependencies`
- `GET /workspace/<project_id>/evidence`
- `GET /workspace/<project_id>/drift`
- `GET /workspace/<project_id>/impact`
- `GET /workspace/<project_id>/freshness`
- `GET /workspace/<project_id>/provenance`
- `GET /workspace/<project_id>/release`
- `GET /workspace/<project_id>/safety`

The existing project payload also embeds `workspace` so the desktop can render the centre without a separate fetch.

## Design Constraints

- no external repository access
- no actuator authority
- no firmware flashing authority
- no deployment authority
- no non-deterministic classification fallback
- project safety facts can be `TRUE`, `FALSE`, or `UNKNOWN`
- missing project safety evidence remains `UNKNOWN`
- NEOS platform authority restrictions stay separate from project safety declarations
- Workspace consumes persisted dependency evidence read-only rather than invoking Portfolio Intelligence during reads
