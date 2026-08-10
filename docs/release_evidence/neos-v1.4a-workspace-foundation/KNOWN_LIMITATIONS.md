# Known Limitations

- The workspace layer is intentionally conservative and may classify sparse repositories as `UNKNOWN` or `NOT_READY`.
- The first-party filter depends on manifest and scan evidence, so very sparse projects may stay hidden unless `--include-non-first-party` is used.
- The workspace API is read-only by design.
- Dependency provenance depends on existing persisted project-relationship rows; if no prior evidence exists, dependency reconciliation may remain `UNKNOWN`.
- Project safety evidence stays `UNKNOWN` until an explicit contract exists, which is intentional.
- The desktop view currently renders the workspace payload as a diagnostic workspace rather than a polished narrative UI.
