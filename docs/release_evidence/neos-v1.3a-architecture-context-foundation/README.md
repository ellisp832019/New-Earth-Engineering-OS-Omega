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
- closeout commit: `0ff61454cf08418d94b274634ee764e6090f9585`
- closeout merge / final main SHA: `e4ea2bd44ace4e330bf5b50c4dbb1e0ebb37cd92`
- release branch: `release/neos-v1.3.0-closeout`
- final evidence branch: `release/neos-v1.3.0-final-evidence`
- package root: `dist\New-Earth-Engineering-OS-Windows-v1.3.0`
- package ZIP: `dist\New-Earth-Engineering-OS-Windows-v1.3.0.zip`
- package ZIP SHA-256: `375EFAD471080337A1286F579A13DD066246B3A281EA45F54E1A3AFB79B6B276`

### Final package manifest

- `git_sha`: `e4ea2bd44ace4e330bf5b50c4dbb1e0ebb37cd92`
- `git_branch`: `main`
- `build_timestamp_utc`: `2026-08-09T18:37:24.1802128Z`
- `neos_version`: `1.3.0`
- `database_schema`: `11`
- `api_version`: `v1`

### Final package file hashes

- `NEOS.exe`
  - SHA-256: `65673C2C15081AD1BCBC025825FCCF4DC973DFDA1474E4EBDFA5BD45DB1EC28D`
  - size: `128000` bytes
- `neos_engine.exe`
  - SHA-256: `81ECA55CAC0FEB5F7399F090F83B5FC060BC5D96608DB872F372F840CFD798C1`
  - size: `10367638` bytes
- `runtime\neos_engine.exe`
  - SHA-256: `81ECA55CAC0FEB5F7399F090F83B5FC060BC5D96608DB872F372F840CFD798C1`
  - size: `10367638` bytes

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
