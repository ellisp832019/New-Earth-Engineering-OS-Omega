# Flight Snapshots

Flight snapshots are immutable records of engineering state.

## Snapshot fields

- id
- project_id
- source_commit
- source_branch
- scan_id
- genome_snapshot_id
- memory_snapshot_id
- timestamp
- schema_version
- repository_state_hash
- semantic_state_hash
- genome_hash
- memory_hash
- metadata

## Persistence

Snapshots are stored in SQLite and are deduplicated by a source fingerprint derived from the canonical state hashes.

## Practical meaning

If two snapshots have the same source fingerprint, NEOS treats them as the same engineering state even if they were generated at different times.
