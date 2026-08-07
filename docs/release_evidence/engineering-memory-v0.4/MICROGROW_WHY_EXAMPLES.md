# MicroGrow Why Examples
Representative `why` and memory trace results.
Decision example: `dec-53b22ae52b0c2cf3edd50e13`
Feature example: `feat-f775897b978921d2a59877ac`

## Why on decision

```json
{
  "decisions": [
    {
      "alternatives": "",
      "confidence": 0.92,
      "consequences": "This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\n\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\n\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\n\n---",
      "context": "MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\n\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\n\n- reading sensor data\n- controlling relays\n- simple debugging\n- straightforward integration with Flutter\n\nThe main options considered for node communication were:\n\n- HTTP REST\n- MQTT\n\n---",
      "created_at": "2026-08-07T08:04:28.668744+00:00",
      "date": "2026-03-03",
      "decision": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
      "id": "dec-53b22ae52b0c2cf3edd50e13",
      "metadata_json": "{\"alternatives\": \"\", \"consequences\": \"This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\\n\\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\\n\\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\\n\\n---\", \"context\": \"MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\\n\\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\\n\\n- reading sensor data\\n- controlling relays\\n- simple debugging\\n- straightforward integration with Flutter\\n\\nThe main options considered for node communication were:\\n\\n- HTTP REST\\n- MQTT\\n\\n---\", \"date\": \"2026-03-03\", \"decision\": \"HTTP REST was selected as the communication model for MicroGrow V1.\\n\\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\\n\\n---\", \"rationale\": \"\"}",
      "observed_at": "2026-08-07T08:04:28.668744+00:00",
      "project_id": "microgrow-v1",
      "provenance": "adr-markdown",
      "rationale": "",
      "scan_id": "scan-aac96b9287d74edf",
      "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
      "status": "accepted",
      "title": "ADR-0001-api-style"
    }
  ],
  "entity": {
    "alternatives": "",
    "confidence": 0.92,
    "consequences": "This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\n\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\n\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\n\n---",
    "context": "MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\n\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\n\n- reading sensor data\n- controlling relays\n- simple debugging\n- straightforward integration with Flutter\n\nThe main options considered for node communication were:\n\n- HTTP REST\n- MQTT\n\n---",
    "created_at": "2026-08-07T08:04:28.668744+00:00",
    "date": "2026-03-03",
    "decision": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
    "entity_table": "engineering_decisions",
    "entity_type": "engineering_decision",
    "id": "dec-53b22ae52b0c2cf3edd50e13",
    "metadata_json": "{\"alternatives\": \"\", \"consequences\": \"This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\\n\\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\\n\\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\\n\\n---\", \"context\": \"MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\\n\\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\\n\\n- reading sensor data\\n- controlling relays\\n- simple debugging\\n- straightforward integration with Flutter\\n\\nThe main options considered for node communication were:\\n\\n- HTTP REST\\n- MQTT\\n\\n---\", \"date\": \"2026-03-03\", \"decision\": \"HTTP REST was selected as the communication model for MicroGrow V1.\\n\\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\\n\\n---\", \"rationale\": \"\"}",
    "observed_at": "2026-08-07T08:04:28.668744+00:00",
    "project_id": "microgrow-v1",
    "provenance": "adr-markdown",
    "rationale": "",
    "scan_id": "scan-aac96b9287d74edf",
    "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
    "status": "accepted",
    "title": "ADR-0001-api-style"
  },
  "evidence": [
    {
      "row": {
        "confidence": 0.92,
        "content_hash": "719ad593d9a7b40b4cb443e544ea05b89d1ad25a498ff2cefd6d970b30cc0648",
        "decision_id": "dec-53b22ae52b0c2cf3edd50e13",
        "end_line": 78,
        "entity_id": "dec-53b22ae52b0c2cf3edd50e13",
        "evidence_type": "adr_markdown",
        "id": "dec_ev-7136d8b053df69255f3d171e",
        "metadata_json": "{\"alternatives\": \"\", \"consequences\": \"This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\\n\\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\\n\\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\\n\\n---\", \"context\": \"MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\\n\\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\\n\\n- reading sensor data\\n- controlling relays\\n- simple debugging\\n- straightforward integration with Flutter\\n\\nThe main options considered for node communication were:\\n\\n- HTTP REST\\n- MQTT\\n\\n---\", \"date\": \"2026-03-03\", \"decision\": \"HTTP REST was selected as the communication model for MicroGrow V1.\\n\\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\\n\\n---\", \"rationale\": \"\"}",
        "project_id": "microgrow-v1",
        "provenance": "adr-markdown",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
        "start_line": 1
      },
      "type": "decision_evidence"
    }
  ],
  "historical_changes": [],
  "memory_trace": {
    "count": 5,
    "edges": [
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624402+00:00",
        "depth": 1,
        "id": "memory_rel-8dd12ccdcbf1baf4785f4749",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_decision-bab90b2ca9a70370a8d9dc45",
        "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624402+00:00",
        "depth": 2,
        "id": "memory_rel-8dd12ccdcbf1baf4785f4749",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_decision-bab90b2ca9a70370a8d9dc45",
        "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624428+00:00",
        "depth": 2,
        "id": "memory_rel-908e08532f5151c994bc0f4f",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
        "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.634769+00:00",
        "depth": 2,
        "id": "memory_rel-e49cf272788b649b5e01232b",
        "metadata": {
          "entity": "docs/09_logs/MG-MILESTONE-TIMELINE.md"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
        "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624428+00:00",
        "depth": 3,
        "id": "memory_rel-908e08532f5151c994bc0f4f",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
        "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624437+00:00",
        "depth": 3,
        "id": "memory_rel-3c96d58ad0c21fb2e317f200",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
        "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.634628+00:00",
        "depth": 3,
        "id": "memory_rel-7878f1ac323eb150385ae0f9",
        "metadata": {
          "entity": "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
        "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624437+00:00",
        "depth": 4,
        "id": "memory_rel-3c96d58ad0c21fb2e317f200",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
        "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.624444+00:00",
        "depth": 4,
        "id": "memory_rel-9a4010a3184afaa81db2266f",
        "metadata": {
          "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-c9a5489b8961130afbe37616",
        "target_record_id": "memory_milestone-5ca6b418440f71ce12bb0a85"
      },
      {
        "confidence": 0.65,
        "created_at": "2026-08-07T09:24:43.634643+00:00",
        "depth": 4,
        "id": "memory_rel-35e8a176bc9e5b8b59cdf86c",
        "metadata": {
          "entity": "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md"
        },
        "project_id": "microgrow-v1",
        "provenance": "deterministic-memory-ordering",
        "relationship_type": "occurred_before",
        "source_record_id": "memory_milestone-c9a5489b8961130afbe37616",
        "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
      }
    ],
    "entity_id": "dec-53b22ae52b0c2cf3edd50e13",
    "nodes": [
      {
        "depth": 0,
        "id": "memory_decision-bab90b2ca9a70370a8d9dc45",
        "record": {
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
        }
      },
      {
        "depth": 1,
        "id": "memory_milestone-a36313291c8f9c3dba2d4f25",
        "record": {
          "confidence": 0.68,
          "created_at": "2026-08-07T09:23:40.034752+00:00",
          "effective_date": "2026-03-14T15:05:03Z",
          "genome_id": "genome-874beeefe1bcb72981dd5864",
          "id": "memory_milestone-a36313291c8f9c3dba2d4f25",
          "memory_schema_version": 2,
          "memory_type": "milestone",
          "metadata": {
            "source_excerpt": "# MicroGrow Milestone Timeline This document tracks the major development phases of the MicroGrow platform. Each milestone represents a stable advancement in system capability and repository maturity. --- # Milestone Overview ## MG-001 \u2014 Pr"
          },
          "project_id": "microgrow-v1",
          "provenance": "explicit-milestone-text",
          "related_entities": [
            "docs/09_logs/MG-MILESTONE-TIMELINE.md"
          ],
          "scan_id": "scan-aac96b9287d74edf",
          "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
          "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
          "source_path": "docs/09_logs/MG-MILESTONE-TIMELINE.md",
          "source_type": "milestone_doc",
          "status": "complete",
          "summary": "This document tracks the major development phases of the MicroGrow platform.",
          "superseded_by": null,
          "timestamp": "2026-03-14T15:05:03Z",
          "title": "MicroGrow Milestone Timeline"
        }
      },
      {
        "depth": 2,
        "id": "memory_milestone-a527785b8b855e64182de50e",
        "record": {
          "confidence": 0.68,
          "created_at": "2026-08-07T09:23:39.228797+00:00",
          "effective_date": "2026-03-16T14:18:00Z",
          "genome_id": "genome-874beeefe1bcb72981dd5864",
          "id": "memory_milestone-a527785b8b855e64182de50e",
          "memory_schema_version": 2,
          "memory_type": "milestone",
          "metadata": {
            "source_excerpt": "# MG-LOG-APP-001 Flutter Architecture Refactor \u2013 Phase 1 Historical context: This phase log captures the Flutter refactor window on 2026-03-14. File paths and folder names here describe the in-progress tree at that point, not necessarily th"
          },
          "project_id": "microgrow-v1",
          "provenance": "explicit-milestone-text",
          "related_entities": [
            "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md"
          ],
          "scan_id": "scan-aac96b9287d74edf",
          "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
          "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
          "source_path": "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
          "source_type": "milestone_doc",
          "status": "complete",
          "summary": "Flutter Architecture Refactor \u2013 Phase 1",
          "superseded_by": null,
          "timestamp": "2026-03-16T14:18:00Z",
          "title": "MG-LOG-APP-001"
        }
      },
      {
        "depth": 3,
        "id": "memory_milestone-c9a5489b8961130afbe37616",
        "record": {
          "confidence": 0.68,
          "created_at": "2026-08-07T09:23:39.311416+00:00",
          "effective_date": "2026-03-16T14:18:00Z",
          "genome_id": "genome-874beeefe1bcb72981dd5864",
          "id": "memory_milestone-c9a5489b8961130afbe37616",
          "memory_schema_version": 2,
          "memory_type": "milestone",
          "metadata": {
            "source_excerpt": "# MG-LOG-APP-002 Flutter Architecture Refactor \u2013 Phase 2 Historical context: This phase log captures the Flutter refactor window on 2026-03-14. File paths and folder names here describe the in-progress tree at that point, not necessarily th"
          },
          "project_id": "microgrow-v1",
          "provenance": "explicit-milestone-text",
          "related_entities": [
            "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md"
          ],
          "scan_id": "scan-aac96b9287d74edf",
          "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
          "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
          "source_path": "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
          "source_type": "milestone_doc",
          "status": "complete",
          "summary": "Flutter Architecture Refactor \u2013 Phase 2",
          "superseded_by": null,
          "timestamp": "2026-03-16T14:18:00Z",
          "title": "MG-LOG-APP-002"
        }
      },
      {
        "depth": 4,
        "id": "memory_milestone-5ca6b418440f71ce12bb0a85",
        "record": {
          "confidence": 0.68,
          "created_at": "2026-08-07T09:23:42.108833+00:00",
          "effective_date": "2026-03-17T13:27:35Z",
          "genome_id": "genome-874beeefe1bcb72981dd5864",
          "id": "memory_milestone-5ca6b418440f71ce12bb0a85",
          "memory_schema_version": 2,
          "memory_type": "milestone",
          "metadata": {
            "source_excerpt": "# MicroGrow V1 RC1 Burn-In Checklist Use this checklist after tagging a release candidate and before promoting it to `v1.0.0`. For the current project state, this checklist applies to: - tag: `v1.0.0-rc1` - release-candidate commit: `998107"
          },
          "project_id": "microgrow-v1",
          "provenance": "explicit-milestone-text",
          "related_entities": [
            "docs/10_roadmap/rc1_burn_in_checklist.md"
          ],
          "scan_id": "scan-aac96b9287d74edf",
          "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
          "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
          "source_path": "docs/10_roadmap/rc1_burn_in_checklist.md",
          "source_type": "milestone_doc",
          "status": "complete",
          "summary": "Use this checklist after tagging a release candidate and before promoting it to `v1.0.0`.",
          "superseded_by": null,
          "timestamp": "2026-03-17T13:27:35Z",
          "title": "MicroGrow V1 RC1 Burn-In Checklist"
        }
      }
    ]
  },
  "rationale": "Rationale not recorded in current NEOS evidence.",
  "recorded_rationale": [
    "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---"
  ],
  "related_decisions": [
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
    }
  ],
  "supporting_evidence": [],
  "unknown_rationale": []
}
```

## Why on feature

```json
{
  "decisions": [],
  "entity": {
    "confidence": 0.98,
    "created_at": "2026-08-07T08:04:29.535466+00:00",
    "description": "Deterministically inferred feature area from observed repository evidence for api.",
    "entity_table": "features",
    "entity_type": "feature",
    "id": "feat-f775897b978921d2a59877ac",
    "introduced_version": null,
    "metadata_json": "{\"evidence_count\": 111, \"evidence_paths\": [\"contracts/api_fixtures/README.md\", \"contracts/api_fixtures/access_test_account_seed_data.json\", \"contracts/api_fixtures/get_auth_me_pro_active_owner_response.json\", \"contracts/api_fixtures/get_auth_me_pro_expired_owner_response.json\", \"contracts/api_fixtures/get_auth_me_pro_grace_owner_response.json\", \"contracts/api_fixtures/get_auth_me_team_editor_response.json\", \"contracts/api_fixtures/get_auth_me_team_owner_response.json\", \"contracts/api_fixtures/get_auth_me_team_viewer_response.json\", \"contracts/api_fixtures/get_config_response.json\", \"contracts/api_fixtures/get_crop_profile_catalog_response.json\", \"contracts/api_fixtures/get_crop_profile_entitlements_response.json\", \"contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json\", \"contracts/api_fixtures/get_data_response.json\", \"contracts/api_fixtures/get_firmware_capabilities_response.json\", \"contracts/api_fixtures/get_firmware_update_status_response.json\", \"contracts/api_fixtures/get_firmware_version_response.json\", \"contracts/api_fixtures/get_info_response.json\", \"contracts/api_fixtures/get_outputs_response.json\", \"contracts/api_fixtures/get_status_response.json\", \"contracts/api_fixtures/get_subscription_summary_local_response.json\"]}",
    "name": "API",
    "project_id": "microgrow-v1",
    "provenance": "path-heuristic",
    "removed_version": null,
    "scan_id": "scan-aac96b9287d74edf",
    "source": "heuristic",
    "status": "candidate",
    "updated_at": "2026-08-07T08:04:29.535466+00:00"
  },
  "evidence": [
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "b7f367393ab5c4c62c8e9e3856bf53408960032c8964f737cabbede5366d224b",
        "end_line": null,
        "entity_id": "raw-ff922448b8020201ec7e36ea",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-f93d55a937627d1cfdd56d36",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/README.md",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "34c5bb1d586c071aa6cc6eb07a09f9643e2aaed778faff7c28206d2b239cac49",
        "end_line": null,
        "entity_id": "raw-b61438226816042da09c30b7",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-a39d3da504af96153eb18585",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/access_test_account_seed_data.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "43899864202ba74f73ee1ca7f8cffc60f4597795986c50736d9bd26bc216912a",
        "end_line": null,
        "entity_id": "raw-f704ae00391fc4a4e4e13ac3",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-571f11476002db0de6a7dc76",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_pro_active_owner_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "707a85d72368645732ec91e398f258612c0b98420b93a31d367b04128cfd1b14",
        "end_line": null,
        "entity_id": "raw-77195109feb30586167c3341",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-032170906d0884edbd1f785f",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_pro_expired_owner_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "912a0fa5e8bdcc0b29dec4e73f424175b230adcdf1ebf32081c85c93b3f4be4a",
        "end_line": null,
        "entity_id": "raw-dabb60bd253f19cb2856d8cf",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-74a1166f5811257ce01f1aaf",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_pro_grace_owner_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "033aacdc9298797ea0f6fb1b511234d899d5b6477a800246b2dac1a3d67eda9f",
        "end_line": null,
        "entity_id": "raw-7dbb6356e46fb1dd30b03750",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-4913d54c4f1d77b892b8b653",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_team_editor_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "3d452ca42f22cb64b5627de4c8f5c7923bf7463085fceba8585597b0b222a0e8",
        "end_line": null,
        "entity_id": "raw-f17019d12f9afdbf9712aff0",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-24c3a1903b791e6b48e7fae8",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_team_owner_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "1d310dd6d96bffb07c6d8e3dc6aa405f3faacf87df4ebaaababf15f8ea225dd7",
        "end_line": null,
        "entity_id": "raw-f838e0aee2e3eadaf7d9bd51",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-14fec31c018497ae2725d5e4",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_auth_me_team_viewer_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "e186e68f4a061982fc157f9f53779efc41eb628400aeb598289b67cf425ed5dd",
        "end_line": null,
        "entity_id": "raw-b594fbe2993717c5df87f2ef",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-d928d9092dbe3aa47f013563",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_config_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "94e93e294a5d25861877885b336b3a889cc89262bbd9d0812078ce5b260b3df3",
        "end_line": null,
        "entity_id": "raw-9e2f9e4e988a4475b5341d7c",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-fe3b391d4cb5c6e809f2abd6",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_crop_profile_catalog_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "a2745196ebc0af2659c23c976b60926b0da2ca610b5b884b3f7029f70ed4449b",
        "end_line": null,
        "entity_id": "raw-a765031a92a80ee40d975a47",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-88d1b838c3f85042e53896c4",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_crop_profile_entitlements_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "b2fc68d3a999351ae5517a0c3ce8e1ede17603cfc3707269a87fbebc0c399060",
        "end_line": null,
        "entity_id": "raw-a7fc4e2a5494c358d2e657d9",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-0db85de79764ddc89a8dfef9",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "5a5e3bef0c7fd3ca239b6258a83f29970026fa3d9cc5a6f99d0bed30133ca961",
        "end_line": null,
        "entity_id": "raw-e6c524c56f7d2ed37ceba220",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-1c76b85852b706f06a1ef7d6",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_data_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "9b909bc954e420f5b65d111dfed8d58e5f8f9992df6e1dde5c63e151b8235a8b",
        "end_line": null,
        "entity_id": "raw-e4148c420450488b63ea66d9",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-be93dfd8ada30189b32a5e1f",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_firmware_capabilities_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "af3f435a32291212e5c0db8ec103929829e1b9d644219fb1bfc0396d33e375c3",
        "end_line": null,
        "entity_id": "raw-0d15c3ed22fc32f3c0a15e7e",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-9123f06dabfb7d266f8b3513",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_firmware_update_status_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "ce69986b7d6c536e604e3ad1bb3bfb04b85c5d8f502da10e27d98878a3524388",
        "end_line": null,
        "entity_id": "raw-f2aa542ed22a83332e1361f2",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-ff57e5d0b56d0b4c3ffa16e4",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_firmware_version_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "17ae9b136fc1b55e4856b715df0d0549322b694cdc869922c3cf33b9440f2d24",
        "end_line": null,
        "entity_id": "raw-061b3e8a2f6df17d0cbf2654",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-924a6ed65328db8d652e6941",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_info_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "3f7b9b2e3b542aad4ecb0c7c44381ec21d57d0868a506516542e21093a9d081d",
        "end_line": null,
        "entity_id": "raw-ef8ab372ed13e2c6ac408783",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-5f9b258df261b769aa112f94",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_outputs_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "e006970621c24ca61c3ccd5b1778e99d841562ac0fa23883a8c3cd6d77941609",
        "end_line": null,
        "entity_id": "raw-fa3e20ef470ff6ffad405c42",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-8709f3ac41e9f4242e33a129",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_status_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    },
    {
      "row": {
        "confidence": 0.98,
        "content_hash": "f1e9c750727ae3201b5b060116b9a6c7987022942a32003916c71347dfa812e7",
        "end_line": null,
        "entity_id": "raw-184dbb73ffcb52a6e9ad2e2f",
        "evidence_type": "path",
        "feature_id": "feat-f775897b978921d2a59877ac",
        "id": "feat_ev-09bce8be8391f52df53d4953",
        "metadata_json": "{\"feature_name\": \"API\"}",
        "project_id": "microgrow-v1",
        "provenance": "path-heuristic",
        "scan_id": "scan-aac96b9287d74edf",
        "source_path": "contracts/api_fixtures/get_subscription_summary_local_response.json",
        "start_line": null
      },
      "type": "feature_evidence"
    }
  ],
  "historical_changes": [],
  "memory_trace": {
    "count": 0,
    "edges": [],
    "entity_id": "feat-f775897b978921d2a59877ac",
    "nodes": []
  },
  "rationale": "Rationale not recorded in current NEOS evidence.",
  "recorded_rationale": [],
  "related_decisions": [],
  "supporting_evidence": [],
  "unknown_rationale": [
    "Rationale not recorded in current engineering memory."
  ]
}
```

## Memory trace

```json
{
  "count": 5,
  "edges": [
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624402+00:00",
      "depth": 1,
      "id": "memory_rel-8dd12ccdcbf1baf4785f4749",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_decision-bab90b2ca9a70370a8d9dc45",
      "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624402+00:00",
      "depth": 2,
      "id": "memory_rel-8dd12ccdcbf1baf4785f4749",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_decision-bab90b2ca9a70370a8d9dc45",
      "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624428+00:00",
      "depth": 2,
      "id": "memory_rel-908e08532f5151c994bc0f4f",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
      "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.634769+00:00",
      "depth": 2,
      "id": "memory_rel-e49cf272788b649b5e01232b",
      "metadata": {
        "entity": "docs/09_logs/MG-MILESTONE-TIMELINE.md"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
      "target_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624428+00:00",
      "depth": 3,
      "id": "memory_rel-908e08532f5151c994bc0f4f",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a36313291c8f9c3dba2d4f25",
      "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624437+00:00",
      "depth": 3,
      "id": "memory_rel-3c96d58ad0c21fb2e317f200",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
      "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.634628+00:00",
      "depth": 3,
      "id": "memory_rel-7878f1ac323eb150385ae0f9",
      "metadata": {
        "entity": "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
      "target_record_id": "memory_milestone-a527785b8b855e64182de50e"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624437+00:00",
      "depth": 4,
      "id": "memory_rel-3c96d58ad0c21fb2e317f200",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-a527785b8b855e64182de50e",
      "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.624444+00:00",
      "depth": 4,
      "id": "memory_rel-9a4010a3184afaa81db2266f",
      "metadata": {
        "entity": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-c9a5489b8961130afbe37616",
      "target_record_id": "memory_milestone-5ca6b418440f71ce12bb0a85"
    },
    {
      "confidence": 0.65,
      "created_at": "2026-08-07T09:24:43.634643+00:00",
      "depth": 4,
      "id": "memory_rel-35e8a176bc9e5b8b59cdf86c",
      "metadata": {
        "entity": "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md"
      },
      "project_id": "microgrow-v1",
      "provenance": "deterministic-memory-ordering",
      "relationship_type": "occurred_before",
      "source_record_id": "memory_milestone-c9a5489b8961130afbe37616",
      "target_record_id": "memory_milestone-c9a5489b8961130afbe37616"
    }
  ],
  "entity_id": "dec-53b22ae52b0c2cf3edd50e13",
  "nodes": [
    {
      "depth": 0,
      "id": "memory_decision-bab90b2ca9a70370a8d9dc45",
      "record": {
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
      }
    },
    {
      "depth": 1,
      "id": "memory_milestone-a36313291c8f9c3dba2d4f25",
      "record": {
        "confidence": 0.68,
        "created_at": "2026-08-07T09:23:40.034752+00:00",
        "effective_date": "2026-03-14T15:05:03Z",
        "genome_id": "genome-874beeefe1bcb72981dd5864",
        "id": "memory_milestone-a36313291c8f9c3dba2d4f25",
        "memory_schema_version": 2,
        "memory_type": "milestone",
        "metadata": {
          "source_excerpt": "# MicroGrow Milestone Timeline This document tracks the major development phases of the MicroGrow platform. Each milestone represents a stable advancement in system capability and repository maturity. --- # Milestone Overview ## MG-001 \u2014 Pr"
        },
        "project_id": "microgrow-v1",
        "provenance": "explicit-milestone-text",
        "related_entities": [
          "docs/09_logs/MG-MILESTONE-TIMELINE.md"
        ],
        "scan_id": "scan-aac96b9287d74edf",
        "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
        "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
        "source_path": "docs/09_logs/MG-MILESTONE-TIMELINE.md",
        "source_type": "milestone_doc",
        "status": "complete",
        "summary": "This document tracks the major development phases of the MicroGrow platform.",
        "superseded_by": null,
        "timestamp": "2026-03-14T15:05:03Z",
        "title": "MicroGrow Milestone Timeline"
      }
    },
    {
      "depth": 2,
      "id": "memory_milestone-a527785b8b855e64182de50e",
      "record": {
        "confidence": 0.68,
        "created_at": "2026-08-07T09:23:39.228797+00:00",
        "effective_date": "2026-03-16T14:18:00Z",
        "genome_id": "genome-874beeefe1bcb72981dd5864",
        "id": "memory_milestone-a527785b8b855e64182de50e",
        "memory_schema_version": 2,
        "memory_type": "milestone",
        "metadata": {
          "source_excerpt": "# MG-LOG-APP-001 Flutter Architecture Refactor \u2013 Phase 1 Historical context: This phase log captures the Flutter refactor window on 2026-03-14. File paths and folder names here describe the in-progress tree at that point, not necessarily th"
        },
        "project_id": "microgrow-v1",
        "provenance": "explicit-milestone-text",
        "related_entities": [
          "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md"
        ],
        "scan_id": "scan-aac96b9287d74edf",
        "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
        "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
        "source_path": "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
        "source_type": "milestone_doc",
        "status": "complete",
        "summary": "Flutter Architecture Refactor \u2013 Phase 1",
        "superseded_by": null,
        "timestamp": "2026-03-16T14:18:00Z",
        "title": "MG-LOG-APP-001"
      }
    },
    {
      "depth": 3,
      "id": "memory_milestone-c9a5489b8961130afbe37616",
      "record": {
        "confidence": 0.68,
        "created_at": "2026-08-07T09:23:39.311416+00:00",
        "effective_date": "2026-03-16T14:18:00Z",
        "genome_id": "genome-874beeefe1bcb72981dd5864",
        "id": "memory_milestone-c9a5489b8961130afbe37616",
        "memory_schema_version": 2,
        "memory_type": "milestone",
        "metadata": {
          "source_excerpt": "# MG-LOG-APP-002 Flutter Architecture Refactor \u2013 Phase 2 Historical context: This phase log captures the Flutter refactor window on 2026-03-14. File paths and folder names here describe the in-progress tree at that point, not necessarily th"
        },
        "project_id": "microgrow-v1",
        "provenance": "explicit-milestone-text",
        "related_entities": [
          "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md"
        ],
        "scan_id": "scan-aac96b9287d74edf",
        "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
        "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
        "source_path": "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
        "source_type": "milestone_doc",
        "status": "complete",
        "summary": "Flutter Architecture Refactor \u2013 Phase 2",
        "superseded_by": null,
        "timestamp": "2026-03-16T14:18:00Z",
        "title": "MG-LOG-APP-002"
      }
    },
    {
      "depth": 4,
      "id": "memory_milestone-5ca6b418440f71ce12bb0a85",
      "record": {
        "confidence": 0.68,
        "created_at": "2026-08-07T09:23:42.108833+00:00",
        "effective_date": "2026-03-17T13:27:35Z",
        "genome_id": "genome-874beeefe1bcb72981dd5864",
        "id": "memory_milestone-5ca6b418440f71ce12bb0a85",
        "memory_schema_version": 2,
        "memory_type": "milestone",
        "metadata": {
          "source_excerpt": "# MicroGrow V1 RC1 Burn-In Checklist Use this checklist after tagging a release candidate and before promoting it to `v1.0.0`. For the current project state, this checklist applies to: - tag: `v1.0.0-rc1` - release-candidate commit: `998107"
        },
        "project_id": "microgrow-v1",
        "provenance": "explicit-milestone-text",
        "related_entities": [
          "docs/10_roadmap/rc1_burn_in_checklist.md"
        ],
        "scan_id": "scan-aac96b9287d74edf",
        "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
        "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
        "source_path": "docs/10_roadmap/rc1_burn_in_checklist.md",
        "source_type": "milestone_doc",
        "status": "complete",
        "summary": "Use this checklist after tagging a release candidate and before promoting it to `v1.0.0`.",
        "superseded_by": null,
        "timestamp": "2026-03-17T13:27:35Z",
        "title": "MicroGrow V1 RC1 Burn-In Checklist"
      }
    }
  ]
}
```
