# Security Review

The architecture registry pass follows the existing NEOS security posture.

## Security posture

- local-first
- read-only against inspected repositories
- provenance-preserving
- conservative on inference
- no external synchronization required

## Residual risks

- stale local data can still mislead an operator
- incomplete contract documents can reduce analysis quality
