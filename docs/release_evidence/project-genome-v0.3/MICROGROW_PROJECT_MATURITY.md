# MicroGrow Project Maturity
Project: `microgrow-v1`
Label: **healthy**
Score: **946**

```json
{
  "components": [
    {
      "evidence": [
        ".github/workflows/app-ci.yml",
        ".github/workflows/commerce-backend-ci.yml",
        ".github/workflows/commerce-backend-provider-smoke.yml",
        ".github/workflows/firmware-ci.yml",
        "ai/codex_prompts/espnow_gateway_to_data_bridge_prompt.md",
        "ai/codex_prompts/espnow_lab_integration_prompt.md",
        "architecture/master/microgrow_engineering_dashboard.png",
        "architecture/master/microgrow_master_system_architecture.png",
        "architecture/v1_node/block_diagram.png",
        "architecture/v1_node/data_flow.png",
        "architecture/v1_node/firmware_module_interaction.png",
        "architecture/v1_node/microgrow_system_control_loop.png",
        "architecture/v1_node/microgrow_v1_node_architecture.png",
        "calibration/reference_measurements/README.md",
        "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md",
        "calibration/sensor_offsets/README.md",
        "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
        "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
        "contracts/api_fixtures/README.md",
        "contracts/api_fixtures/access_test_account_seed_data.json"
      ],
      "name": "architecture",
      "score": 100,
      "weight": 15
    },
    {
      "evidence": [
        "contracts/api_fixtures/README.md",
        "contracts/api_fixtures/access_test_account_seed_data.json",
        "contracts/api_fixtures/get_auth_me_pro_active_owner_response.json",
        "contracts/api_fixtures/get_auth_me_pro_expired_owner_response.json",
        "contracts/api_fixtures/get_auth_me_pro_grace_owner_response.json",
        "contracts/api_fixtures/get_auth_me_team_editor_response.json",
        "contracts/api_fixtures/get_auth_me_team_owner_response.json",
        "contracts/api_fixtures/get_auth_me_team_viewer_response.json",
        "contracts/api_fixtures/get_config_response.json",
        "contracts/api_fixtures/get_crop_profile_catalog_response.json"
      ],
      "name": "implementation",
      "score": 54,
      "weight": 20
    },
    {
      "evidence": [
        "contracts/api_fixtures/access_test_account_seed_data.json",
        "docs/02_product/system_specification.md",
        "docs/03_architecture/microgrow_node_specification.md",
        "docs/04_hardware/mist_driver_module_v1_spec.md",
        "docs/04_hardware/prototype/validation_plan.md",
        "docs/04_hardware/sensor_specifications.md",
        "docs/04_hardware/v1_hardware_validation_record.md",
        "docs/04_hardware/v1_hardware_validation_runbook.md",
        "docs/04_hardware/validation_logs/V1_RUN_001.md",
        "docs/04_hardware/validation_logs/V1_RUN_002.md",
        "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
        "docs/05_firmware/firmware_api_spec.md",
        "docs/05_firmware/node_firmware_specification.md",
        "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md",
        "docs/09_logs/MG-LOG-APP-044_access_validation_log_template.md",
        "docs/09_logs/MG-LOG-APP-060_ota_v1_usb_validation.md",
        "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/09_ACCEPTANCE_TESTS.md",
        "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/03_FSD_BLE_GATT_SPEC.md",
        "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/08_FSD_TEST_PLAN.md",
        "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md"
      ],
      "name": "testing",
      "score": 92,
      "weight": 15
    },
    {
      "evidence": [
        "AGENTS.md",
        "CHANGELOG.md",
        "CODEX_INSTALL_PROMPT.md",
        "CODEX_MERGE_SAFE_PROMPT.md",
        "INSTALL_INTO_REPO.md",
        "INSTALL_INTO_REPO_SAFE_NO_OVERWRITE.md",
        "MICROGROW_RND_ROADMAP.md",
        "PACK_MANIFEST.md",
        "README.md",
        "README_EXPERIMENTS.md",
        "REPO_CONTEXT.md",
        "ROADMAP.md",
        "What\u2019s active now vs parked for later.txt",
        "ai/codex_prompts/espnow_gateway_to_data_bridge_prompt.md",
        "ai/codex_prompts/espnow_lab_integration_prompt.md",
        "assets/branding/README.md",
        "assets/diagrams/README.md",
        "assets/photos/README.md",
        "assets/screenshots/README.md",
        "calibration/reference_measurements/README.md"
      ],
      "name": "documentation",
      "score": 100,
      "weight": 10
    },
    {
      "evidence": [
        "CHANGELOG.md",
        "docs/10_roadmap/release_candidate_burn_in_checklist.md",
        "docs/10_roadmap/release_readiness_checklist.md",
        "docs/10_roadmap/v1_0_0_rc1_release_notes.md",
        "docs/10_roadmap/v1_0_0_rc3_release_notes.md",
        "docs/10_roadmap/v1_0_0_rc4_release_notes.md",
        "docs/10_roadmap/v1_0_0_release_notes.md",
        "docs/10_roadmap/v1_0_1_release_notes.md",
        "docs/diagrams/microgrow_release_validation_flow.png",
        "docs/diagrams/source_ai_drafts/microgrow_release_validation_flow.png",
        "docs/project_control/RELEASE_GATES.md",
        "docs/project_control/RELEASE_TRAIN.md",
        "docs/project_control/hardware_validation/HARDWARE_RELEASE_BLOCKERS.md",
        "docs/project_control/release_v1/BACKUP_AND_RECOVERY_GUIDE.md",
        "docs/project_control/release_v1/COMPLETE_SYSTEM_ARCHITECTURE_REVIEW.md",
        "docs/project_control/release_v1/DAILY_OPERATING_GUIDE.md",
        "docs/project_control/release_v1/DATA_AND_EVIDENCE_MODEL.md",
        "docs/project_control/release_v1/INSTALLATION_GUIDE.md",
        "docs/project_control/release_v1/KNOWN_LIMITATIONS.md",
        "docs/project_control/release_v1/MILESTONE_REVIEW_GUIDE.md"
      ],
      "name": "release discipline",
      "score": 100,
      "weight": 10
    },
    {
      "evidence": [
        "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0001-local-first-architecture.md",
        "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0002-one-hub-per-site.md",
        "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0003-pressure-tube-water-level-method.md",
        "D:/Dev/Projects/MicroGrow V1/docs/adr/README.md",
        "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
        "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_Architecture_decision_board.md",
        "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_TEMPLATE.md"
      ],
      "name": "traceability",
      "score": 100,
      "weight": 10
    },
    {
      "evidence": [
        {
          "alternatives": "",
          "confidence": 0.92,
          "consequences": "",
          "context": "",
          "date": null,
          "decision": "",
          "evidence_paths": [
            "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_TEMPLATE.md"
          ],
          "id": "dec-6a17f892cfec83686fee60fb",
          "rationale": "",
          "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR_TEMPLATE.md",
          "status": "accepted",
          "title": "ADR_TEMPLATE"
        },
        {
          "alternatives": "",
          "confidence": 0.92,
          "consequences": "",
          "context": "",
          "date": null,
          "decision": "",
          "evidence_paths": [
            "D:/Dev/Projects/MicroGrow V1/docs/adr/README.md"
          ],
          "id": "dec-5b496ce8cc0ef340108fbf04",
          "rationale": "",
          "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/README.md",
          "status": "accepted",
          "title": "README"
        },
        {
          "alternatives": "",
          "confidence": 0.92,
          "consequences": "This decision allows MicroGrow V1 to move quickly toward a working prototype with minimal implementation overhead.\n\nHowever, this is considered a prototype-stage decision rather than a final platform decision.\n\nFuture versions may migrate toward MQTT or another more scalable communication model as the system expands into distributed multi-node operation.\n\n---",
          "context": "MicroGrow V1 requires communication between the ESP32 node and the Flutter application over a local Wi-Fi network.\n\nAt this stage of development, the primary goal is to achieve a working prototype that supports:\n\n- reading sensor data\n- controlling relays\n- simple debugging\n- straightforward integration with Flutter\n\nThe main options considered for node communication were:\n\n- HTTP REST\n- MQTT\n\n---",
          "date": "2026-03-03",
          "decision": "HTTP REST was selected as the communication model for MicroGrow V1.\n\nThe ESP32 will expose simple local endpoints for data retrieval and relay control, and the Flutter application will interact with these endpoints directly over Wi-Fi.\n\n---",
          "evidence_paths": [
            "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md"
          ],
          "id": "dec-53b22ae52b0c2cf3edd50e13",
          "rationale": "",
          "source_path": "D:/Dev/Projects/MicroGrow V1/engineering_logs/decisions/ADR-0001-api-style.md",
          "status": "accepted",
          "title": "ADR-0001-api-style"
        },
        {
          "alternatives": "",
          "confidence": 0.92,
          "consequences": "Describe benefits, risks, and trade-offs.",
          "context": "Describe the engineering problem.",
          "date": "YYYY-MM-DD",
          "decision": "Describe the chosen approach.",
          "evidence_paths": [
            "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0001-local-first-architecture.md"
          ],
          "id": "dec-a8c82b3f394209e77d292add",
          "rationale": "",
          "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0001-local-first-architecture.md",
          "status": "draft",
          "title": "ADR-0001-local-first-architecture"
        },
        {
          "alternatives": "",
          "confidence": 0.92,
          "consequences": "Describe benefits, risks, and trade-offs.",
          "context": "Describe the engineering problem.",
          "date": "YYYY-MM-DD",
          "decision": "Describe the chosen approach.",
          "evidence_paths": [
            "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0002-one-hub-per-site.md"
          ],
          "id": "dec-d4d54b8abb19febe1965c6e0",
          "rationale": "",
          "source_path": "D:/Dev/Projects/MicroGrow V1/docs/adr/ADR-0002-one-hub-per-site.md",
          "status": "draft",
          "title": "ADR-0002-one-hub-per-site"
        }
      ],
      "name": "engineering decisions",
      "score": 100,
      "weight": 10
    },
    {
      "evidence": [
        "D:/Dev/Projects/MicroGrow V1/.github/workflows/app-ci.yml",
        "D:/Dev/Projects/MicroGrow V1/.github/workflows/commerce-backend-ci.yml",
        "D:/Dev/Projects/MicroGrow V1/.github/workflows/commerce-backend-provider-smoke.yml",
        "D:/Dev/Projects/MicroGrow V1/.github/workflows/firmware-ci.yml",
        "D:/Dev/Projects/MicroGrow V1/config/espnow_lab_config.example.json",
        "D:/Dev/Projects/MicroGrow V1/config/local_settings.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/access_test_account_seed_data.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_pro_active_owner_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_pro_expired_owner_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_pro_grace_owner_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_team_editor_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_team_owner_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_auth_me_team_viewer_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_config_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_crop_profile_catalog_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_crop_profile_entitlements_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_data_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_firmware_capabilities_response.json",
        "D:/Dev/Projects/MicroGrow V1/contracts/api_fixtures/get_firmware_update_status_response.json"
      ],
      "name": "configuration management",
      "score": 100,
      "weight": 5
    },
    {
      "evidence": [
        "ai/codex_prompts/espnow_lab_integration_prompt.md",
        "contracts/api_fixtures/README.md",
        "contracts/api_fixtures/access_test_account_seed_data.json",
        "contracts/api_fixtures/get_auth_me_pro_active_owner_response.json",
        "contracts/api_fixtures/get_auth_me_pro_expired_owner_response.json",
        "contracts/api_fixtures/get_auth_me_pro_grace_owner_response.json",
        "contracts/api_fixtures/get_auth_me_team_editor_response.json",
        "contracts/api_fixtures/get_auth_me_team_owner_response.json",
        "contracts/api_fixtures/get_auth_me_team_viewer_response.json",
        "contracts/api_fixtures/get_config_response.json",
        "contracts/api_fixtures/get_crop_profile_catalog_response.json",
        "contracts/api_fixtures/get_crop_profile_entitlements_response.json",
        "contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json",
        "contracts/api_fixtures/get_data_response.json",
        "contracts/api_fixtures/get_firmware_capabilities_response.json",
        "contracts/api_fixtures/get_firmware_update_status_response.json",
        "contracts/api_fixtures/get_firmware_version_response.json",
        "contracts/api_fixtures/get_info_response.json",
        "contracts/api_fixtures/get_outputs_response.json",
        "contracts/api_fixtures/get_status_response.json"
      ],
      "name": "validation",
      "score": 100,
      "weight": 3
    },
    {
      "evidence": [
        "docs/07_network/ble_provisioning_security_acceptance.md",
        "docs/08_security/README.md",
        "docs/08_security/security_model.md",
        "docs/09_logs/MG-LOG-006_security.md",
        "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/07_FSD_SECURITY_AND_LIMITS.md",
        "docs/10_roadmap/future_platform/dev_control_panel/fsd/05_SECURITY_SAFETY_FSD.md",
        "docs/audit/security/SECURITY_SAFETY_AND_COMPLIANCE_AUDIT.md",
        "docs/project_control/CONTROL_SYSTEM_SECURITY_REVIEW.md",
        "docs/project_control/build_evidence/PHASE_2E_SECURITY_REVIEW.md",
        "docs/project_control/hardware_validation/SECURITY_AND_SAFETY_REVIEW.md",
        "docs/project_control/live_intelligence/SECURITY_REVIEW.md",
        "docs/project_control/release_v1/SECURITY_MODEL.md",
        "docs/project_control/user_guide/SECURITY_MODEL.md",
        "docs/project_control/version_simulator/SECURITY_AND_GOVERNANCE_REVIEW.md",
        "docs/security/07_SECURITY_AND_PERMISSIONS_FSD.md",
        "experiments/security/licence_token_validation/NEXT_STEPS.md",
        "experiments/security/licence_token_validation/README.md",
        "experiments/security/licence_token_validation/RESULTS.md",
        "experiments/security/licence_token_validation/STATUS.md",
        "experiments/security/licence_token_validation/TEST_PLAN.md"
      ],
      "name": "security evidence",
      "score": 100,
      "weight": 2
    }
  ],
  "label": "healthy",
  "score": 946
}
```