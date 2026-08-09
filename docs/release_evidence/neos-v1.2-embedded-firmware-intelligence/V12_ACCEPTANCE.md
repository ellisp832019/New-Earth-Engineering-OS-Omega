# V1.2 Acceptance Notes

- product version target: `1.2.0`
- API version: `v1`
- database schema: `11`
- detector version: `firmware-static-2026-08-heuristic-hardened-v1`

## Current outcome
- firmware source discovery: complete
- targets/environments: complete
- build variants: complete
- RTOS/task intelligence: complete for static evidence, partial for call-graph depth
- interrupt intelligence: complete for handler review and conservative body findings
- timing facts: complete
- state-machine intelligence: complete for candidate/canonical discovery and transitions
- peripherals/buses: complete
- GPIO ownership/conflicts: complete with alias and conditional-variant protection
- hardware compatibility: complete with deterministic precedence and reasons
- protocol/packet evidence: complete
- firmware findings: complete
- provenance: complete
- deterministic diff: complete
- false-positive controls: complete
- Firmware Centre: complete
- API and CLI: complete
- MicroGrow safe analysis: complete
- docs/evidence: in progress in this worktree

## Known limitations
- deep call-graph reconstruction remains partial
- formal timing verification remains partial
- watchdog correctness is not claimed without validation
- memory analysis remains conservative
