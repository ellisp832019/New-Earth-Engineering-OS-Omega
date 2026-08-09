# MicroGrow Decision History
Evidence-backed decision chronology for `microgrow-v1`.
Decision count: **7**

| id | title | status | effective_date | confidence |
| --- | --- | --- | --- | --- |
| memory_decision-bab90b2ca9a70370a8d9dc45 | ADR-0001-api-style | accepted | 2026-03-03 | 0.92 |
| memory_decision-939df070dad57dc513accfb1 | README | accepted | 2026-08-07T08:04:28.589068+00:00 | 0.92 |
| memory_decision-e98db9ffb808632c3d15184e | ADR_TEMPLATE | accepted | 2026-08-07T08:04:28.669364+00:00 | 0.92 |
| memory_decision-f48ff43e9f192fd37798ce7e | ADR-0001-local-first-architecture | draft | YYYY-MM-DD | 0.92 |
| memory_decision-aa626bc64c3d4995c73167e4 | ADR-0002-one-hub-per-site | draft | YYYY-MM-DD | 0.92 |
| memory_decision-9b297c862273e06c103075cf | ADR-0003-pressure-tube-water-level-method | draft | YYYY-MM-DD | 0.92 |
| memory_decision-4424dec1d6d9e6201d6920f4 | ADR_Architecture_decision_board | accepted | YYYY-MM-DD | 0.92 |

```json
{
  "count": 7,
  "items": [
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725526+00:00",
      "effective_date": "2026-03-03",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-bab90b2ca9a70370a8d9dc45",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\n\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\n\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\n\n---",
        "context": "MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\n\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\n\n- reading sensor data\n- controlling relays\n- simple debugging\n- straightforward integration with Flutter\n\nThe main options considered for node communication were:\n\n- HTTP REST\n- MQTT\n\n---",
        "decision": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
        "decision_id": "dec-53b22ae52b0c2cf3edd50e13",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\n\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\n\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\n\n---",
          "context": "MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\n\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\n\n- reading sensor data\n- controlling relays\n- simple debugging\n- straightforward integration with Flutter\n\nThe main options considered for node communication were:\n\n- HTTP REST\n- MQTT\n\n---",
          "date": "2026-03-03",
          "decision": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-53b22ae52b0c2cf3edd50e13"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
      "source_type": "adr",
      "status": "accepted",
      "summary": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.668744+00:00",
      "title": "ADR-0001-api-style"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725496+00:00",
      "effective_date": null,
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-939df070dad57dc513accfb1",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "",
        "context": "",
        "decision": "",
        "decision_id": "dec-5b496ce8cc0ef340108fbf04",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "",
          "context": "",
          "date": null,
          "decision": "",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-5b496ce8cc0ef340108fbf04"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/README.md",
      "source_type": "adr",
      "status": "accepted",
      "summary": "README",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.589068+00:00",
      "title": "README"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725444+00:00",
      "effective_date": null,
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-e98db9ffb808632c3d15184e",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "",
        "context": "",
        "decision": "",
        "decision_id": "dec-6a17f892cfec83686fee60fb",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "",
          "context": "",
          "date": null,
          "decision": "",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-6a17f892cfec83686fee60fb"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_TEMPLATE.md",
      "source_type": "adr",
      "status": "accepted",
      "summary": "ADR_TEMPLATE",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.669364+00:00",
      "title": "ADR_TEMPLATE"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725551+00:00",
      "effective_date": "YYYY-MM-DD",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-f48ff43e9f192fd37798ce7e",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "Describe benefits, risks, and trade-offs.",
        "context": "Describe the engineering problem.",
        "decision": "Describe the chosen approach.",
        "decision_id": "dec-a8c82b3f394209e77d292add",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "Describe benefits, risks, and trade-offs.",
          "context": "Describe the engineering problem.",
          "date": "YYYY-MM-DD",
          "decision": "Describe the chosen approach.",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-a8c82b3f394209e77d292add"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0001-local-first-architecture.md",
      "source_type": "adr",
      "status": "draft",
      "summary": "Describe the chosen approach.",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.588468+00:00",
      "title": "ADR-0001-local-first-architecture"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725572+00:00",
      "effective_date": "YYYY-MM-DD",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-aa626bc64c3d4995c73167e4",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "Describe benefits, risks, and trade-offs.",
        "context": "Describe the engineering problem.",
        "decision": "Describe the chosen approach.",
        "decision_id": "dec-d4d54b8abb19febe1965c6e0",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "Describe benefits, risks, and trade-offs.",
          "context": "Describe the engineering problem.",
          "date": "YYYY-MM-DD",
          "decision": "Describe the chosen approach.",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-d4d54b8abb19febe1965c6e0"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0002-one-hub-per-site.md",
      "source_type": "adr",
      "status": "draft",
      "summary": "Describe the chosen approach.",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.588672+00:00",
      "title": "ADR-0002-one-hub-per-site"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725590+00:00",
      "effective_date": "YYYY-MM-DD",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-9b297c862273e06c103075cf",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "Describe benefits, risks, and trade-offs.",
        "context": "Describe the engineering problem.",
        "decision": "Describe the chosen approach.",
        "decision_id": "dec-c58592d5d660c7b367ca76d8",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "Describe benefits, risks, and trade-offs.",
          "context": "Describe the engineering problem.",
          "date": "YYYY-MM-DD",
          "decision": "Describe the chosen approach.",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-c58592d5d660c7b367ca76d8"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0003-pressure-tube-water-level-method.md",
      "source_type": "adr",
      "status": "draft",
      "summary": "Describe the chosen approach.",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.588889+00:00",
      "title": "ADR-0003-pressure-tube-water-level-method"
    },
    {
      "confidence": 0.92,
      "created_at": "2026-08-07T09:23:18.725607+00:00",
      "effective_date": "YYYY-MM-DD",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_decision-4424dec1d6d9e6201d6920f4",
      "memory_schema_version": 2,
      "memory_type": "decision",
      "metadata": {
        "alternatives": "",
        "consequences": "Explain what this decision enables, limits, or changes.\n\n---",
        "context": "Describe the situation, constraints, and options being considered.\n\nExample:\nMicroGrow requires a communication model between the node and app.\nThe options considered were HTTP REST and MQTT.\n\n---",
        "decision": "State the decision clearly and directly.\n\nExample:\nHTTP REST was selected for V1 communication.\n\n---",
        "decision_id": "dec-ba5e752cd4fc4c89650e047e",
        "rationale": "",
        "source_metadata": {
          "alternatives": "",
          "consequences": "Explain what this decision enables, limits, or changes.\n\n---",
          "context": "Describe the situation, constraints, and options being considered.\n\nExample:\nMicroGrow requires a communication model between the node and app.\nThe options considered were HTTP REST and MQTT.\n\n---",
          "date": "YYYY-MM-DD",
          "decision": "State the decision clearly and directly.\n\nExample:\nHTTP REST was selected for V1 communication.\n\n---",
          "rationale": ""
        },
        "status_source": "engineering_decisions"
      },
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "related_entities": [
        "dec-ba5e752cd4fc4c89650e047e"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_Architecture_decision_board.md",
      "source_type": "adr",
      "status": "accepted",
      "summary": "State the decision clearly and directly.\n\nExample:\nHTTP REST was selected for V1 communication.\n\n---",
      "superseded_by": null,
      "timestamp": "2026-08-07T08:04:28.669050+00:00",
      "title": "ADR_Architecture_decision_board"
    }
  ],
  "project_id": "microgrow-v1"
}
```
