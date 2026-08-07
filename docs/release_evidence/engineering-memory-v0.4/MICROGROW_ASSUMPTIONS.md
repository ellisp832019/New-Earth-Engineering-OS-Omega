# MicroGrow Assumptions
Explicit engineering assumptions and their current status.
Assumption count: **18**

| id | title | status | effective_date | confidence |
| --- | --- | --- | --- | --- |
| memory_assumption-590a07226a56eebe873b9fa3 | MicroGrow - `<Feature Name>` (FSD) | unvalidated | 2026-04-06T22:26:11+01:00 | 0.70 |
| memory_assumption-0a32bf6ba38d71bbc6aa09dd | AI FSD Implementation Plan | unvalidated | 2026-04-08T09:54:18+01:00 | 0.70 |
| memory_assumption-5513fe2de8e7744572633079 | AI FSD Implementation Plan | unvalidated | 2026-04-08T23:55:17+01:00 | 0.70 |
| memory_assumption-c0b9108b76d28e14c2b8d01d | MicroGrow - Relay Boot Inhibit And Interlock (FSD) | unvalidated | 2026-04-09T15:10:44+01:00 | 0.70 |
| memory_assumption-11035782e88594bcaf53d2f1 | MicroGrow - Firmware and App Execution Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-279d31018aff5dfcd6361ace | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-4ae033a13b3e0a9aead01f96 | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-726699edf9802f8895cc754d | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-ae40df62b6760ed9dca331fa | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-b3bdff9400db4e8ccd5e91cc | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-ca2f85891505d70a25493fca | MicroGrow - Development Roadmap | unvalidated | 2026-05-30T14:40:58+01:00 | 0.70 |
| memory_assumption-7849a03d1b2b595d063cfa8d | MicroGrow V1 Now / Next / Later Roadmap | unvalidated | 2026-05-31T05:34:15+01:00 | 0.70 |

