# NEOS AI Engineering Partner Architecture

NEOS v0.6 adds a bounded AI layer on top of canonical engineering evidence.

## Data Flow

`Flutter Desktop -> NEOS Local Service API -> AI Gateway -> Provider Adapter -> Structured Response`

## Core Rules

- Python remains the canonical engine.
- Flutter stays a thin client.
- AI provider logic lives behind an explicit provider interface.
- The AI layer is read-only in v0.6.
- Evidence, citations, unknowns, and safety findings stay distinct.

## Implemented Surface

- AI settings persisted in SQLite.
- Provider abstraction with `mock`, `none`, and OpenAI-compatible HTTP support.
- Deterministic evidence retrieval and prompt-injection warnings.
- Project-scoped conversations, requests, and citations.
- Desktop AI workspace with conversation, question, response, and context panels.
