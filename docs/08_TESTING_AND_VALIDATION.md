# Testing and Validation

## Required lanes

### Unit
Schemas, hashing, classification, database operations, plugin contracts.

### Integration
Create project -> scan fixture repo -> query summary -> rescan -> diff.

### Safety
- excluded secret files are not read
- scanner does not mutate target repository
- symlink handling is safe
- unsupported files fail gracefully

### Migration
Every database migration must have a forward migration test.

### Acceptance — Alpha
1. Clean Windows setup succeeds.
2. `python -m neos doctor` returns healthy.
3. MicroGrow manifest imports.
4. MicroGrow repository scan completes without modifying the repository.
5. Project summary reports meaningful inventory.
6. Second unchanged scan reports no content changes.
7. Changed fixture produces correct diff.
8. Unit/integration tests pass.
9. Canonical DB can be backed up and restored.
10. Generated AI context includes provenance and timestamp.

## Release evidence
Release evidence belongs under `docs/release_evidence/` and should include commands, environment, commit, hashes and outcomes.
