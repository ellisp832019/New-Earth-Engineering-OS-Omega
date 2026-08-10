# Provenance Evidence

The workspace response records evidence provenance from:

- manifest declarations
- registry evidence
- scan evidence
- persisted project-relationship evidence
- live Git state
- release-readiness output
- derived summaries

This keeps the desktop and CLI views traceable back to the backend state that produced them.

Workspace reads do not call Portfolio Intelligence as part of normal composition. They consume existing persisted evidence only.
