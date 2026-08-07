# Plugin Architecture

## Purpose

The core should understand generic repositories. Plugins provide deeper domain intelligence.

## Plugin categories
- language adapters
- build-system adapters
- application-framework adapters
- hardware/CAD adapters
- evidence importers
- external service connectors
- report generators

## Initial plugin API

A plugin declares:
- id
- version
- capabilities
- detection rules
- analyze(path, context) -> findings

Findings may propose nodes, edges, metadata and evidence references.

## Safety

Plugins are read-only by default. Mutation capability must be separately declared and explicitly enabled by the user/project policy.

## Planned plugins

### PlatformIO
Detect environments, boards, frameworks, source roots and build configuration.

### Flutter
Detect packages, platforms, dependencies, test roots and application entry points.

### Python
Detect pyproject, packages, test frameworks and CLI entry points.

### KiCad
Index projects, schematics, PCBs, BOM outputs and revision artefacts without modifying design files.

### GitHub
Import issues, PRs, releases and CI evidence through an explicit connector.
