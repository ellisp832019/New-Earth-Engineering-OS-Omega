# Impact Analysis Guide

Impact analysis in NEOS v1.3.0 is read-only and deterministic.

## When to use it

- checking whether a project change may affect a nearby project
- reviewing overlap between two registered projects
- validating whether identity or contract claims look stale
- looking for coupling before a release or migration

## What to expect

- a conservative relationship score
- shared contract type indicators
- explicit peer comparison notes
- no hidden writes or mutations

## What it does not do

- it does not guarantee safety
- it does not estimate business risk
- it does not replace engineering review