```json
{
  "count": 18,
  "items": [
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:24.907050+00:00",
      "effective_date": "2026-04-06T22:26:11+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-590a07226a56eebe873b9fa3",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "`<important assumption>`"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/fsd/fsd_template.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/fsd/fsd_template.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "`<important assumption>`",
      "superseded_by": null,
      "timestamp": "2026-04-06T22:26:11+01:00",
      "title": "MicroGrow - `<Feature Name>` (FSD)"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:25.092400+00:00",
      "effective_date": "2026-04-08T09:54:18+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-0a32bf6ba38d71bbc6aa09dd",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "Keep this logic in Flutter only; do not add firmware behavior or new discovery assumptions."
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/fsd/tasks/fsd_002_device_setup_recovery_ux_tasks.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/fsd/tasks/fsd_002_device_setup_recovery_ux_tasks.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "Keep this logic in Flutter only; do not add firmware behavior or new discovery assumptions.",
      "superseded_by": null,
      "timestamp": "2026-04-08T09:54:18+01:00",
      "title": "AI FSD Implementation Plan"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:25.259204+00:00",
      "effective_date": "2026-04-08T23:55:17+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-5513fe2de8e7744572633079",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "Ensure the release checklist treats irrigation guardrail behavior as an explicit safety check rather than an informal assumption."
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/fsd/tasks/fsd_003_automation_guardrails_tasks.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/fsd/tasks/fsd_003_automation_guardrails_tasks.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "Ensure the release checklist treats irrigation guardrail behavior as an explicit safety check rather than an informal assumption.",
      "superseded_by": null,
      "timestamp": "2026-04-08T23:55:17+01:00",
      "title": "AI FSD Implementation Plan"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:24.737373+00:00",
      "effective_date": "2026-04-09T15:10:44+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-c0b9108b76d28e14c2b8d01d",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "rerun the hardware safety gate with a clear pass/fail result instead of relying on assumptions about floating GPIO behavior"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/fsd/fsd_006_relay_boot_inhibit_interlock.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/fsd/fsd_006_relay_boot_inhibit_interlock.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "rerun the hardware safety gate with a clear pass/fail result instead of relying on assumptions about floating GPIO behavior",
      "superseded_by": null,
      "timestamp": "2026-04-09T15:10:44+01:00",
      "title": "MicroGrow - Relay Boot Inhibit And Interlock (FSD)"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.427637+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-11035782e88594bcaf53d2f1",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "document all safety assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/firmware_app_execution_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/firmware_app_execution_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "document all safety assumptions",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Firmware and App Execution Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:22.746596+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-279d31018aff5dfcd6361ace",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "validate relay wear, timing assumptions, and fail-safe behavior for automated switching"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "validate relay wear, timing assumptions, and fail-safe behavior for automated switching",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:22.908178+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-4ae033a13b3e0a9aead01f96",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "document automation rules, assumptions, and override policy"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "document automation rules, assumptions, and override policy",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:22.398832+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-726699edf9802f8895cc754d",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "power and physical safety assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "power and physical safety assumptions",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.075694+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-ae40df62b6760ed9dca331fa",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "tighten documentation around supported sensors, relays, and power assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "tighten documentation around supported sensors, relays, and power assumptions",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.249485+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-b3bdff9400db4e8ccd5e91cc",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "firmware, app, docs, and hardware assumptions are in sync"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "firmware, app, docs, and hardware assumptions are in sync",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:22.570977+00:00",
      "effective_date": "2026-05-30T14:40:58+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-ca2f85891505d70a25493fca",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "validate that the current pin map, relay behavior, and SHTC3 I2C timing assumptions are stable on real hardware"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/development_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/development_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "validate that the current pin map, relay behavior, and SHTC3 I2C timing assumptions are stable on real hardware",
      "superseded_by": null,
      "timestamp": "2026-05-30T14:40:58+01:00",
      "title": "MicroGrow - Development Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:24.154147+00:00",
      "effective_date": "2026-05-31T05:34:15+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-7849a03d1b2b595d063cfa8d",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "define pricing assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/microgrow_v1_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/microgrow_v1_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "define pricing assumptions",
      "superseded_by": null,
      "timestamp": "2026-05-31T05:34:15+01:00",
      "title": "MicroGrow V1 Now / Next / Later Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:24.533210+00:00",
      "effective_date": "2026-06-06T09:04:37+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-0cfc3affabed773fd621d2ac",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "the evidence matrix is filled by real measurements, not assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/v1_0_hardening_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/v1_0_hardening_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "the evidence matrix is filled by real measurements, not assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-06T09:04:37+01:00",
      "title": "MicroGrow V1.0 Hardening Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:24.327521+00:00",
      "effective_date": "2026-06-06T09:04:37+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-cb0fed21a93afa18ec5dbe4a",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "local-only deployment assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/v1_0_hardening_roadmap.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/v1_0_hardening_roadmap.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "local-only deployment assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-06T09:04:37+01:00",
      "title": "MicroGrow V1.0 Hardening Roadmap"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.691314+00:00",
      "effective_date": "2026-06-07T20:11:19+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-0ceffb44fa7fcea337cd5c60",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "packs that rely on highly specialized hardware assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/microgrow_crop_profile_pack_catalog_choices.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/microgrow_crop_profile_pack_catalog_choices.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "packs that rely on highly specialized hardware assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-07T20:11:19+01:00",
      "title": "MicroGrow Crop Profile Pack Catalog Choices"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.854778+00:00",
      "effective_date": "2026-06-07T20:22:04+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-26e1e117241e33808b9e5016",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "avoid special hardware assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "avoid special hardware assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-07T20:22:04+01:00",
      "title": "MicroGrow Crop Profile Pack First Wave Lineup"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.982556+00:00",
      "effective_date": "2026-06-07T20:22:04+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-dbd62ed694aaa053e075ad56",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "regulated-agriculture assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "regulated-agriculture assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-07T20:22:04+01:00",
      "title": "MicroGrow Crop Profile Pack First Wave Lineup"
    },
    {
      "confidence": 0.7,
      "created_at": "2026-08-07T09:23:23.543319+00:00",
      "effective_date": "2026-06-07T20:23:49+01:00",
      "genome_id": "genome-874beeefe1bcb72981dd5864",
      "id": "memory_assumption-c584127f7e6b3bfb3d8d52df",
      "memory_schema_version": 2,
      "memory_type": "assumption",
      "metadata": {
        "source_excerpt": "pack-specific firmware assumptions"
      },
      "project_id": "microgrow-v1",
      "provenance": "explicit-assumption-text",
      "related_entities": [
        "docs/10_roadmap/microgrow_crop_profile_first_wave_template.md"
      ],
      "scan_id": "scan-aac96b9287d74edf",
      "source_branch": "planning/microgrow-v1-firmware-target-dependency-lock",
      "source_commit": "0f9df32862bfb74f0acba8c4c1aa84d5a17c8363",
      "source_path": "docs/10_roadmap/microgrow_crop_profile_first_wave_template.md",
      "source_type": "assumption_doc",
      "status": "unvalidated",
      "summary": "pack-specific firmware assumptions",
      "superseded_by": null,
      "timestamp": "2026-06-07T20:23:49+01:00",
      "title": "MicroGrow Crop Profile First Wave Template"
    }
  ],
  "project_id": "microgrow-v1"
}
```
