# Safety Review

This release remains read-only and conservative.

No new authority was introduced for:

- deployment
- firmware flashing
- actuator control
- external repository mutation

The workspace layer only classifies, summarizes, reconciles, and presents evidence that already exists in the local NEOS data model.

Project safety facts are separate from NEOS platform authority:

- NEOS platform authority remains `FALSE` for actuator control, firmware flashing, deployment, and external repository mutation.
- Project safety facts are only marked `TRUE` or `FALSE` when an explicit project contract exists.
- Missing project safety evidence remains `UNKNOWN`.
- Workspace safety summaries preserve provenance for every field.
