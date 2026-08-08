# Hardware API Evidence

Observed HTTP results from a synthetic fixture project:

- `GET /hardware/demo` -> `200`
- `GET /hardware/demo/boards` -> `200`
- `GET /hardware/demo/pins` -> `200`
- `GET /hardware/demo/validation` -> `200`
- `GET /hardware/missing` -> `404 not_found`

Representative summary fields returned:

- `board_count: 1`
- `component_count: 2`
- `pin_mapping_count: 2`
- `validation_state: validated`

These responses came from a deterministic temporary project database with KiCad-like and BOM fixture files.
