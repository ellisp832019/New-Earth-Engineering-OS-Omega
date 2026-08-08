# NEOS v1.1.0 Release Notes

## Summary

NEOS v1.1.0 closes out the Hardware & Physical Engineering Intelligence slice and packages it as a Windows release.

## New Capabilities

- deterministic hardware artefact discovery
- structured board, component, BOM, pin, validation, risk, and gap views
- Hardware Centre in the desktop app
- hardware service routes
- hardware CLI commands
- hardware trace and impact lookups

## Windows Package

- portable Windows release bundle
- backend and desktop binaries included
- package metadata aligned to `1.1.0`

## Upgrade Notes

Users upgrading from `1.0.0` should keep their local projects and database. The release remains local-first and read-only for hardware evidence.

## Known Limitations

- hardware parsing is conservative
- unsupported file formats may be ignored
- validation reports evidence, not certification
- the release does not add embedded firmware intelligence

## Security and Behavior

- localhost-only backend behavior is preserved
- backend ownership and shutdown behavior are preserved
- provider-disabled AI mode remains unchanged
- no external hardware services are required
