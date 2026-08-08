# Hardware Intelligence Architecture

NEOS v1.1.0 adds a deterministic, read-only hardware intelligence slice that turns hardware files into structured project evidence.

## Discovery

The backend scans project repositories for likely hardware artefacts such as:

- KiCad project, schematic, and PCB files
- BOM CSV or JSON files
- pin mapping notes
- bring-up or validation notes
- datasheet references
- board revision hints

## Parser Pipeline

The hardware intelligence module normalizes discovered files into a snapshot with:

- board revisions
- component models
- component instances
- connectors
- pin mappings
- power rails
- datasheet references
- validation evidence
- risks
- gaps

Parsing is deterministic. The same inputs produce the same snapshot.

## Canonical Data

The backend exposes hardware snapshots through the project payload and dedicated hardware routes.

The desktop client renders the snapshot in Hardware Centre as a read-only view.

## API Boundary

Hardware intelligence is served from the local NEOS backend. The API is still `v1`; the hardware routes are additive.

## Desktop Boundary

The desktop app requests hardware data from the backend and does not parse hardware artefacts itself.

## Provenance

Evidence remains tied to discovered files and their repository paths. The module prefers explicit file content over inference.

## Read-Only Guarantees

- no hardware file edits are performed
- no external services are contacted
- no cloud synchronization is required

## Current Limitations

- the parser is conservative and may not understand every CAD or BOM format
- unsupported file names may not be discovered
- validation state is evidence-based, not electrical certification
- the module does not manufacture confidence where the repository has no proof
