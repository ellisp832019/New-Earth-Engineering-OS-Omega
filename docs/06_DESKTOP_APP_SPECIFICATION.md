# Desktop Application Specification

## Platform

Primary target: Windows desktop. Recommended implementation: Flutter desktop communicating with the local NEOS core through an internal service/CLI boundary.

## Main navigation

1. Home
2. Projects
3. Repository Intelligence
4. Knowledge Graph
5. Features & Requirements
6. Tests & Evidence
7. Releases
8. Timeline
9. Documentation
10. AI Engineering Assistant
11. Plugins
12. System Health
13. Settings

## Home
Show project health, current branch/release, stale knowledge warnings, failed validations, recent changes and recommended next actions.

## Project Explorer
Provide hierarchical and semantic views. A file tree alone is insufficient; users should also browse by feature, subsystem, release and evidence.

## Knowledge Graph
Interactive graph visualization with filters. Every relationship must be inspectable and show provenance.

## AI Assistant
Questions should display evidence links, freshness, scope and uncertainty. The UI must distinguish deterministic facts from AI interpretation.

## Design language
Calm, professional, dense enough for engineering work, but not visually noisy. Prioritize information hierarchy and traceability over decorative dashboards.

## Desktop Alpha rule
The app should begin as a thin client. Do not duplicate scanner/business logic inside Flutter.
