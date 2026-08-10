# Classification Evidence

Classification is deterministic and conservative.

Observed implementation states:

- explicit manifest and scan evidence can resolve first-party projects
- vendor and reference tags are filtered out of the default workspace inventory
- unregistered or empty repositories resolve to `UNKNOWN` rather than being forced into first-party status

Workspace inventory defaults to first-party projects only and can be expanded with `--include-non-first-party`.

