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

## Final closeout snapshot

- implementation SHA: `a2b7cfdca8f69e3073204fe44c4a0c79711ec614`
- merge SHA: `ce8a271538dc67aeb0b83319b68f29583815b44c`
- main SHA: `ce8a271538dc67aeb0b83319b68f29583815b44c`
- release branch: `release/neos-v1.3.0-closeout`
- package root: `dist\New-Earth-Engineering-OS-Windows-v1.3.0`
- package ZIP: `dist\New-Earth-Engineering-OS-Windows-v1.3.0.zip`
- package ZIP SHA-256: `29E0CE878B62D6A2CC8CE05B2BA569EF5F74A95001A8473CE7998E325298584F`

### Final package manifest

- `git_sha`: `ce8a271538dc67aeb0b83319b68f29583815b44c`
- `git_branch`: `main`
- `build_timestamp_utc`: `2026-08-09T15:50:56.2350722Z`
- `neos_version`: `1.3.0`
- `database_schema`: `11`
- `api_version`: `v1`

### Final package file hashes

- `NEOS.exe`
  - SHA-256: `66C6D7ED8EFCE6DC31CD73B5EF20CD091654E5FFA32DAAC39875466BB073895B`
  - size: `128000` bytes
- `neos_engine.exe`
  - SHA-256: `F75BDF69B68900210DFF3662E8B3B4FBB914EC1F260C1A989F6212EB771B24BD`
  - size: `10370045` bytes
- `runtime\neos_engine.exe`
  - SHA-256: `F75BDF69B68900210DFF3662E8B3B4FBB914EC1F260C1A989F6212EB771B24BD`
  - size: `10370045` bytes

### Final smoke checks

- `python -m pytest -q` - passed (`30 passed`)
- `python -m ruff check src tests` - passed
- `python -m mypy src\neos` - passed
- `python -m neos doctor` - healthy
- `cd apps\desktop; flutter analyze` - passed
- `cd apps\desktop; flutter test` - passed
- `scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck` - passed
- `scripts\smoke_windows_package.ps1` - passed

## Reference projects

- MicroGrow V1: read-only comparison target
- New-Earth-AI-Employee: read-only comparison target
