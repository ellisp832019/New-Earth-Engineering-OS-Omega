# Test Results

Observed validation during this pass:

- `python -m pytest -q` - passed
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy
- `powershell -ExecutionPolicy Bypass -File .\scripts\package_windows.ps1 -SkipRepoCleanCheck` - passed
- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck` - passed
- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_package.ps1` - passed
- `cd apps\desktop; flutter analyze` - passed
- `cd apps\desktop; flutter test` - passed

The package build and smoke checks validated the integrated `main` release state at `ce8a271538dc67aeb0b83319b68f29583815b44c`.
The final merged-main release state is `e4ea2bd44ace4e330bf5b50c4dbb1e0ebb37cd92`.
