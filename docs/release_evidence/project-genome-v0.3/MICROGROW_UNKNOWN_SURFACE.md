# MicroGrow Unknown Surface
Project: `microgrow-v1`
Unknown count: **3**

- **Feature coverage unknown for API** | medium | test coverage unknown | confidence 0.66
- **Feature coverage unknown for Hardware Validation** | medium | test coverage unknown | confidence 0.70
- **Feature coverage unknown for Repository Intelligence** | medium | test coverage unknown | confidence 0.61

```json
{
  "count": 3,
  "items": [
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
  "project_id": "microgrow-v1"
}
```