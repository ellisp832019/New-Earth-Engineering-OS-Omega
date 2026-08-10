# Test Results

Validation commands and results:

- `python -m pytest -q` - passed, 34 tests
- `python -m pytest tests/test_workspace.py -q` - passed, 4 tests
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy, database schema 11, NEOS version 1.3.0
- `python -m neos --help` - passed
- `python -m neos workspace --help` - passed
- `cd apps\desktop && flutter pub get` - passed
- `flutter analyze` - passed
- `flutter test` - passed
- `flutter build windows --release` - passed
