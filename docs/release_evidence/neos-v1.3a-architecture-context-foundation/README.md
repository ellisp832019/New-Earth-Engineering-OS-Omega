# NEOS v1.3.0 Architecture Context Foundation Evidence

This bundle records the closeout evidence for the architecture registry, contract spine, provenance, and impact analysis pass that underpins the NEOS v1.3.0 release.

## Observed validation

- `python -m pytest -q`
- `python -m ruff check src tests`
- `python -m mypy src\neos`
- `python -m neos doctor`
- `cd apps\desktop; flutter analyze`
- `cd apps\desktop; flutter test`

## Scope

- deterministic project identity
- contract spine v0.1
- contract validation and drift
- registry inventory and project snapshots
- cross-project impact analysis
- Registry Centre desktop view
- API and CLI additions
- public release version `1.3.0`
- version consistency evidence
- registry architecture evidence
- safety boundary evidence

## Reference projects

- MicroGrow V1: read-only comparison target
- New-Earth-AI-Employee: read-only comparison target
