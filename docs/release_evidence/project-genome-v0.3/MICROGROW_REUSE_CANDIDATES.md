# MicroGrow Reuse Candidates
Project: `microgrow-v1`
Reuse count: **10**

- **software/flutter_app** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **firmware/microgrow_node** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **docs/project_control** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **docs/10_roadmap** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **tools/microgrow_dev_launcher** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **simulation/proteus** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **docs/audit** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **tools/project_control_app** | architecture-component | confidence 0.98 | domains: api, application, configuration
- **Flutter Application** | feature-maturity | confidence 0.99 | domains: api, application
- **Testing** | feature-maturity | confidence 0.99 | domains: api, application

```json
{
  "project_id": "microgrow-v1",
  "reuse": [
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "software/flutter_app",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "firmware/microgrow_node",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "docs/project_control",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "docs/10_roadmap",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "tools/microgrow_dev_launcher",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "simulation/proteus",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "docs/audit",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.98,
      "dependencies": [],
      "name": "tools/project_control_app",
      "possible_reuse_domains": [
        "api",
        "application",
        "configuration"
      ],
      "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
      "source": "architecture-component",
      "tests": []
    },
    {
      "confidence": 0.99,
      "dependencies": [],
      "name": "Flutter Application",
      "possible_reuse_domains": [
        "api",
        "application"
      ],
      "reason": "Feature maturity is high enough to consider reuse across similar projects.",
      "source": "feature-maturity",
      "tests": [
        "services/crop_profile_commerce_backend/pubspec.yaml"
      ]
    },
    {
      "confidence": 0.99,
      "dependencies": [],
      "name": "Testing",
      "possible_reuse_domains": [
        "api",
        "application"
      ],
      "reason": "Feature maturity is high enough to consider reuse across similar projects.",
      "source": "feature-maturity",
      "tests": [
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
      ]
    }
  ]
}
```