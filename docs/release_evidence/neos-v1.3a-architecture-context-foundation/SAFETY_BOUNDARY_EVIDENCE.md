# Safety Boundary Evidence

The registry and impact layers remain read-only orchestration layers.

Observed safety boundaries:

- no repository writes
- no external repository checkout or commit operations
- no firmware flashing
- no deployment activation
- no relay, pump, fan, lighting, or irrigation control
- no automatic safety-boundary mutation

The code only inspects local repository and SQLite evidence and returns derived projections.
