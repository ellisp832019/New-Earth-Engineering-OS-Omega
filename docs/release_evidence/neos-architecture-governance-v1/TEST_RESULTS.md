# Test Results

Validated locally with:

```bash
python -m pytest -q tests/test_governance.py
```

Result:

- `3 passed`

Focused coverage verified:

- deterministic governance report generation
- read-only CLI and HTTP governance surfaces
- rule coverage for canonical, planned, embedded, legacy, reference, dependency, and unregistered estate scenarios
