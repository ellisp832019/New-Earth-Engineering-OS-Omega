# Hardware CLI Evidence

Observed command surface:

- `python -m neos hardware --help`
- `python -m neos --db <db> hardware summary demo`
- `python -m neos --db <db> hardware trace demo GPIO21`
- `python -m neos --db <db> hardware impact demo GPIO21`

Representative output from the fixture project:

- `summary` reported `board_count: 1`, `component_count: 2`, `pin_mapping_count: 2`, `validation_state: validated`
- `trace` returned the `GPIO21 -> I2C_SDA` mapping
- `impact` returned the same hardware pin entity and summary counts

The command parser exposes:

- `summary`
- `boards`
- `components`
- `bom`
- `pins`
- `validation`
- `gaps`
- `risks`
- `trace`
- `impact`
- `diff`
