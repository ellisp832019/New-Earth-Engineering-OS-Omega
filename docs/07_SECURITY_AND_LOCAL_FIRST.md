# Security and Local-First Architecture

## Principles
- local processing by default
- least privilege
- read-only scanning by default
- explicit consent for writes
- secrets excluded from indexing
- deterministic audit logs
- bounded AI context

## Secret exclusions
Default scan exclusions include `.env`, private keys, credential directories, build outputs and common token stores. The scanner should classify suspicious filenames and avoid reading their content.

## AI boundary
AI integrations receive generated context bundles. They should not automatically receive whole repositories, credentials or unrelated personal files.

## External connectors
Cloud/GitHub/LLM connectors must be optional. Connector configuration should be stored separately from project manifests and never committed with secrets.

## Threat model summary
Threats include malicious repository content, prompt injection in documentation, poisoned plugin output, credential leakage, stale evidence, accidental writes, and over-trusting AI interpretations.

See `docs/security/THREAT_MODEL.md` for the detailed model.
