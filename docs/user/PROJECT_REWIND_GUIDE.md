# Project Rewind Guide

Use rewind when you need to inspect an older engineering state.

## Example

```powershell
neos flight state microgrow-v1 --at 0f9df32862bfb74f0acba8c4c1aa84d5a17c8363 --json
```

## What you can ask

- What features existed?
- What tests existed?
- What decisions were active?
- What risks were present?
- What unknowns were still unresolved?

## When reconstruction is partial

NEOS surfaces unknowns explicitly instead of guessing.
