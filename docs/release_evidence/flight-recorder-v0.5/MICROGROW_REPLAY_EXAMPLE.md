# MicroGrow Replay Example

Replay from `flight_snapshot-5eb57b2b695cc5cace75ca7e` to `flight_snapshot-38f979826dd1efc23aad6462` produced 8 ordered items.

```json
{
  "count": 8,
  "items": [
    {
      "id": "flight_snapshot-5eb57b2b695cc5cace75ca7e",
      "kind": "snapshot",
      "summary": "Snapshot flight_snapshot-5eb57b2b695cc5cace75ca7e",
      "timestamp": "2026-08-07T11:07:36.063085+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "flight_snapshot-5eb57b2b695cc5cace75ca7e",
      "kind": "snapshot",
      "metadata": {
        "scan_id": "scan-e80b879c6f434f5d",
        "source_commit": "cb4ac7cd43170549c66dc7381f742c005017b24b"
      },
      "summary": "Flight snapshot flight_snapshot-5eb57b2b695cc5cace75ca7e",
      "timestamp": "2026-08-07T11:07:36.063085+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "memory_decision-3533320ced27c199237cb0bb",
      "kind": "decision",
      "metadata": {
        "source_path": "C:/Users/ellis/AppData/Local/Temp/neos-flight-3lk2i5mr/microgrow-clone/docs/adr/README.md",
        "status": "accepted"
      },
      "summary": "README",
      "timestamp": "2026-08-07T11:09:46.477933+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "memory_decision-1bc53778a7e31bcff7a5bc41",
      "kind": "decision",
      "metadata": {
        "source_path": "C:/Users/ellis/AppData/Local/Temp/neos-flight-3lk2i5mr/microgrow-clone/engineering_logs/decisions/ADR_TEMPLATE.md",
        "status": "accepted"
      },
      "summary": "ADR_TEMPLATE",
      "timestamp": "2026-08-07T11:09:46.564983+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "flight_event-e85eab48c4739d8578833f50",
      "kind": "config_changed",
      "metadata": {
        "affected_entities": [
          "cfg-0deb87bcc912143c78a57e3f",
          "cfg-477eb740e4962de74c90ef30",
          "cfg-4d321b2bb0f518c1f6a1522e",
          "cfg-65bf7ea475a5f9218fb6d917",
          "cfg-76516226e5c7cebeaa25192c",
          "cfg-77fc31de24e33db7c305cd19",
          "cfg-922310ee057d4d559eda9963",
          "cfg-b46946036c23d2008303ed46",
          "cfg-d471485cac9d149fc1ada4f1",
          "cfg-e4e1e71224bdc720946b8553",
          "cfg-f7b53f603988cbcee6c3433b",
          "cfg-0fea290a53633d3618b9e7d4",
          "cfg-2d63cad6ec67549a50eb49bc",
          "cfg-7571409e5b6c1b8ea70ac87d",
          "cfg-8d2df208a72cd817871b259a",
          "cfg-95bb4b5a6640967a3d91b64b",
          "cfg-b3ae4c0bcf1fc091cd0c4694",
          "cfg-cc0a3c14a6fbbc9309a51f3c",
          "cfg-cc32e7660f9596ba4f214852",
          "cfg-e7938dcad3f53fa587b7e5c7",
          "cfg-f4412b74aab9f7376954ef5f"
        ]
      },
      "summary": "config_changed",
      "timestamp": "2026-08-07T11:09:51.883216+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "flight_event-c22fd0004ab941131e2789d2",
      "kind": "maturity_changed",
      "metadata": {
        "affected_entities": [
          "maturity"
        ]
      },
      "summary": "maturity_changed",
      "timestamp": "2026-08-07T11:09:51.883216+00:00"
    },
    {
      "entity": "microgrow-v1",
      "id": "flight_snapshot-38f979826dd1efc23aad6462",
      "kind": "snapshot",
      "metadata": {
        "scan_id": "scan-491d8eb9b9fd4e28",
        "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "summary": "Flight snapshot flight_snapshot-38f979826dd1efc23aad6462",
      "timestamp": "2026-08-07T11:09:51.883216+00:00"
    },
    {
      "id": "flight_snapshot-38f979826dd1efc23aad6462",
      "kind": "snapshot",
      "summary": "Snapshot flight_snapshot-38f979826dd1efc23aad6462",
      "timestamp": "2026-08-07T11:09:51.883216+00:00"
    }
  ],
  "project_id": "microgrow-v1",
  "source": "flight_snapshot-5eb57b2b695cc5cace75ca7e",
  "target": "flight_snapshot-38f979826dd1efc23aad6462"
}
```
