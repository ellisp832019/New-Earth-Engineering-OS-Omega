# Security Review

Reviewed areas:

- hardware file discovery
- BOM and pin-map parsing
- datasheet reference parsing
- backend route exposure
- CLI entry points
- package contents

Observed posture:

- discovery is local and deterministic
- file paths are normalized through the repository root
- hardware routes are read-only
- the package does not depend on external hardware services
- the desktop client is a thin backend consumer

Residual risks:

- malformed hardware files can still produce partial or empty snapshots
- very large hardware artefacts may require future size or complexity limits
- unsupported file formats may be ignored rather than fully parsed

No high-severity security defect was identified in this pass.
