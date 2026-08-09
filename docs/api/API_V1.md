# API V1

NEOS v1.3.0 keeps the service API on `v1` and adds additive hardware and registry routes.

## Core Service

- `GET /health` - service and database status
- `GET /projects` - project registry
- `GET /projects/{project_id}` - project payload including hardware snapshot
- `GET /registry` - architecture registry inventory
- `GET /registry/{project_id}` - architecture registry snapshot
- `GET /registry/{project_id}/drift` - contract drift and provenance status
- `GET /registry/{project_id}/contracts` - discovered contract sources
- `GET /registry/{project_id}/identity` - deterministic project identity
- `GET /registry/{project_id}/impact` - architecture impact analysis
- `GET /projects/{project_id}/summary` - project summary
- `GET /projects/{project_id}/genome` - project genome
- `GET /projects/{project_id}/memory` - project memory
- `GET /projects/{project_id}/flight` - engineering flight snapshot

## Hardware Routes

- `GET /hardware/{project_id}` - full hardware snapshot
- `GET /hardware/{project_id}/boards` - board inventory
- `GET /hardware/{project_id}/components` - component inventory
- `GET /hardware/{project_id}/bom` - BOM summary and entries
- `GET /hardware/{project_id}/pins` - pin mappings
- `GET /hardware/{project_id}/validation` - validation evidence and status
- `GET /hardware/{project_id}/gaps` - discovered hardware gaps
- `GET /hardware/{project_id}/risks` - discovered hardware risks
- `GET /hardware/{project_id}/history` - hardware trace history view
- `GET /hardware/{project_id}/impact/{entity}` - trace impact for a given entity

## Response Notes

- Empty projects return empty lists and counts rather than errors.
- Unknown projects return `404 not_found`.
- The hardware routes are read-only.

## Compatibility Notes

The hardware and registry routes are additive and do not change the existing `v1` contract for the rest of the service.
