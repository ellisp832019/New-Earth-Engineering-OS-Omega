# NEOS v1.2.0 Embedded Firmware Intelligence Evidence

This folder collects the closeout evidence for the embedded firmware intelligence slice.

## Observed validation
- `python -m pytest -q`: 28 passed before the release closeout work began
- `python -m ruff check src tests`: passed
- `python -m mypy src\neos`: passed
- `python -m neos doctor`: healthy, schema 11, version 1.1.0 before the release bump
- `flutter analyze`: passed on `apps/desktop`
- `flutter test`: passed on `apps/desktop`
- `flutter build windows`: passed on `apps/desktop`

## Synthetic fixture
- environments: 3
- targets: 3
- build variants: 3
- tasks: 1
- RTOS primitives: 8
- timing facts: 3
- state machines: 1
- deterministic diff: yes

## MicroGrow
- firmware sources: 196
- environments: 1
- targets: 1
- build variants: 1
- timing facts: 50
- buses: 4
- compatibility state: possible_mismatch
