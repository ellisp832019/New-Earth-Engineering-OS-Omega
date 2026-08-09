import json
from pathlib import Path

from neos.core import init_project, scan_project
from neos.firmware import (
    _build_compatibility,
    _build_gpio_conflicts,
    _detect_gpio,
    _detect_isr_body_risks,
    _detect_state_machines,
    _detect_tasks_or_control_risks,
    _detect_timing_facts,
    build_firmware_intelligence,
    firmware_impact,
    firmware_trace,
)


def _manifest(repo: Path) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": "demo",
            "name": "Demo",
            "repository": {"path": str(repo)},
        }
    )


def test_firmware_intelligence_extracts_platformio_and_rtossignals(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "platformio.ini").write_text(
        """
[platformio]
default_envs = release

[env:base]
platform = espressif32
board = esp32dev
framework = arduino, espidf
build_flags = -DDEBUG
lib_deps = Wire, SPI
upload_protocol = esptool
monitor_speed = 115200

[env:release]
extends = base
build_flags = -O2 -DRELEASE

[env:debug]
extends = base
build_flags = -Og -DDEBUG
"""
    )
    (repo / "src").mkdir()
    (repo / "src" / "main.cpp").write_text(
        """
#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/event_groups.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

enum class State { Boot, Running, Fault };

struct Packet {
  uint8_t id;
  uint16_t value;
};

static uint8_t buffer[256];
static const int RELAY_PIN = 25;

QueueHandle_t queueHandle;
SemaphoreHandle_t mutexHandle;
EventGroupHandle_t eventHandle;

void onInterrupt() {
  delay(1);
}

void workerTask(void *) {
  while (true) {
    delay(10);
  }
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  attachInterrupt(RELAY_PIN, onInterrupt, FALLING);
  xTaskCreatePinnedToCore(workerTask, "worker", 2048, nullptr, 1, nullptr, 1);
  queueHandle = xQueueCreate(4, sizeof(Packet));
  mutexHandle = xSemaphoreCreateMutex();
  eventHandle = xEventGroupCreate();
  xQueueSend(queueHandle, nullptr, 0);
  xSemaphoreTake(mutexHandle, 0);
  xTaskNotifyGive(nullptr);
  xTimerCreate("poll", 1000, pdTRUE, nullptr, nullptr);
  Wire.begin();
  Serial.begin(115200);
}

void loop() {
  State state = State::Boot;
  switch (state) {
    case State::Boot:
      break;
    default:
      break;
  }
  Serial.println("ready");
}
"""
    )
    hardware = repo / "hardware"
    hardware.mkdir()
    (hardware / "esp32dev.kicad_pro").write_text("{\"board\": \"ESP32 Dev Board\"}")
    (hardware / "esp32dev.kicad_sch").write_text("(kicad_sch (version 20211014))")
    (hardware / "esp32dev.kicad_pcb").write_text("(kicad_pcb (version 20211014))")
    (hardware / "pin_map.md").write_text("GPIO25 -> GPIO_RELAY\nGPIO21 -> I2C_SDA\nGPIO22 -> I2C_SCL\n")
    (hardware / "bringup.md").write_text("Hardware validation passed.\n")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))

    init_project(db, manifest)
    scan_project(db, "demo", repo)

    snapshot = build_firmware_intelligence(db, "demo")

    summary = snapshot["summary"]
    assert summary["firmware_source_count"] >= 2
    assert summary["environment_count"] == 3
    assert summary["target_count"] == 3
    assert summary["build_variant_count"] == 3
    assert summary["rtos_primitive_count"] >= 5
    assert summary["timing_fact_count"] >= 2
    assert summary["bus_count"] >= 1
    assert summary["packet_count"] >= 1
    assert summary["finding_count"] >= 1
    assert summary["gpio_conflict_count"] >= 0
    assert "platformio" in snapshot["supported_parsers"]
    assert snapshot["build_variants"]
    assert snapshot["tasks"]
    assert snapshot["rtos_primitives"]
    assert snapshot["interrupts"]
    assert snapshot["timers"]
    assert snapshot["timing_facts"]
    assert snapshot["state_machines"]
    assert snapshot["peripherals"]
    assert snapshot["buses"]
    assert snapshot["gpio"]
    assert isinstance(snapshot["gpio_conflicts"], list)
    assert snapshot["protocols"]
    assert snapshot["packets"]
    assert snapshot["memory_findings"]
    assert snapshot["findings"]
    assert snapshot["compatibility"]
    assert summary["compatibility_state"] in {"compatible", "compatible_with_conditions", "possible_mismatch", "unknown"}

    trace = firmware_trace(snapshot, "RELAY_PIN")
    assert trace["count"] >= 1

    impact = firmware_impact(snapshot, "worker")
    assert impact["count"] >= 1


