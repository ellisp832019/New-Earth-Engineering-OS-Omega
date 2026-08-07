# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---:|---:|---|
| R-001 | Scope explosion | High | High | Alpha limited to one-repo understanding |
| R-002 | AI introduced before reliable data | High | High | deterministic core first |
| R-003 | Scanner leaks secrets | Medium | Critical | exclusions, filename screening, safety tests |
| R-004 | UI duplicates core logic | Medium | High | thin-client architecture |
| R-005 | Schema churn | High | Medium | versioned migrations |
| R-006 | Plugin ecosystem becomes unsafe | Medium | High | capabilities, sandboxing roadmap, review |
| R-007 | Generated state pollutes Git | High | Medium | `.neos/` and generated outputs ignored |
| R-008 | Knowledge becomes stale | Medium | High | snapshot freshness + rescan/drift indicators |
