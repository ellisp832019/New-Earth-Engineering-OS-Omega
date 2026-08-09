# Historical Reconstruction

Historical reconstruction lets NEOS answer `state at time T` questions without checking out old commits inside the reference repository.

## Resolution order

1. Exact flight snapshot id
2. Exact Git commit recorded in the scan history
3. Latest stored snapshot when the exact state is unavailable

## Safe Git usage

Read-only commands are allowed:

- `git show`
- `git log`
- `git ls-tree`
- `git diff`
- `git cat-file`

## Unknowns

If reconstruction is incomplete, NEOS must surface unknowns rather than pretending the state is exact.
