# Performance

The registry layer is designed to be lightweight.

## Performance posture

- derived from local data already available to the project database
- read-only on the scanned repositories
- no extra schema migration cost
- no network round trip requirement
