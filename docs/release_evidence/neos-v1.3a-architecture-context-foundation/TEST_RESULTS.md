# Test Results

Observed validation during this pass:

- `python -m pytest -q` - passed
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy
- `cd apps\desktop; flutter analyze` - passed
- `cd apps\desktop; flutter test` - passed
