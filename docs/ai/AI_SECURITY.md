# AI Security

## Current Properties

- Local service only.
- No shell execution exposed to the AI layer.
- No repository mutation capabilities in v0.6.
- No secrets are written into evidence bundles or logs.

## Known Limitation

Real provider credentials must come from the environment or an external secret store. NEOS does not persist them in ordinary SQLite settings.
