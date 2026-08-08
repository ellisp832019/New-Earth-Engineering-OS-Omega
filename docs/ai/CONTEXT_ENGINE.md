# Context Engine

The context engine converts a user question into a bounded engineering context bundle.

## Sources

- Project summary
- Genome
- Features
- Decisions
- Memory
- Flight Recorder
- APIs
- Configuration
- Symbols
- Tests
- Documentation
- Why / Impact / Trace views

## Behavior

- Classify intent first.
- Rank evidence deterministically.
- Trim to a context budget.
- Flag stale repository state when scan head differs from current HEAD.
- Carry prompt-injection warnings forward as safety findings.
