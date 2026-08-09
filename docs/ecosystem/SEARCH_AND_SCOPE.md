# Search and Scope

NEOS ecosystem search ranks registered portfolio entities by deterministic keyword overlap.

Scope rules:

- single-project operation must remain unchanged
- portfolio search may run against a selected set of projects
- multi-project AI answers must keep the selected project IDs visible in the request and citation metadata
- synthetic fixtures may be used for deterministic validation, but they must be labeled synthetic

Use `neos ecosystem search QUERY` or the desktop Portfolio Workspace search tab to inspect the selected portfolio scope.
