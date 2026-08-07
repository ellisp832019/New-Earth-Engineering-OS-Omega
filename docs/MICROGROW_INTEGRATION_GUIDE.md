# MicroGrow Integration Guide

1. Confirm the real MicroGrow repository is clean or record its existing state.
2. Run NEOS from the NEOS repository, not inside MicroGrow.
3. Import `examples/microgrow/project.neos.json`.
4. Scan with `scripts/demo_microgrow.ps1` or the CLI.
5. Re-check `git status` in MicroGrow to confirm NEOS did not modify it.
6. Review inventory and classify gaps before adding semantic plugins.

Never use the initial Alpha scanner as proof that a feature is complete. It inventories artefacts; later semantic layers establish feature and requirement traceability.
