# NEOS Architecture Governance v1 Evidence

This package records the deterministic NEOS governance validator added for the architecture governance phase.

## Evidence contents

- `ARCHITECTURE_EVIDENCE.md`
- `CLI_EVIDENCE.md`
- `API_EVIDENCE.md`
- `TEST_RESULTS.md`
- `KNOWN_LIMITATIONS.md`
- `evidence.json`

## Summary

The validator compares Platform Core declared architecture with the observed NEOS estate using read-only inputs only.
It is designed to keep Platform Core canonical, preserve `UNKNOWN` safety when evidence is incomplete, and avoid any actuator or deployment authority.

## Validation commands

```bash
python -m pytest -q tests/test_governance.py
python -m ruff check src tests
python -m mypy src\\neos
python -m neos doctor
```
