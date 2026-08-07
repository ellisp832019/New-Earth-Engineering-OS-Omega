# System Architecture

## Architectural rule

NEOS separates **truth ingestion**, **normalized project state**, **knowledge relationships**, **derived intelligence**, **AI context**, and **presentation**.

```text
Repositories / Docs / Test Evidence / Releases / Hardware Evidence
                         |
                    Ingestion Layer
                         |
                  Normalization Layer
                         |
         Project Registry + Knowledge Graph
                         |
        Query / Diff / Impact / Evidence Services
                         |
                  AI Context Gateway
                         |
           Desktop UI / CLI / Future Agents
```

## Core services

### Project Registry
Stores project identity, roots, technology profile, lifecycle status and canonical configuration.

### Repository Scanner
Walks a repository with explicit ignore rules and classifies artefacts. It must avoid secret directories and generated build trees by default.

### Knowledge Graph Store
Stores nodes and edges with provenance. Alpha uses SQLite for auditability and simple deployment.

### Change Intelligence
Compares scans, identifies added/removed/changed artefacts and later maps those changes to features and releases.

### Evidence Store
Stores references to test reports, build logs, release verification, hardware experiments and other evidence. Large binary evidence should be referenced, not copied into the database.

### AI Context Gateway
Generates bounded, provenance-rich context bundles. It does not give an AI unrestricted filesystem access.

### Plugin Runtime
Lets domain adapters identify deeper semantics for Flutter, PlatformIO, KiCad, Python, GitHub and other ecosystems.

## Persistence

Alpha:
- SQLite canonical store
- JSON project manifests
- JSON scan snapshots where useful
- file hashes for change tracking

Later:
- Optional graph database adapter
- optional vector index for semantic search
- content-addressed evidence cache

## Trust boundaries

1. Source repository: external input, potentially untrusted.
2. Scanner: read-only by default.
3. Canonical store: NEOS-owned state.
4. Automation: explicit write permissions.
5. AI: consumes generated context, not raw unrestricted host access.

## Dependency rule

The CLI and core model must remain usable without the desktop application. The UI is a client of the core, not the owner of project truth.
