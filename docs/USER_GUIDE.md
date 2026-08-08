# User Guide

## Windows desktop

- `docs/user/INSTALLING_NEOS_WINDOWS.md`
- `docs/user/STARTING_NEOS.md`
- `docs/user/ADDING_A_PROJECT.md`
- `docs/user/SCANNING_A_PROJECT.md`
- `docs/user/REFRESHING_PROJECT_INTELLIGENCE.md`
- `docs/user/PORTFOLIO_WORKSPACE_GUIDE.md`
- `docs/user/TROUBLESHOOTING_WINDOWS.md`
- `docs/user/CREATING_DIAGNOSTICS.md`

## 1. Install
Run `scripts/setup_windows.ps1` from PowerShell.

## 2. Register a project
`python -m neos init-project --manifest <manifest>`

## 3. Scan
`python -m neos scan --project-id <id> --repo <path>`

## 4. Inspect
`python -m neos project-summary --project-id <id>`

## 5. Back up
Run `scripts/backup_neos.ps1`.

## Understanding outputs
The current Alpha skeleton reports observed repository artefacts. Counts are derived facts, not manually curated feature truth. Future versions will add scan diff, feature relationships and evidence intelligence.

## Portfolio workspace
Use the desktop Portfolio Workspace to compare capability matrices, technology overlap, reuse opportunities, dependencies, portfolio risks, attention items, timeline events, and search results across the registered project set.

## Portfolio AI
The AI Assistant remains project-scoped by default. The Portfolio Workspace can send a selected project set to the deterministic portfolio AI path so multi-project citations stay explicit and auditable.
