# AI Context V2 Evidence

Observed on 2026-08-07.

## Schema

The AI context bundle schema now requires:

- `project_id`
- `scan_id`
- `generated_at`
- `question`
- `evidence_paths`
- `facts`
- `inferences`
- `provenance`
- `unknowns`
- `limitations`

Optional fields include:

- `scan_freshness`
- `selected_facts`
- `warnings`

## Sample bundle

A sample context bundle for the question `How should I change test coverage?` returned:

- 10 matched evidence paths
- 10 selected facts
- 2 inferences
- 0 unknowns
- 0 warnings

## Defense posture

Repository text is treated as untrusted input, and the context bundle logic scans for explicit instruction-like markers before assembling the final response.
