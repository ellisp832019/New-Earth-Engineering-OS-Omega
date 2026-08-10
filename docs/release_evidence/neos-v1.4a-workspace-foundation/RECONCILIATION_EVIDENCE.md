# Reconciliation Evidence

The workspace layer reconciles declared and observed dependency evidence into:

- `VERIFIED`
- `PARTIALLY_VERIFIED`
- `DRIFTED`
- `STALE`
- `CONFLICT`
- `NOT_APPLICABLE`
- `UNKNOWN`

The dependency model is deterministic and derived from manifest declarations plus observed cross-project dependency evidence.

