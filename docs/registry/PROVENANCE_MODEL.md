# Provenance Model

The registry keeps provenance attached to every discovered contract, identity hint, and drift signal.

## Provenance fields

- source file path
- source kind
- repository scope
- extracted contract type
- extraction confidence
- evidence notes

## Provenance rules

- prefer explicit files over inference
- preserve source paths
- annotate synthetic envelopes clearly
- separate discovery from interpretation

## Why provenance matters

The registry is only useful if an operator can see why the backend believes a project identity or contract exists.
