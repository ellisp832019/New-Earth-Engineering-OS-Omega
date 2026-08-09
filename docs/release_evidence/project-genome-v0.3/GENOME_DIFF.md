# Genome Diff
Project: `microgrow-v1`
Latest genome: `genome-874beeefe1bcb72981dd5864`
Previous genome: `none`

```json
{
  "changes": {
    "architecture_changes": [],
    "documentation_changes": [],
    "maturity_changes": [],
    "new_features": [
      {
        "confidence": 0.99,
        "feature_id": "feat-f775897b978921d2a59877ac",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "contracts/api_fixtures/access_test_account_seed_data.json"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 1,
              "evidence_paths": [
                "contracts/api_fixtures/README.md"
              ],
              "name": "documentation",
              "ratio": 0.5,
              "score": 8,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 20,
              "evidence_paths": [
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
                "contracts/api_fixtures/get_status_response.json",
                "contracts/api_fixtures/get_subscription_summary_local_response.json"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "validation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "release",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
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
            "contracts/api_fixtures/get_status_response.json",
            "contracts/api_fixtures/get_subscription_summary_local_response.json"
          ],
          "label": "experimental",
          "score": 33,
          "signals": {
            "config_paths": [
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
              "contracts/api_fixtures/get_status_response.json",
              "contracts/api_fixtures/get_subscription_summary_local_response.json"
            ],
            "hardware_paths": [
              "contracts/api_fixtures/get_firmware_capabilities_response.json",
              "contracts/api_fixtures/get_firmware_update_status_response.json",
              "contracts/api_fixtures/get_firmware_version_response.json"
            ]
          }
        },
        "name": "API",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-352f8363d80487a34ac86743",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "experiments/automation/mist_driver/TEST_PLAN.md"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 18,
              "evidence_paths": [
                "docs/04_hardware/relay_control_design.md",
                "docs/09_logs/MG-LOG-APP-007_light_scheduler_and_irrigation_guidance.md",
                "docs/09_logs/MG-LOG-APP-013_relay_command_failure_health.md",
                "docs/09_logs/MG-LOG-APP-014_relay_command_pending_state.md",
                "docs/09_logs/MG-LOG-APP-015_relay_command_failure_feedback.md",
                "docs/10_roadmap/fsd/fsd_003_automation_guardrails.md",
                "docs/10_roadmap/fsd/fsd_006_relay_boot_inhibit_interlock.md",
                "docs/10_roadmap/fsd/reviews/fsd_003_automation_guardrails_review.md",
                "docs/10_roadmap/fsd/tasks/fsd_003_automation_guardrails_tasks.md",
                "docs/10_roadmap/fsd/tasks/fsd_006_relay_boot_inhibit_interlock_tasks.md",
                "docs/diagrams/microgrow_8_relay_expansion_board.png",
                "docs/diagrams/source_ai_drafts/microgrow_relay_control_authority.png",
                "experiments/automation/mist_driver/NEXT_STEPS.md",
                "experiments/automation/mist_driver/README.md",
                "experiments/automation/mist_driver/RESULTS.md",
                "experiments/automation/mist_driver/STATUS.md",
                "experiments/automation/mist_driver/TEST_PLAN.md",
                "experiments/automation/pump_control/NEXT_STEPS.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "contracts/api_fixtures/post_relay_request.json",
                "contracts/api_fixtures/post_relay_response.json"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-APP-013_relay_command_failure_health.md",
                "experiments/automation/mist_driver/RESULTS.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/diagrams/source_ai_drafts/microgrow_relay_control_authority.png"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "contracts/api_fixtures/post_relay_request.json",
            "contracts/api_fixtures/post_relay_response.json",
            "docs/04_hardware/relay_control_design.md",
            "docs/09_logs/MG-LOG-APP-007_light_scheduler_and_irrigation_guidance.md",
            "docs/09_logs/MG-LOG-APP-013_relay_command_failure_health.md",
            "docs/09_logs/MG-LOG-APP-014_relay_command_pending_state.md",
            "docs/09_logs/MG-LOG-APP-015_relay_command_failure_feedback.md",
            "docs/10_roadmap/fsd/fsd_003_automation_guardrails.md",
            "docs/10_roadmap/fsd/fsd_006_relay_boot_inhibit_interlock.md",
            "docs/10_roadmap/fsd/reviews/fsd_003_automation_guardrails_review.md",
            "docs/10_roadmap/fsd/tasks/fsd_003_automation_guardrails_tasks.md",
            "docs/10_roadmap/fsd/tasks/fsd_006_relay_boot_inhibit_interlock_tasks.md",
            "docs/diagrams/microgrow_8_relay_expansion_board.png",
            "docs/diagrams/source_ai_drafts/microgrow_relay_control_authority.png",
            "experiments/automation/mist_driver/NEXT_STEPS.md",
            "experiments/automation/mist_driver/README.md",
            "experiments/automation/mist_driver/RESULTS.md",
            "experiments/automation/mist_driver/STATUS.md",
            "experiments/automation/mist_driver/TEST_PLAN.md",
            "experiments/automation/pump_control/NEXT_STEPS.md"
          ],
          "label": "developing",
          "score": 60,
          "signals": {
            "config_paths": [
              "contracts/api_fixtures/post_relay_request.json",
              "contracts/api_fixtures/post_relay_response.json"
            ],
            "hardware_paths": [
              "contracts/api_fixtures/post_relay_request.json",
              "contracts/api_fixtures/post_relay_response.json",
              "docs/04_hardware/relay_control_design.md",
              "docs/09_logs/MG-LOG-APP-013_relay_command_failure_health.md",
              "docs/09_logs/MG-LOG-APP-014_relay_command_pending_state.md",
              "docs/09_logs/MG-LOG-APP-015_relay_command_failure_feedback.md",
              "docs/10_roadmap/fsd/fsd_006_relay_boot_inhibit_interlock.md",
              "docs/10_roadmap/fsd/tasks/fsd_006_relay_boot_inhibit_interlock_tasks.md",
              "docs/diagrams/microgrow_8_relay_expansion_board.png",
              "docs/diagrams/source_ai_drafts/microgrow_relay_control_authority.png"
            ]
          }
        },
        "name": "Climate Control",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-0e7f17006f8766739a7129cb",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/04_hardware/sensor_specifications.md"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 20,
              "evidence_paths": [
                "assets/photos/README.md",
                "calibration/sensor_offsets/README.md",
                "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
                "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
                "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
                "docs/04_hardware/sensor_arrival_checklist.md",
                "docs/04_hardware/sensor_specifications.md",
                "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
                "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md",
                "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
                "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
                "docs/09_logs/MG-LOG-APP-003_flutter_architecture_refactor_phase3.md",
                "docs/09_logs/MG-LOG-APP-004_flutter_architecture_refactor_phase4.md",
                "docs/09_logs/MG-LOG-APP-005_flutter_architecture_refactor_phase5.md",
                "docs/09_logs/MG-LOG-APP-007_light_scheduler_and_irrigation_guidance.md",
                "docs/09_logs/MG-LOG-APP-011_sensor_health_capability_panel.md",
                "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md",
                "docs/09_logs/MG-LOG-APP-022_sensor_screen_and_sidebar_route.md",
                "docs/09_logs/MG-LOG-APP-025_sensors_recommended_action.md",
                "docs/10_roadmap/v1_physical_product_evidence_matrix.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 5,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
                "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
                "docs/09_logs/MG-LOG-APP-003_flutter_architecture_refactor_phase3.md",
                "docs/09_logs/MG-LOG-APP-004_flutter_architecture_refactor_phase4.md",
                "docs/09_logs/MG-LOG-APP-005_flutter_architecture_refactor_phase5.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/04_hardware/sensor_arrival_checklist.md",
                "docs/09_logs/MG-LOG-APP-011_sensor_health_capability_panel.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 5,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
                "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
                "docs/09_logs/MG-LOG-APP-003_flutter_architecture_refactor_phase3.md",
                "docs/09_logs/MG-LOG-APP-004_flutter_architecture_refactor_phase4.md",
                "docs/09_logs/MG-LOG-APP-005_flutter_architecture_refactor_phase5.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "assets/photos/README.md",
            "calibration/sensor_offsets/README.md",
            "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
            "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
            "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
            "docs/04_hardware/sensor_arrival_checklist.md",
            "docs/04_hardware/sensor_specifications.md",
            "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
            "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md",
            "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
            "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
            "docs/09_logs/MG-LOG-APP-003_flutter_architecture_refactor_phase3.md",
            "docs/09_logs/MG-LOG-APP-004_flutter_architecture_refactor_phase4.md",
            "docs/09_logs/MG-LOG-APP-005_flutter_architecture_refactor_phase5.md",
            "docs/09_logs/MG-LOG-APP-007_light_scheduler_and_irrigation_guidance.md",
            "docs/09_logs/MG-LOG-APP-011_sensor_health_capability_panel.md",
            "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md",
            "docs/09_logs/MG-LOG-APP-022_sensor_screen_and_sidebar_route.md",
            "docs/09_logs/MG-LOG-APP-025_sensors_recommended_action.md",
            "docs/10_roadmap/v1_physical_product_evidence_matrix.md"
          ],
          "label": "developing",
          "score": 60,
          "signals": {
            "config_paths": [],
            "hardware_paths": [
              "calibration/sensor_offsets/README.md",
              "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
              "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
              "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
              "docs/04_hardware/sensor_arrival_checklist.md",
              "docs/04_hardware/sensor_specifications.md",
              "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
              "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md",
              "docs/09_logs/MG-LOG-APP-011_sensor_health_capability_panel.md",
              "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md",
              "docs/09_logs/MG-LOG-APP-022_sensor_screen_and_sidebar_route.md",
              "docs/09_logs/MG-LOG-APP-025_sensors_recommended_action.md"
            ]
          }
        },
        "name": "Climate Sensing",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-ff62c2e79b2cda70c977cc3b",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 3,
              "evidence_paths": [
                "experiments/espnow_lab/2026-06-03_first_test_template.md",
                "experiments/espnow_lab/TEST_PLAN.md",
                "experiments/networking/wifi_lan_discovery/TEST_PLAN.md"
              ],
              "name": "testing",
              "ratio": 1.0,
              "score": 20,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 18,
              "evidence_paths": [
                "ai/codex_prompts/espnow_gateway_to_data_bridge_prompt.md",
                "ai/codex_prompts/espnow_lab_integration_prompt.md",
                "diagnostics/espnow_lab_logs/README.md",
                "docs/05_firmware/espnow_lab_architecture.md",
                "docs/10_roadmap/fsd/fsd_005_local_node_discovery.md",
                "docs/10_roadmap/fsd/tasks/fsd_005_local_node_discovery_tasks.md",
                "experiments/espnow_lab/2026-06-03_first_test_template.md",
                "experiments/espnow_lab/NEXT_STEPS.md",
                "experiments/espnow_lab/README.md",
                "experiments/espnow_lab/STATUS.md",
                "experiments/espnow_lab/TEST_PLAN.md",
                "experiments/networking/wifi_lan_discovery/NEXT_STEPS.md",
                "experiments/networking/wifi_lan_discovery/README.md",
                "experiments/networking/wifi_lan_discovery/RESULTS.md",
                "experiments/networking/wifi_lan_discovery/STATUS.md",
                "experiments/networking/wifi_lan_discovery/TEST_PLAN.md",
                "experiments/security/node_pairing_secret/NEXT_STEPS.md",
                "experiments/security/node_pairing_secret/README.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "integration",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 1,
              "evidence_paths": [
                "experiments/networking/wifi_lan_discovery/RESULTS.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/05_firmware/espnow_lab_architecture.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "ai/codex_prompts/espnow_gateway_to_data_bridge_prompt.md",
            "ai/codex_prompts/espnow_lab_integration_prompt.md",
            "config/espnow_lab_config.example.json",
            "diagnostics/espnow_lab_logs/README.md",
            "docs/05_firmware/espnow_lab_architecture.md",
            "docs/10_roadmap/fsd/fsd_005_local_node_discovery.md",
            "docs/10_roadmap/fsd/tasks/fsd_005_local_node_discovery_tasks.md",
            "experiments/espnow_lab/2026-06-03_first_test_template.md",
            "experiments/espnow_lab/NEXT_STEPS.md",
            "experiments/espnow_lab/README.md",
            "experiments/espnow_lab/STATUS.md",
            "experiments/espnow_lab/TEST_PLAN.md",
            "experiments/networking/wifi_lan_discovery/NEXT_STEPS.md",
            "experiments/networking/wifi_lan_discovery/README.md",
            "experiments/networking/wifi_lan_discovery/RESULTS.md",
            "experiments/networking/wifi_lan_discovery/STATUS.md",
            "experiments/networking/wifi_lan_discovery/TEST_PLAN.md",
            "experiments/networking/wifi_lan_discovery/experiment.json",
            "experiments/security/node_pairing_secret/NEXT_STEPS.md",
            "experiments/security/node_pairing_secret/README.md"
          ],
          "label": "developing",
          "score": 55,
          "signals": {
            "config_paths": [
              "config/espnow_lab_config.example.json",
              "experiments/networking/wifi_lan_discovery/experiment.json"
            ],
            "hardware_paths": [
              "docs/05_firmware/espnow_lab_architecture.md"
            ]
          }
        },
        "name": "Device Discovery",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-8210a0bc2e6b06af23080c5c",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "testing",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 17,
              "evidence_paths": [
                "calibration/tank_profiles/README.md",
                "docs/02_product/crop_profile_marketplace.md",
                "docs/03_architecture/crop_profile_commerce_backend_deployment.md",
                "docs/03_architecture/crop_profile_marketplace_backend.md",
                "docs/10_roadmap/fsd/fsd_007_crop_profiles.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_app_data_model_tasks.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_flutter_mapping.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_implementation_board.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_implementation_checklist.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_schema.md",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_template.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_catalog_choices.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_system_focus.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_system_next_5_tasks_board.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_system_weekly_action_checklist.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_system_weekly_action_sheet.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 4,
              "evidence_paths": [
                "contracts/api_fixtures/get_crop_profile_catalog_response.json",
                "contracts/api_fixtures/get_crop_profile_entitlements_response.json",
                "contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json",
                "docs/10_roadmap/microgrow_crop_profile_first_wave_flutter_mapping.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/10_roadmap/microgrow_crop_profile_first_wave_implementation_checklist.md",
                "docs/10_roadmap/microgrow_crop_profile_pack_system_weekly_action_checklist.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/03_architecture/crop_profile_commerce_backend_deployment.md",
                "docs/03_architecture/crop_profile_marketplace_backend.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "calibration/tank_profiles/README.md",
            "contracts/api_fixtures/get_crop_profile_catalog_response.json",
            "contracts/api_fixtures/get_crop_profile_entitlements_response.json",
            "contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json",
            "docs/02_product/crop_profile_marketplace.md",
            "docs/03_architecture/crop_profile_commerce_backend_deployment.md",
            "docs/03_architecture/crop_profile_marketplace_backend.md",
            "docs/10_roadmap/fsd/fsd_007_crop_profiles.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_app_data_model_tasks.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_flutter_mapping.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_implementation_board.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_implementation_checklist.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_schema.md",
            "docs/10_roadmap/microgrow_crop_profile_first_wave_template.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_catalog_choices.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_first_wave_lineup.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_system_focus.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_system_next_5_tasks_board.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_system_weekly_action_checklist.md",
            "docs/10_roadmap/microgrow_crop_profile_pack_system_weekly_action_sheet.md"
          ],
          "label": "developing",
          "score": 50,
          "signals": {
            "config_paths": [
              "contracts/api_fixtures/get_crop_profile_catalog_response.json",
              "contracts/api_fixtures/get_crop_profile_entitlements_response.json",
              "contracts/api_fixtures/get_crop_profile_package_tomato_pro_response.json"
            ],
            "hardware_paths": [
              "calibration/tank_profiles/README.md"
            ]
          }
        },
        "name": "Device Profiles",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-4c56e84da9d36bd6af4de157",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 20,
              "evidence_paths": [
                "datasets/node_health/README.md",
                "diagnostics/espnow_lab_logs/README.md",
                "docs/00_master_index/developer_diagnostics_workflow.md",
                "docs/04_hardware/validation_logs/V1_RUN_001.md",
                "docs/04_hardware/validation_logs/V1_RUN_002.md",
                "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
                "docs/09_logs/MG-LOG-000_project_genesis.md",
                "docs/09_logs/MG-LOG-0011_dev_pipeline.md",
                "docs/09_logs/MG-LOG-001_firmware.md",
                "docs/09_logs/MG-LOG-002_flutter_app.md",
                "docs/09_logs/MG-LOG-003_architecture.md",
                "docs/09_logs/MG-LOG-004_dev_environment.md",
                "docs/09_logs/MG-LOG-005_networking_api.md",
                "docs/09_logs/MG-LOG-006_security.md",
                "docs/09_logs/MG-LOG-007_hardware.md",
                "docs/09_logs/MG-LOG-008_repository_cicd.md",
                "docs/09_logs/MG-LOG-009_architecture_documentation.md",
                "docs/09_logs/MG-LOG-010_firmware_source_layout_refactor.md",
                "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md",
                "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-002_flutter_app.md",
                "docs/09_logs/MG-LOG-005_networking_api.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 4,
              "evidence_paths": [
                "datasets/node_health/README.md",
                "docs/04_hardware/validation_logs/V1_RUN_001.md",
                "docs/04_hardware/validation_logs/V1_RUN_002.md",
                "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 3,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-003_architecture.md",
                "docs/09_logs/MG-LOG-009_architecture_documentation.md",
                "docs/09_logs/MG-LOG-010_firmware_source_layout_refactor.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "datasets/node_health/README.md",
            "diagnostics/espnow_lab_logs/README.md",
            "docs/00_master_index/developer_diagnostics_workflow.md",
            "docs/04_hardware/validation_logs/V1_RUN_001.md",
            "docs/04_hardware/validation_logs/V1_RUN_002.md",
            "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
            "docs/09_logs/MG-LOG-000_project_genesis.md",
            "docs/09_logs/MG-LOG-0011_dev_pipeline.md",
            "docs/09_logs/MG-LOG-001_firmware.md",
            "docs/09_logs/MG-LOG-002_flutter_app.md",
            "docs/09_logs/MG-LOG-003_architecture.md",
            "docs/09_logs/MG-LOG-004_dev_environment.md",
            "docs/09_logs/MG-LOG-005_networking_api.md",
            "docs/09_logs/MG-LOG-006_security.md",
            "docs/09_logs/MG-LOG-007_hardware.md",
            "docs/09_logs/MG-LOG-008_repository_cicd.md",
            "docs/09_logs/MG-LOG-009_architecture_documentation.md",
            "docs/09_logs/MG-LOG-010_firmware_source_layout_refactor.md",
            "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md",
            "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md"
          ],
          "label": "developing",
          "score": 60,
          "signals": {
            "config_paths": [],
            "hardware_paths": [
              "docs/04_hardware/validation_logs/V1_RUN_001.md",
              "docs/04_hardware/validation_logs/V1_RUN_002.md",
              "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
              "docs/09_logs/MG-LOG-001_firmware.md",
              "docs/09_logs/MG-LOG-007_hardware.md",
              "docs/09_logs/MG-LOG-010_firmware_source_layout_refactor.md",
              "docs/09_logs/MG-LOG-012_veml7700_light_sensor.md"
            ]
          }
        },
        "name": "Diagnostics",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-995d0278c2302f7aaf5dbeef",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/05_firmware/firmware_api_spec.md"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 15,
              "evidence_paths": [
                "docs/03_architecture/diagrams/firmware_architecture_v1.png",
                "docs/03_architecture/diagrams/firmware_module_architecture.png",
                "docs/03_architecture/diagrams/firmware_startup_flow.png",
                "docs/03_architecture/firmware_architecture.md",
                "docs/03_architecture/firmware_freertos_adoption_note.md",
                "docs/05_firmware/README.md",
                "docs/05_firmware/api_sequence_diagram.md",
                "docs/05_firmware/dev_cheat_sheet.md",
                "docs/05_firmware/dev_cheat_sheet_image_prompt.md",
                "docs/05_firmware/dev_environment.md",
                "docs/05_firmware/espnow_lab_architecture.md",
                "docs/05_firmware/firmware_api_spec.md",
                "docs/05_firmware/firmware_hardware_integration.md",
                "docs/05_firmware/firmware_module_map.md",
                "docs/05_firmware/firmware_notes.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 6,
              "evidence_paths": [
                ".github/workflows/firmware-ci.yml",
                "contracts/api_fixtures/get_firmware_capabilities_response.json",
                "contracts/api_fixtures/get_firmware_update_status_response.json",
                "contracts/api_fixtures/get_firmware_version_response.json",
                "docs/05_firmware/api_sequence_diagram.md",
                "docs/05_firmware/firmware_api_spec.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "validation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 7,
              "evidence_paths": [
                "architecture/v1_node/firmware_module_interaction.png",
                "docs/03_architecture/diagrams/firmware_architecture_v1.png",
                "docs/03_architecture/diagrams/firmware_module_architecture.png",
                "docs/03_architecture/diagrams/firmware_startup_flow.png",
                "docs/03_architecture/firmware_architecture.md",
                "docs/03_architecture/firmware_freertos_adoption_note.md",
                "docs/05_firmware/espnow_lab_architecture.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            ".github/workflows/firmware-ci.yml",
            "architecture/v1_node/firmware_module_interaction.png",
            "contracts/api_fixtures/get_firmware_capabilities_response.json",
            "contracts/api_fixtures/get_firmware_update_status_response.json",
            "contracts/api_fixtures/get_firmware_version_response.json",
            "docs/03_architecture/diagrams/firmware_architecture_v1.png",
            "docs/03_architecture/diagrams/firmware_module_architecture.png",
            "docs/03_architecture/diagrams/firmware_startup_flow.png",
            "docs/03_architecture/firmware_architecture.md",
            "docs/03_architecture/firmware_freertos_adoption_note.md",
            "docs/05_firmware/README.md",
            "docs/05_firmware/api_sequence_diagram.md",
            "docs/05_firmware/dev_cheat_sheet.md",
            "docs/05_firmware/dev_cheat_sheet_image_prompt.md",
            "docs/05_firmware/dev_environment.md",
            "docs/05_firmware/espnow_lab_architecture.md",
            "docs/05_firmware/firmware_api_spec.md",
            "docs/05_firmware/firmware_hardware_integration.md",
            "docs/05_firmware/firmware_module_map.md",
            "docs/05_firmware/firmware_notes.md"
          ],
          "label": "developing",
          "score": 50,
          "signals": {
            "config_paths": [
              ".github/workflows/firmware-ci.yml",
              "contracts/api_fixtures/get_firmware_capabilities_response.json",
              "contracts/api_fixtures/get_firmware_update_status_response.json",
              "contracts/api_fixtures/get_firmware_version_response.json"
            ],
            "hardware_paths": [
              ".github/workflows/firmware-ci.yml",
              "architecture/v1_node/firmware_module_interaction.png",
              "contracts/api_fixtures/get_firmware_capabilities_response.json",
              "contracts/api_fixtures/get_firmware_update_status_response.json",
              "contracts/api_fixtures/get_firmware_version_response.json",
              "docs/03_architecture/diagrams/firmware_architecture_v1.png",
              "docs/03_architecture/diagrams/firmware_module_architecture.png",
              "docs/03_architecture/diagrams/firmware_startup_flow.png",
              "docs/03_architecture/firmware_architecture.md",
              "docs/03_architecture/firmware_freertos_adoption_note.md",
              "docs/05_firmware/README.md",
              "docs/05_firmware/api_sequence_diagram.md",
              "docs/05_firmware/dev_cheat_sheet.md",
              "docs/05_firmware/dev_cheat_sheet_image_prompt.md",
              "docs/05_firmware/dev_environment.md",
              "docs/05_firmware/espnow_lab_architecture.md",
              "docs/05_firmware/firmware_api_spec.md",
              "docs/05_firmware/firmware_hardware_integration.md",
              "docs/05_firmware/firmware_module_map.md",
              "docs/05_firmware/firmware_notes.md"
            ]
          }
        },
        "name": "Firmware",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-3f28cf38c62cd0f4b2b1a659",
        "maturity": {
          "components": [
            {
              "count": 16,
              "evidence_paths": [
                "services/crop_profile_commerce_backend/lib/crop_profile_commerce_backend.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_catalog_loader.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_database.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_options.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_package_verifier.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_seed_data.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_service.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_state.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_billing_provider.dart",
                "software/flutter_app/.flutter-plugins-dependencies",
                "software/flutter_app/.gitignore",
                "software/flutter_app/.metadata",
                "software/flutter_app/README.md",
                "software/flutter_app/analysis_options.yaml",
                "software/flutter_app/devtools_options.yaml",
                "software/flutter_app/flutter-architecture.png"
              ],
              "name": "implementation",
              "ratio": 1.0,
              "score": 30,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "services/crop_profile_commerce_backend/pubspec.yaml"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 4,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-002_flutter_app.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/06_FSD_FLUTTER_APP_PROVISIONING_FLOW.md",
                "docs/10_roadmap/future_platform/local_hub/05_FLUTTER_APP_INTEGRATION_FSD.md",
                "software/flutter_app/README.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 11,
              "evidence_paths": [
                "docs/09_logs/MG-LOG-002_flutter_app.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/06_FSD_FLUTTER_APP_PROVISIONING_FLOW.md",
                "docs/10_roadmap/future_platform/local_hub/05_FLUTTER_APP_INTEGRATION_FSD.md",
                "services/crop_profile_commerce_backend/pubspec.yaml",
                "software/flutter_app/.flutter-plugins-dependencies",
                "software/flutter_app/.gitignore",
                "software/flutter_app/.metadata",
                "software/flutter_app/README.md",
                "software/flutter_app/analysis_options.yaml",
                "software/flutter_app/devtools_options.yaml",
                "software/flutter_app/flutter-architecture.png"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "validation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 11,
              "evidence_paths": [
                "services/crop_profile_commerce_backend/lib/crop_profile_commerce_backend.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_catalog_loader.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_database.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_options.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_package_verifier.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_seed_data.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_service.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_backend_state.dart",
                "services/crop_profile_commerce_backend/lib/src/commerce_billing_provider.dart",
                "services/crop_profile_commerce_backend/pubspec.yaml",
                "software/flutter_app/flutter-architecture.png"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "docs/09_logs/MG-LOG-002_flutter_app.md",
            "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/06_FSD_FLUTTER_APP_PROVISIONING_FLOW.md",
            "docs/10_roadmap/future_platform/local_hub/05_FLUTTER_APP_INTEGRATION_FSD.md",
            "services/crop_profile_commerce_backend/lib/crop_profile_commerce_backend.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_catalog_loader.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_database.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_options.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_package_verifier.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_seed_data.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_service.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_backend_state.dart",
            "services/crop_profile_commerce_backend/lib/src/commerce_billing_provider.dart",
            "services/crop_profile_commerce_backend/pubspec.yaml",
            "software/flutter_app/.flutter-plugins-dependencies",
            "software/flutter_app/.gitignore",
            "software/flutter_app/.metadata",
            "software/flutter_app/README.md",
            "software/flutter_app/analysis_options.yaml",
            "software/flutter_app/devtools_options.yaml",
            "software/flutter_app/flutter-architecture.png"
          ],
          "label": "maturing",
          "score": 80,
          "signals": {
            "config_paths": [
              "services/crop_profile_commerce_backend/pubspec.yaml",
              "software/flutter_app/analysis_options.yaml",
              "software/flutter_app/devtools_options.yaml"
            ],
            "hardware_paths": []
          }
        },
        "name": "Flutter Application",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-788a13b593018923769b94c1",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "testing",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 20,
              "evidence_paths": [
                "calibration/reference_measurements/README.md",
                "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md",
                "calibration/sensor_offsets/README.md",
                "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
                "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
                "calibration/tank_profiles/README.md",
                "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
                "docs/04_hardware/prototype/images/rev_b_bench_layout.png",
                "docs/04_hardware/prototype/rev_b_bench_checklist.md",
                "docs/04_hardware/prototype/rev_b_bench_layout.md",
                "docs/04_hardware/prototype/validation_plan.md",
                "docs/04_hardware/v1_hardware_validation_record.md",
                "docs/04_hardware/v1_hardware_validation_runbook.md",
                "docs/04_hardware/validation_logs/V1_RUN_001.md",
                "docs/04_hardware/validation_logs/V1_RUN_002.md",
                "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
                "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
                "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md",
                "docs/09_logs/MG-LOG-APP-044_access_validation_log_template.md",
                "docs/09_logs/MG-LOG-APP-060_ota_v1_usb_validation.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "integration",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 9,
              "evidence_paths": [
                "docs/04_hardware/prototype/rev_b_bench_checklist.md",
                "docs/04_hardware/prototype/validation_plan.md",
                "docs/04_hardware/v1_hardware_validation_record.md",
                "docs/04_hardware/v1_hardware_validation_runbook.md",
                "docs/04_hardware/validation_logs/V1_RUN_001.md",
                "docs/04_hardware/validation_logs/V1_RUN_002.md",
                "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
                "docs/09_logs/MG-LOG-APP-044_access_validation_log_template.md",
                "docs/09_logs/MG-LOG-APP-060_ota_v1_usb_validation.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "release",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "calibration/reference_measurements/README.md",
            "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md",
            "calibration/sensor_offsets/README.md",
            "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
            "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
            "calibration/tank_profiles/README.md",
            "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
            "docs/04_hardware/prototype/images/rev_b_bench_layout.png",
            "docs/04_hardware/prototype/rev_b_bench_checklist.md",
            "docs/04_hardware/prototype/rev_b_bench_layout.md",
            "docs/04_hardware/prototype/validation_plan.md",
            "docs/04_hardware/v1_hardware_validation_record.md",
            "docs/04_hardware/v1_hardware_validation_runbook.md",
            "docs/04_hardware/validation_logs/V1_RUN_001.md",
            "docs/04_hardware/validation_logs/V1_RUN_002.md",
            "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
            "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
            "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md",
            "docs/09_logs/MG-LOG-APP-044_access_validation_log_template.md",
            "docs/09_logs/MG-LOG-APP-060_ota_v1_usb_validation.md"
          ],
          "label": "experimental",
          "score": 25,
          "signals": {
            "config_paths": [],
            "hardware_paths": [
              "calibration/reference_measurements/README.md",
              "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md",
              "calibration/sensor_offsets/README.md",
              "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
              "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
              "calibration/tank_profiles/README.md",
              "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
              "docs/04_hardware/prototype/images/rev_b_bench_layout.png",
              "docs/04_hardware/prototype/rev_b_bench_checklist.md",
              "docs/04_hardware/prototype/rev_b_bench_layout.md",
              "docs/04_hardware/prototype/validation_plan.md",
              "docs/04_hardware/v1_hardware_validation_record.md",
              "docs/04_hardware/v1_hardware_validation_runbook.md",
              "docs/04_hardware/validation_logs/V1_RUN_001.md",
              "docs/04_hardware/validation_logs/V1_RUN_002.md",
              "docs/04_hardware/validation_logs/V1_RUN_TEMPLATE.md",
              "docs/04_hardware/veml7700_light_sensor_bench_plan.md",
              "docs/09_logs/MG-LOG-APP-012_sensor_setup_and_calibration_entry_points.md"
            ]
          }
        },
        "name": "Hardware Validation",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-6bd78a55b04afdb2036a402f",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "testing",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 20,
              "evidence_paths": [
                "docs/project_control/CHANGE_CONTROL.md",
                "docs/project_control/CONTROL_DASHBOARD.md",
                "docs/project_control/CONTROL_SYSTEM_SECURITY_REVIEW.md",
                "docs/project_control/CURRENT_POSITION.md",
                "docs/project_control/DECISION_LOG.md",
                "docs/project_control/FEATURE_STATUS.md",
                "docs/project_control/GLOSSARY.md",
                "docs/project_control/HARDWARE_VALIDATION_STATUS.md",
                "docs/project_control/MASTER_ROADMAP.md",
                "docs/project_control/MILESTONE_STATUS.md",
                "docs/project_control/NEXT_ACTIONS.md",
                "docs/project_control/OWNER_OPERATING_GUIDE.md",
                "docs/project_control/RELEASE_GATES.md",
                "docs/project_control/RELEASE_TRAIN.md",
                "docs/project_control/RISK_STATUS.md",
                "docs/project_control/SOURCE_TRACEABILITY.md",
                "docs/project_control/START_HERE.md",
                "docs/project_control/SUBSYSTEM_STATUS.md",
                "docs/project_control/VALIDATION_STATUS.md",
                "docs/project_control/VERSION_DIRECTION.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 20,
              "evidence_paths": [
                "docs/project_control/CHANGE_CONTROL.md",
                "docs/project_control/CONTROL_DASHBOARD.md",
                "docs/project_control/CONTROL_SYSTEM_SECURITY_REVIEW.md",
                "docs/project_control/CURRENT_POSITION.md",
                "docs/project_control/DECISION_LOG.md",
                "docs/project_control/FEATURE_STATUS.md",
                "docs/project_control/GLOSSARY.md",
                "docs/project_control/HARDWARE_VALIDATION_STATUS.md",
                "docs/project_control/MASTER_ROADMAP.md",
                "docs/project_control/MILESTONE_STATUS.md",
                "docs/project_control/NEXT_ACTIONS.md",
                "docs/project_control/OWNER_OPERATING_GUIDE.md",
                "docs/project_control/RELEASE_GATES.md",
                "docs/project_control/RELEASE_TRAIN.md",
                "docs/project_control/RISK_STATUS.md",
                "docs/project_control/SOURCE_TRACEABILITY.md",
                "docs/project_control/START_HERE.md",
                "docs/project_control/SUBSYSTEM_STATUS.md",
                "docs/project_control/VALIDATION_STATUS.md",
                "docs/project_control/VERSION_DIRECTION.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 2,
              "evidence_paths": [
                "docs/project_control/HARDWARE_VALIDATION_STATUS.md",
                "docs/project_control/VALIDATION_STATUS.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 3,
              "evidence_paths": [
                "docs/project_control/RELEASE_GATES.md",
                "docs/project_control/RELEASE_TRAIN.md",
                "docs/project_control/SOURCE_TRACEABILITY.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "docs/project_control/CHANGE_CONTROL.md",
            "docs/project_control/CONTROL_DASHBOARD.md",
            "docs/project_control/CONTROL_SYSTEM_SECURITY_REVIEW.md",
            "docs/project_control/CURRENT_POSITION.md",
            "docs/project_control/DECISION_LOG.md",
            "docs/project_control/FEATURE_STATUS.md",
            "docs/project_control/GLOSSARY.md",
            "docs/project_control/HARDWARE_VALIDATION_STATUS.md",
            "docs/project_control/MASTER_ROADMAP.md",
            "docs/project_control/MILESTONE_STATUS.md",
            "docs/project_control/NEXT_ACTIONS.md",
            "docs/project_control/OWNER_OPERATING_GUIDE.md",
            "docs/project_control/RELEASE_GATES.md",
            "docs/project_control/RELEASE_TRAIN.md",
            "docs/project_control/RISK_STATUS.md",
            "docs/project_control/SOURCE_TRACEABILITY.md",
            "docs/project_control/START_HERE.md",
            "docs/project_control/SUBSYSTEM_STATUS.md",
            "docs/project_control/VALIDATION_STATUS.md",
            "docs/project_control/VERSION_DIRECTION.md"
          ],
          "label": "developing",
          "score": 50,
          "signals": {
            "config_paths": [],
            "hardware_paths": [
              "docs/project_control/HARDWARE_VALIDATION_STATUS.md"
            ]
          }
        },
        "name": "Project Control Centre",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-23f809db86bbeebeb78e3814",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "testing",
              "ratio": 0.0,
              "score": 0,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 20,
              "evidence_paths": [
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
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 10,
              "evidence_paths": [
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
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 5,
              "evidence_paths": [
                "docs/10_roadmap/release_candidate_burn_in_checklist.md",
                "docs/10_roadmap/release_readiness_checklist.md",
                "docs/diagrams/microgrow_release_validation_flow.png",
                "docs/diagrams/source_ai_drafts/microgrow_release_validation_flow.png",
                "docs/project_control/hardware_validation/HARDWARE_RELEASE_BLOCKERS.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 20,
              "evidence_paths": [
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
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
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
          "label": "developing",
          "score": 50,
          "signals": {
            "config_paths": [],
            "hardware_paths": [
              "docs/project_control/hardware_validation/HARDWARE_RELEASE_BLOCKERS.md"
            ]
          }
        },
        "name": "Releases",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.95,
        "feature_id": "feat-1da7afc0a31b13a4366e1827",
        "maturity": {
          "components": [
            {
              "count": 0,
              "evidence_paths": [],
              "name": "implementation",
              "ratio": 0.0,
              "score": 0,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 1,
              "evidence_paths": [
                "experiments/vision/plant_scanner/TEST_PLAN.md"
              ],
              "name": "testing",
              "ratio": 0.5,
              "score": 10,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 7,
              "evidence_paths": [
                "REPO_CONTEXT.md",
                "docs/project_control/user_guide/REPOSITORY_INTELLIGENCE_GUIDE.md",
                "experiments/vision/plant_scanner/NEXT_STEPS.md",
                "experiments/vision/plant_scanner/README.md",
                "experiments/vision/plant_scanner/RESULTS.md",
                "experiments/vision/plant_scanner/STATUS.md",
                "experiments/vision/plant_scanner/TEST_PLAN.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/project_control/user_guide/REPOSITORY_INTELLIGENCE_GUIDE.md"
              ],
              "name": "integration",
              "ratio": 0.5,
              "score": 8,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 1,
              "evidence_paths": [
                "experiments/vision/plant_scanner/RESULTS.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 0,
              "evidence_paths": [],
              "name": "release",
              "ratio": 0.0,
              "score": 0,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "REPO_CONTEXT.md",
            "docs/project_control/user_guide/REPOSITORY_INTELLIGENCE_GUIDE.md",
            "experiments/vision/plant_scanner/NEXT_STEPS.md",
            "experiments/vision/plant_scanner/README.md",
            "experiments/vision/plant_scanner/RESULTS.md",
            "experiments/vision/plant_scanner/STATUS.md",
            "experiments/vision/plant_scanner/TEST_PLAN.md",
            "tools/dev/update_repo_context.ps1"
          ],
          "label": "developing",
          "score": 43,
          "signals": {
            "config_paths": [],
            "hardware_paths": []
          }
        },
        "name": "Repository Intelligence",
        "source": "heuristic",
        "status": "candidate"
      },
      {
        "confidence": 0.99,
        "feature_id": "feat-f1373e78819ccef2774d5d48",
        "maturity": {
          "components": [
            {
              "count": 1,
              "evidence_paths": [
                "docs/audit/deep_verification/VERIFIED_TEST_MATRIX.csv"
              ],
              "name": "implementation",
              "ratio": 0.333,
              "score": 10,
              "threshold": 3,
              "weight": 30
            },
            {
              "count": 20,
              "evidence_paths": [
                "contracts/api_fixtures/access_test_account_seed_data.json",
                "docs/02_product/system_specification.md",
                "docs/03_architecture/microgrow_node_specification.md",
                "docs/04_hardware/mist_driver_module_v1_spec.md",
                "docs/04_hardware/sensor_specifications.md",
                "docs/05_firmware/firmware_api_spec.md",
                "docs/05_firmware/node_firmware_specification.md",
                "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md",
                "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/09_ACCEPTANCE_TESTS.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/03_FSD_BLE_GATT_SPEC.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/08_FSD_TEST_PLAN.md",
                "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md",
                "docs/10_roadmap/future_platform/dev_control_panel/fsd/06_TESTING_ACCEPTANCE_FSD.md",
                "docs/10_roadmap/microgrow_access_test_account_fixture_catalog.md",
                "docs/10_roadmap/microgrow_access_test_account_matrix.md",
                "docs/10_roadmap/microgrow_access_test_account_qa_checklist.md",
                "docs/10_roadmap/microgrow_access_test_account_run_sheet.md",
                "docs/10_roadmap/microgrow_access_test_account_smoke_test.md",
                "docs/audit/deep_verification/VERIFIED_TEST_MATRIX.csv",
                "docs/hardware/mist_driver/MIST_DRIVER_MODULE_SPEC_v0.1.md"
              ],
              "name": "testing",
              "ratio": 1.0,
              "score": 20,
              "threshold": 2,
              "weight": 20
            },
            {
              "count": 19,
              "evidence_paths": [
                "docs/02_product/system_specification.md",
                "docs/03_architecture/microgrow_node_specification.md",
                "docs/04_hardware/mist_driver_module_v1_spec.md",
                "docs/04_hardware/sensor_specifications.md",
                "docs/05_firmware/firmware_api_spec.md",
                "docs/05_firmware/node_firmware_specification.md",
                "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md",
                "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/09_ACCEPTANCE_TESTS.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/03_FSD_BLE_GATT_SPEC.md",
                "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/08_FSD_TEST_PLAN.md",
                "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md",
                "docs/10_roadmap/future_platform/dev_control_panel/fsd/06_TESTING_ACCEPTANCE_FSD.md",
                "docs/10_roadmap/microgrow_access_test_account_fixture_catalog.md",
                "docs/10_roadmap/microgrow_access_test_account_matrix.md",
                "docs/10_roadmap/microgrow_access_test_account_qa_checklist.md",
                "docs/10_roadmap/microgrow_access_test_account_run_sheet.md",
                "docs/10_roadmap/microgrow_access_test_account_smoke_test.md",
                "docs/audit/deep_verification/VERIFIED_TEST_MATRIX.csv",
                "docs/hardware/mist_driver/MIST_DRIVER_MODULE_SPEC_v0.1.md"
              ],
              "name": "documentation",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 3,
              "evidence_paths": [
                "contracts/api_fixtures/access_test_account_seed_data.json",
                "docs/05_firmware/firmware_api_spec.md",
                "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md"
              ],
              "name": "integration",
              "ratio": 1.0,
              "score": 15,
              "threshold": 2,
              "weight": 15
            },
            {
              "count": 4,
              "evidence_paths": [
                "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/09_ACCEPTANCE_TESTS.md",
                "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md",
                "docs/10_roadmap/future_platform/dev_control_panel/fsd/06_TESTING_ACCEPTANCE_FSD.md",
                "docs/10_roadmap/microgrow_access_test_account_qa_checklist.md"
              ],
              "name": "validation",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            },
            {
              "count": 1,
              "evidence_paths": [
                "docs/03_architecture/microgrow_node_specification.md"
              ],
              "name": "release",
              "ratio": 1.0,
              "score": 10,
              "threshold": 1,
              "weight": 10
            }
          ],
          "evidence_paths": [
            "contracts/api_fixtures/access_test_account_seed_data.json",
            "docs/02_product/system_specification.md",
            "docs/03_architecture/microgrow_node_specification.md",
            "docs/04_hardware/mist_driver_module_v1_spec.md",
            "docs/04_hardware/sensor_specifications.md",
            "docs/05_firmware/firmware_api_spec.md",
            "docs/05_firmware/node_firmware_specification.md",
            "docs/09_logs/MG-LOG-013_mist_driver_module_spec.md",
            "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/09_ACCEPTANCE_TESTS.md",
            "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/03_FSD_BLE_GATT_SPEC.md",
            "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/08_FSD_TEST_PLAN.md",
            "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md",
            "docs/10_roadmap/future_platform/dev_control_panel/fsd/06_TESTING_ACCEPTANCE_FSD.md",
            "docs/10_roadmap/microgrow_access_test_account_fixture_catalog.md",
            "docs/10_roadmap/microgrow_access_test_account_matrix.md",
            "docs/10_roadmap/microgrow_access_test_account_qa_checklist.md",
            "docs/10_roadmap/microgrow_access_test_account_run_sheet.md",
            "docs/10_roadmap/microgrow_access_test_account_smoke_test.md",
            "docs/audit/deep_verification/VERIFIED_TEST_MATRIX.csv",
            "docs/hardware/mist_driver/MIST_DRIVER_MODULE_SPEC_v0.1.md"
          ],
          "label": "maturing",
          "score": 80,
          "signals": {
            "config_paths": [
              "contracts/api_fixtures/access_test_account_seed_data.json"
            ],
            "hardware_paths": [
              "docs/04_hardware/mist_driver_module_v1_spec.md",
              "docs/04_hardware/sensor_specifications.md",
              "docs/05_firmware/firmware_api_spec.md",
              "docs/05_firmware/node_firmware_specification.md",
              "docs/hardware/mist_driver/MIST_DRIVER_MODULE_SPEC_v0.1.md"
            ]
          }
        },
        "name": "Testing",
        "source": "heuristic",
        "status": "candidate"
      }
    ],
    "new_risks": [
      {
        "affected_entities": [
          "feat-8210a0bc2e6b06af23080c5c"
        ],
        "category": "testing gap",
        "confidence": 0.4,
        "evidence": [],
        "id": "risk-4dce8382e2da2dd50a56d66c",
        "reason": "Feature maturity lacks test evidence in the current canonical scan state.",
        "recommended_investigation": "Add or link test evidence for Device Profiles.",
        "severity": "high",
        "title": "Feature without test evidence: Device Profiles"
      }
    ],
    "new_technologies": [
      {
        "category": "language",
        "confidence": 0.99,
        "evidence_paths": [
          "docs/09_logs/MG-LOG-002_flutter_app.md",
          "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/06_FSD_FLUTTER_APP_PROVISIONING_FLOW.md",
          "docs/10_roadmap/future_platform/local_hub/05_FLUTTER_APP_INTEGRATION_FSD.md",
          "services/crop_profile_commerce_backend/bin/commerce_backend_hosted.dart",
          "services/crop_profile_commerce_backend/bin/commerce_backend_seed_catalog.dart",
          "services/crop_profile_commerce_backend/bin/commerce_backend_server.dart",
          "services/crop_profile_commerce_backend/bin/commerce_backend_smoke.dart",
          "services/crop_profile_commerce_backend/lib/crop_profile_commerce_backend.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_catalog_loader.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_database.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_options.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_package_verifier.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_seed_data.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_service.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_backend_state.dart",
          "services/crop_profile_commerce_backend/lib/src/commerce_billing_provider.dart",
          "services/crop_profile_commerce_backend/pubspec.yaml",
          "services/crop_profile_commerce_backend/test/commerce_backend_catalog_loader_test.dart",
          "services/crop_profile_commerce_backend/test/commerce_backend_options_test.dart",
          "services/crop_profile_commerce_backend/test/commerce_backend_service_test.dart"
        ],
        "name": "Dart",
        "source": "path-heuristic",
        "usage_count": 524,
        "version": null
      },
      {
        "category": "embedded platform",
        "confidence": 0.99,
        "evidence_paths": [
          "docs/10_roadmap/future_platform/local_hub/06_ESP32_NODE_INTEGRATION_FSD.md",
          "docs/api/postman/MicroGrow-ESP32.postman_collection.json",
          "experiments/firmware/esp32_dual_core/NEXT_STEPS.md",
          "experiments/firmware/esp32_dual_core/README.md",
          "experiments/firmware/esp32_dual_core/RESULTS.md",
          "experiments/firmware/esp32_dual_core/STATUS.md",
          "experiments/firmware/esp32_dual_core/TEST_PLAN.md",
          "experiments/firmware/esp32_s3_migration/NEXT_STEPS.md",
          "experiments/firmware/esp32_s3_migration/README.md",
          "experiments/firmware/esp32_s3_migration/RESULTS.md",
          "experiments/firmware/esp32_s3_migration/STATUS.md",
          "experiments/firmware/esp32_s3_migration/TEST_PLAN.md",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP32/.esp8266.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP32/DHT_ESP32.ino",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP8266/.esp32.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_Multi_ESP32/.esp8266.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_Multi_ESP32/DHT_Multi_ESP32.ino",
          "firmware/microgrow_node/.pio/libdeps/esp32dev/ArduinoJson/.piopm",
          "firmware/microgrow_node/.pio/libdeps/esp32dev/ArduinoJson/ArduinoJson.h",
          "firmware/microgrow_node/.pio/libdeps/esp32dev/ArduinoJson/LICENSE.txt"
        ],
        "name": "ESP32",
        "source": "manifest+path-heuristic",
        "usage_count": 203,
        "version": null
      },
      {
        "category": "web framework",
        "confidence": 0.99,
        "evidence_paths": [
          "firmware/microgrow_node/comms/api_routes.cpp",
          "firmware/microgrow_node/comms/api_routes.h",
          "software/microgrow_hub/app/routers/__init__.py",
          "software/microgrow_hub/app/routers/auth.py",
          "software/microgrow_hub/app/routers/health.py",
          "software/microgrow_hub/app/routers/nodes.py",
          "software/microgrow_hub/app/routers/ota.py",
          "software/microgrow_hub/app/routers/pairing.py",
          "software/microgrow_hub/app/routers/structure.py",
          "software/microgrow_hub/app/routers/subscription.py"
        ],
        "name": "FastAPI",
        "source": "path-heuristic",
        "usage_count": 10,
        "version": null
      },
      {
        "category": "mobile application framework",
        "confidence": 0.99,
        "evidence_paths": [
          "docs/06_software/flutter_notes.md",
          "docs/09_logs/MG-LOG-002_flutter_app.md",
          "docs/09_logs/MG-LOG-APP-001_flutter_architecture_refactor_phase1.md",
          "docs/09_logs/MG-LOG-APP-002_flutter_architecture_refactor_phase2.md",
          "docs/09_logs/MG-LOG-APP-003_flutter_architecture_refactor_phase3.md",
          "docs/09_logs/MG-LOG-APP-004_flutter_architecture_refactor_phase4.md",
          "docs/09_logs/MG-LOG-APP-005_flutter_architecture_refactor_phase5.md",
          "docs/09_logs/MG-LOG-APP-006_flutter_visual_system_refresh.md",
          "docs/09_logs/MG-LOG-APP-034_flutter_debug_infrastructure.md",
          "docs/10_roadmap/fsd/fsd_017_ble_wifi_provisioning/06_FSD_FLUTTER_APP_PROVISIONING_FLOW.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/01_MASTER_FSD_BACKGROUND_DEBUG_SYSTEM.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/02_FILE_STRUCTURE_AND_INTEGRATION.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/03_DEBUG_CORE_LOGGER_AND_EVENT_BUFFER.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/04_APP_LIFECYCLE_AND_ROUTE_DIAGNOSTICS.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/05_MICROGROW_DOMAIN_DIAGNOSTICS.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/06_DEVELOPER_MODE_DEBUG_CONSOLE_UI.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/07_OPTIONAL_PERSISTENT_DEBUG_LOGS.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/08_ACCEPTANCE_TESTS_AND_DEBUG_CHECKLIST.md",
          "docs/10_roadmap/fsd/fsd_018_flutter_background_debug/09_CODEX_MASTER_PROMPT.md"
        ],
        "name": "Flutter",
        "source": "manifest+path-heuristic",
        "usage_count": 588,
        "version": null
      },
      {
        "category": "ci system",
        "confidence": 0.99,
        "evidence_paths": [
          ".github/workflows/app-ci.yml",
          ".github/workflows/commerce-backend-ci.yml",
          ".github/workflows/commerce-backend-provider-smoke.yml",
          ".github/workflows/firmware-ci.yml",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/.github/workflows/main.yml"
        ],
        "name": "GitHub Actions",
        "source": "manifest+path-heuristic",
        "usage_count": 5,
        "version": null
      },
      {
        "category": "documentation",
        "confidence": 0.99,
        "evidence_paths": [
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
          "ai/codex_prompts/espnow_gateway_to_data_bridge_prompt.md",
          "ai/codex_prompts/espnow_lab_integration_prompt.md",
          "assets/branding/README.md",
          "assets/diagrams/README.md",
          "assets/photos/README.md",
          "assets/screenshots/README.md",
          "calibration/reference_measurements/README.md",
          "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md"
        ],
        "name": "Markdown",
        "source": "manifest+path-heuristic",
        "usage_count": 996,
        "version": null
      },
      {
        "category": "build system",
        "confidence": 0.99,
        "evidence_paths": [
          "docs/project_control/build_evidence/MICROGROW_V1_DIRECT_PLATFORMIO_BUILD_VERIFICATION.md",
          "docs/project_control/work_packages/MICROGROW_V1_PLATFORMIO_BUILD_VERIFICATION.md",
          "firmware/espnow_lab/gateway_receiver/platformio.ini",
          "firmware/espnow_lab/sender_sensor_node/platformio.ini",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/.github/workflows/main.yml",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/.piopm",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/.travis.yml",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/DHTesp.cpp",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/DHTesp.h",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/LICENSE",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/README.md",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP32/.esp8266.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP32/DHT_ESP32.ino",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP8266/.esp32.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_ESP8266/DHT_ESP8266.ino",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_Multi_ESP32/.esp8266.test.skip",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/examples/DHT_Multi_ESP32/DHT_Multi_ESP32.ino",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/keywords.txt",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/library.json",
          "firmware/microgrow_node/.pio/libdeps/dht22_diag/DHT sensor library for ESPx/library.properties"
        ],
        "name": "PlatformIO",
        "source": "manifest+path-heuristic",
        "usage_count": 182,
        "version": null
      },
      {
        "category": "language",
        "confidence": 0.99,
        "evidence_paths": [
          "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/04_FIRMWARE_REQUIREMENTS.md",
          "docs/10_roadmap/fsd/fsd_016_scalable_output_controller/pack/05_APP_DASHBOARD_REQUIREMENTS.md",
          "docs/audit/deep_verification/HARDWARE_VALIDATION_REQUIREMENTS.md",
          "docs/ota/OTA_SAFETY_REQUIREMENTS.md",
          "modules/microgrow_local_ota_module/tools/create_manifest_example.py",
          "software/flutter_app/ios/Flutter/ephemeral/flutter_lldb_helper.py",
          "software/microgrow_hub/app/__init__.py",
          "software/microgrow_hub/app/config.py",
          "software/microgrow_hub/app/database.py",
          "software/microgrow_hub/app/deps.py",
          "software/microgrow_hub/app/main.py",
          "software/microgrow_hub/app/models.py",
          "software/microgrow_hub/app/ota/__init__.py",
          "software/microgrow_hub/app/ota/bundle_verifier.py",
          "software/microgrow_hub/app/ota/manager_state.py",
          "software/microgrow_hub/app/ota/plan_store.py",
          "software/microgrow_hub/app/ota/report.py",
          "software/microgrow_hub/app/ota/storage.py",
          "software/microgrow_hub/app/routers/__init__.py",
          "software/microgrow_hub/app/routers/auth.py"
        ],
        "name": "Python",
        "source": "manifest+path-heuristic",
        "usage_count": 59,
        "version": null
      },
      {
        "category": "database",
        "confidence": 0.65,
        "evidence_paths": [
          "software/microgrow_hub/microgrow_hub.db"
        ],
        "name": "SQLite",
        "source": "path-heuristic",
        "usage_count": 1,
        "version": null
      }
    ],
    "new_unknowns": [
      {
        "affected_entities": [
          "feat-f775897b978921d2a59877ac"
        ],
        "category": "test coverage unknown",
        "confidence": 0.66,
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
        "id": "unknown-9c9120025142a86dd9ee170a",
        "reason": "Feature maturity is low enough that the implementation or validation surface remains partially unknown.",
        "recommended_investigation": "Inspect the implementation and validation surface for API.",
        "severity": "medium",
        "title": "Feature coverage unknown for API"
      },
      {
        "affected_entities": [
          "feat-788a13b593018923769b94c1"
        ],
        "category": "test coverage unknown",
        "confidence": 0.7,
        "evidence": [
          "calibration/reference_measurements/README.md",
          "calibration/reference_measurements/REFERENCE_INSTRUMENT_REGISTER.md",
          "calibration/sensor_offsets/README.md",
          "calibration/sensor_offsets/SHTC3_CALIBRATION_RECORD.md",
          "calibration/sensor_offsets/VEML7700_CALIBRATION_RECORD.md",
          "calibration/tank_profiles/README.md",
          "docs/04_hardware/pressure_water_level_sensor_bench_plan.md",
          "docs/04_hardware/prototype/images/rev_b_bench_layout.png",
          "docs/04_hardware/prototype/rev_b_bench_checklist.md",
          "docs/04_hardware/prototype/rev_b_bench_layout.md"
        ],
        "id": "unknown-5b758e2766cd4190a5d12cdd",
        "reason": "Feature maturity is low enough that the implementation or validation surface remains partially unknown.",
        "recommended_investigation": "Inspect the implementation and validation surface for Hardware Validation.",
        "severity": "medium",
        "title": "Feature coverage unknown for Hardware Validation"
      },
      {
        "affected_entities": [
          "feat-1da7afc0a31b13a4366e1827"
        ],
        "category": "test coverage unknown",
        "confidence": 0.61,
        "evidence": [
          "REPO_CONTEXT.md",
          "docs/project_control/user_guide/REPOSITORY_INTELLIGENCE_GUIDE.md",
          "experiments/vision/plant_scanner/NEXT_STEPS.md",
          "experiments/vision/plant_scanner/README.md",
          "experiments/vision/plant_scanner/RESULTS.md",
          "experiments/vision/plant_scanner/STATUS.md",
          "experiments/vision/plant_scanner/TEST_PLAN.md",
          "tools/dev/update_repo_context.ps1"
        ],
        "id": "unknown-8b99236e0ae233c18874fcd5",
        "reason": "Feature maturity is low enough that the implementation or validation surface remains partially unknown.",
        "recommended_investigation": "Inspect the implementation and validation surface for Repository Intelligence.",
        "severity": "medium",
        "title": "Feature coverage unknown for Repository Intelligence"
      }
    ],
    "removed_features": [],
    "removed_technologies": [],
    "resolved_risks": [],
    "resolved_unknowns": [],
    "test_changes": []
  },
  "latest_genome_id": "genome-874beeefe1bcb72981dd5864",
  "previous_genome_id": null,
  "project_id": "microgrow-v1"
}
```