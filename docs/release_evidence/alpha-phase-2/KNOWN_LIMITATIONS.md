# Known Limitations

Observed on 2026-08-07.

- Feature candidates are heuristic until an operator confirms them.
- The dependency graph v1 is intentionally conservative and focuses on deterministic relationships that the scanner can justify.
- `trace` and `impact` work only over recorded semantic rows and graph edges; they do not invent missing structure.
- Prompt-injection defense is heuristic and looks for explicit marker phrases in repository text.
- Configuration extraction is broad and may include many generated or documentation-oriented keys in large repositories.
- The read-only acceptance proof covers MicroGrow only; other repositories still need their own scan evidence if they are used as release targets.
