# CLI Evidence

The CLI now exposes registry and impact commands:

- `neos registry inventory`
- `neos registry show PROJECT_ID`
- `neos registry drift PROJECT_ID`
- `neos registry impact PROJECT_ID`

These commands are read-only and reuse the same registry model as the service API and desktop app.
