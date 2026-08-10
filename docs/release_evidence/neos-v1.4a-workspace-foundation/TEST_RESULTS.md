# Test Results

Validation commands and results:

- `python -m pytest -q` - passed, 32 tests
- `python -m pytest -q tests/test_workspace.py` - passed, 2 tests
- `python -m pytest -q tests/test_service_api.py tests/test_registry_intelligence.py tests/test_ecosystem.py` - passed, 5 tests
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `flutter analyze` - passed
- `flutter test` - passed
- `flutter build windows --release` - passed

