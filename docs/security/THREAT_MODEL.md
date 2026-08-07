# Threat Model

## Assets
- source code
- engineering IP
- credentials
- project metadata
- release evidence
- AI context
- local database

## Threats
1. Credential leakage during scans.
2. Prompt injection embedded in repository documents.
3. Malicious symlink traversal.
4. Untrusted plugin behavior.
5. Accidental modification of managed repositories.
6. Stale or fabricated evidence.
7. Corrupt database or migration failure.
8. AI overconfidence based on incomplete context.

## Controls
- ignore/exclusion policy
- no secret-content ingestion by default
- normalized path boundary checks
- plugin capability declarations
- read-only scan mode
- hashes and provenance
- schema migrations and backups
- explicit uncertainty in AI context

## Residual risk
NEOS cannot guarantee a repository is safe or truthful. It provides mechanisms to preserve provenance and reduce accidental trust.
