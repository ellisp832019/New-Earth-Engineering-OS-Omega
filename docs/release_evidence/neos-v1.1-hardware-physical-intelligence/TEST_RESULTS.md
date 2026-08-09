# Test Results

Backend validation:

- `python -m pytest -q` -> `21 passed`
- `python -m ruff check src tests` -> passed
- `python -m mypy src\\neos` -> passed
- `python -m neos doctor` -> healthy, `neos_version=1.1.0`, `database_schema=11`

Desktop validation:

- `flutter pub get` -> passed
- `flutter analyze` -> passed
- `flutter test` -> passed
- `flutter build windows --release` -> passed

Hardware smoke:

- CLI help and fixture commands -> passed
- HTTP hardware routes -> passed

Windows smoke:

- backend smoke -> passed
- package smoke -> passed
