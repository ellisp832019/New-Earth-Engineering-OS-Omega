# Release and Versioning Strategy

NEOS itself uses semantic versioning once API contracts stabilize. During Alpha, minor versions may include schema changes but migrations are still mandatory.

Every release should record:
- Git commit
- database schema version
- CLI version
- plugin versions
- tests executed
- packaging hash
- known limitations
- upgrade/rollback notes

Canonical project versions and NEOS application versions are separate concepts.
