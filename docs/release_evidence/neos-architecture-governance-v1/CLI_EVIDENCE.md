# CLI Evidence

The governance validator is exposed through the NEOS CLI:

- `python -m neos governance status`
- `python -m neos governance findings`
- `python -m neos governance project <project_id>`
- `python -m neos governance report`
- `python -m neos governance snapshot`

Supported options:

- `--platform-core-root`
- `--estate-root` repeated as needed
- `--json`

The CLI is read-only and delegates to the governance report generator.