def test_firmware_gpio_conflicts_prefer_aliases_and_flag_clear_mismatch():
    alias_code = "#define RELAY_PIN 25\n"
    alias_gpio = _detect_gpio(alias_code, "src/main.cpp", "demo")
    alias_snapshot = {
        "pins": [
            {
                "hardware_pin": "GPIO25",
                "signal": "GPIO_RELAY",
                "firmware_symbol": "RELAY_PIN",
                "revision": "r1",
            }
        ],
        "boards": [{"revision": "r1"}],
    }

    assert _build_gpio_conflicts(project_id="demo", gpio=alias_gpio, hardware_snapshot=alias_snapshot) == []

    mismatch_snapshot = {
        "pins": [
            {
                "hardware_pin": "GPIO25",
                "signal": "I2C_SDA",
                "firmware_symbol": "I2C_SDA",
                "revision": "r1",
            }
        ],
        "boards": [{"revision": "r1"}],
    }
    mismatch_conflicts = _build_gpio_conflicts(project_id="demo", gpio=alias_gpio, hardware_snapshot=mismatch_snapshot)
    assert mismatch_conflicts
    assert mismatch_conflicts[0]["status"] == "confirmed_conflict"
    assert mismatch_conflicts[0]["certainty"] == "high_confidence"

    conditional_gpio = _detect_gpio(
        """
#if defined(BOARD_A)
#define RELAY_PIN 25
#endif
""".strip(),
        "src/main.cpp",
        "demo",
    )
    conditional_conflicts = _build_gpio_conflicts(project_id="demo", gpio=conditional_gpio, hardware_snapshot=alias_snapshot)
    assert conditional_conflicts == []


def test_firmware_state_machine_requires_real_transition_evidence():
    unrelated = "enum class State { Boot, Running, Fault }; void loop() { switch(status) { default: break; } }"
    machines = _detect_state_machines(unrelated, "src/main.cpp", "demo")
    assert len(machines) == 1
    assert machines[0]["status"] == "state_machine_candidate"

    real_machine = """
enum class State { Boot, Running, Fault };
void loop() {
  switch(state) {
    case State::Boot:
      state = State::Running;
      break;
    default:
      break;
  }
}
""".strip()
    machines = _detect_state_machines(real_machine, "src/main.cpp", "demo")
    assert machines
    assert machines[0]["status"] == "canonical_state_machine"
    assert machines[0]["transitions"]


def test_timing_and_control_heuristics_ignore_setup_delays():
    code = """
void setup() {
  delay(1000);
}
""".strip()

    risks, validations = _detect_tasks_or_control_risks(code, "src/main.cpp", "demo")
    assert risks == []
    assert validations == []

    facts = _detect_timing_facts(code, "src/main.cpp", "demo")
    assert any(fact["normalized_value_ms"] == 1000.0 for fact in facts)
    assert any(fact["certainty"] == "high_confidence" for fact in facts)


def test_isr_heuristics_whitelist_from_isr_signaling_and_flag_blocking():
    safe_isr = """
void IRAM_ATTR onInterrupt() {
  xQueueSendFromISR(queueHandle, nullptr, nullptr);
  portYIELD_FROM_ISR();
}
""".strip()
    assert _detect_isr_body_risks(safe_isr, "src/main.cpp", "demo", ["onInterrupt"]) == []

    unsafe_isr = """
void onInterrupt() {
  delay(1);
}
""".strip()
    findings = _detect_isr_body_risks(unsafe_isr, "src/main.cpp", "demo", ["onInterrupt"])
    assert findings
    assert findings[0]["scope"] == "isr"
    assert findings[0]["certainty"] == "high_confidence"


def test_compatibility_is_deterministic_and_conservative_without_inventory():
    compatibility, overall = _build_compatibility(
        project_id="demo",
        environments=[{"name": "release", "board": "esp32dev"}],
        hardware_snapshot=None,
    )
    assert overall == "unknown"
    assert compatibility[0]["status"] == "unknown"
    assert compatibility[0]["criteria"]["hardware_inventory"] == "missing"

    compatible, overall_compatible = _build_compatibility(
        project_id="demo",
        environments=[{"name": "release", "board": "esp32dev"}],
        hardware_snapshot={"boards": [{"name": "ESP32 Dev Board", "revision": "revA"}]},
    )
    assert overall_compatible == "compatible"
    assert compatible[0]["status"] == "compatible"
    assert compatible[0]["certainty"] == "high_confidence"
    assert compatible[0]["criteria"]["match_status"] == "compatible"
    assert compatible == _build_compatibility(
        project_id="demo",
        environments=[{"name": "release", "board": "esp32dev"}],
        hardware_snapshot={"boards": [{"name": "ESP32 Dev Board", "revision": "revA"}]},
    )[0]
