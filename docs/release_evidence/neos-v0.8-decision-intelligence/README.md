# NEOS v0.8 Engineering Decision Intelligence Evidence

This bundle records the observed closeout for the v0.8 deterministic decision-intelligence pass.

What it covers:

- schema 9 migration for decision intelligence tables
- deterministic decision evaluation and recommendation storage
- decision inbox, next actions, release readiness, reuse, and scenario routes
- operator accept, reject, and defer flows
- desktop Decision Centre surface
- validation evidence from Python and Flutter test runs

Observed validation on Saturday, August 8, 2026:

- `python -m pytest -q`
- `python -m ruff check src tests`
- `python -m mypy src\neos`
- `flutter analyze`
- `flutter test`

Important note:

- The Decision Centre remains operator-controlled.
- AI remains read-only and advisory outside the deterministic decision engine.

