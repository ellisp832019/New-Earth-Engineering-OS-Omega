# Desktop Connection Evidence

Observed on 2026-08-07.

## Previous failure

The startup UI progressed through engine and database steps but stalled before the connection completed.

## Connection contract

The shell now records:

- the active service URI
- backend ownership state
- process id
- instance id
- shutdown token
- health payload

## Expected result

When the backend is healthy, the startup state should advance to connected and the main shell should load against the same service URI.
