# Hardware Architecture Evidence

Implemented hardware architecture is documented in:

- `docs/hardware/HARDWARE_INTELLIGENCE_ARCHITECTURE.md`
- `docs/api/API_V1.md`
- `docs/user/HARDWARE_CENTRE_GUIDE.md`

Observed implementation surface:

- deterministic file-based hardware discovery
- board, component, pin, BOM, validation, risk, and gap snapshots
- project payload hardware injection
- dedicated hardware routes
- read-only desktop Hardware Centre presentation
- CLI hardware commands

Current constraints:

- conservative parser
- evidence-based validation only
- no external hardware services
- no manufacturing or certification claims
