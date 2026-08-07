# Backup and Recovery

## Alpha
Back up the `.neos/neos.db` SQLite file and project manifests. Scanned repositories remain external source systems and are not duplicated by default.

## Recovery test
A release is not operationally ready until a backup can be restored into a clean checkout and the project registry/query functions still work.

## Future
Add point-in-time snapshots, content-addressed evidence and encrypted backup destinations.
