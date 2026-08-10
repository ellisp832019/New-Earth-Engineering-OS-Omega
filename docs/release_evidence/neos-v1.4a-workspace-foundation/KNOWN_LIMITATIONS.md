# Known Limitations

- The workspace layer is intentionally conservative and may classify sparse repositories as `UNKNOWN` or `NOT_READY`.
- The first-party filter depends on manifest and scan evidence, so very sparse projects may stay hidden unless `--include-non-first-party` is used.
- The workspace API is read-only by design.
- The desktop view currently renders the workspace payload as a diagnostic workspace rather than a polished narrative UI.

