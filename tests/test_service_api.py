from __future__ import annotations

import json
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from neos.core import init_project, scan_project
from neos.flight import build_project_flight
from neos.genome import build_project_genome
from neos.memory import build_project_memory
from neos.service.app import create_service_server


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "user.name", "Tester")


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _manifest(repo: Path) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": "demo",
            "name": "Demo",
            "repository": {"path": str(repo)},
        }
    )


def _start_server(db: Path):
    server = create_service_server(db, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _get_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, object]):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_service_endpoints_and_local_binding(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    hardware = repo / "hardware"
    hardware.mkdir()
    (hardware / "demo_board.kicad_pro").write_text("{\"board\": \"Demo Board\"}")
    (hardware / "demo_board.kicad_sch").write_text("(kicad_sch (version 20211014) (generator eeschema))")
    (hardware / "demo_board.kicad_pcb").write_text("(kicad_pcb (version 20211014) (generator pcbnew))")
    (hardware / "demo_bom.csv").write_text(
        "reference,manufacturer,mpn,description,footprint,value\n"
        "U1,ST,STM32F401,MCU,QFN-48,STM32F401\n"
        "J1,Amphenol,124015,Connector,USB-C,USB-C\n"
    )
    (hardware / "pin_map.md").write_text("GPIO25 -> GPIO_RELAY\nGPIO21 -> I2C_SDA\nGPIO22 -> I2C_SCL\n")
    (hardware / "bringup.md").write_text("Hardware validation passed after bench test and power-on verification.\n")
    (repo / "platformio.ini").write_text(
        """
[platformio]
default_envs = release

[env:base]
platform = espressif32
board = esp32dev
framework = arduino
build_flags = -DDEBUG

[env:release]
extends = base
build_flags = -O2 -DRELEASE
"""
    )
    (repo / "src" / "main.cpp").write_text(
        """
#include <Arduino.h>

enum class State { Boot, Running };

void onInterrupt() {}
void workerTask(void *) {}

void setup() {
  pinMode(25, OUTPUT);
  attachInterrupt(25, onInterrupt, FALLING);
  xTaskCreatePinnedToCore(workerTask, "worker", 2048, nullptr, 1, nullptr, 1);
  xTimerCreate("poll", 1000, pdTRUE, nullptr, nullptr);
}
"""
    )
    _commit(repo, "feat: initial demo")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    init_project(db, manifest)
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")
    build_project_memory(db, "demo")
    build_project_flight(db, "demo")

    server, thread = _start_server(db)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, health = _get_json(f"{base}/health")
        assert status == 200
        assert health["status"] == "healthy"
        assert health["service_name"] == "NEOS Local Service"
        assert health["service_version"] == "1.3.0"
        assert health["api_version"] == "v1"
        assert health["schema_version"] == 11
        assert health["instance_id"]
        assert health["ai"]["settings"]["provider_id"] == "mock"
        assert health["command_centre"]["open_work_items"] >= 0

        status, projects = _get_json(f"{base}/projects")
        assert status == 200
        assert projects["projects"][0]["project_id"] == "demo"

        status, registry = _get_json(f"{base}/registry")
        assert status == 200
        assert registry["project_count"] == 1

        status, project_registry = _get_json(f"{base}/registry/demo")
        assert status == 200
        assert project_registry["project_id"] == "demo"
        assert project_registry["contracts"]["project"]["contract_type"] == "PROJECT_CONTRACT"

        status, project_drift = _get_json(f"{base}/registry/demo/drift")
        assert status == 200
        assert project_drift["project_id"] == "demo"

        status, project_impact = _get_json(f"{base}/registry/demo/impact")
        assert status == 200
        assert project_impact["project_id"] == "demo"

        status, ecosystem_search = _get_json(f"{base}/ecosystem/search?q=demo")
        assert status == 200
        assert ecosystem_search["count"] >= 1

        status, today = _get_json(f"{base}/today")
        assert status == 200
        assert today["work_queue"]["count"] >= 0

        status, queue = _get_json(f"{base}/work")
        assert status == 200
        assert "items" in queue

        status, search = _get_json(f"{base}/search?q=demo")
        assert status == 200
        assert search["query"] == "demo"

        status, providers = _get_json(f"{base}/ai/providers")
        assert status == 200
        assert providers["providers"][0]["provider_id"] in {"none", "mock"}

        status, ai_settings = _get_json(f"{base}/ai/settings")
        assert status == 200
        assert ai_settings["settings"]["provider_id"] == "mock"

        status, ai_response = _post_json(
            f"{base}/ai/query",
            {
                "project_ids": ["demo"],
                "question": "What should I work on next?",
                "mode": "plan",
            },
        )
        assert status == 200
        assert ai_response["status"] == "success"
        assert ai_response["request_id"]
        assert ai_response["conversation_id"]
        assert ai_response["project_ids"] == ["demo"]

        status, citations = _get_json(f"{base}/ai/requests/{ai_response['request_id']}/citations")
        assert status == 200
        assert citations["request_id"] == ai_response["request_id"]

        status, inbox = _get_json(f"{base}/decisions/intelligence/inbox?project_id=demo")
        assert status == 200
        assert "items" in inbox

        status, next_actions = _get_json(f"{base}/decisions/intelligence/next-actions?project_id=demo")
        assert status == 200
        assert "items" in next_actions

        status, readiness = _get_json(f"{base}/decisions/intelligence/release-readiness?project_id=demo")
        assert status == 200
        assert readiness["project_id"] == "demo"

        status, evaluate = _post_json(
            f"{base}/decisions/intelligence/evaluate",
            {
                "project_id": "demo",
                "title": "What should we do next?",
                "description": "Prioritise the highest-impact work.",
                "decision_type": "engineering_next_action",
                "scope": "project",
            },
        )
        assert status == 200
        assert evaluate["recommendation"]["recommended_option"]

        status, compare = _post_json(
            f"{base}/decisions/intelligence/compare",
            {
                "question": "Compare architectures",
                "decision_type": "architecture",
                "options": [
                    {"name": "Option A", "description": "Keep current architecture."},
                    {"name": "Option B", "description": "Introduce a shared module."},
                ],
            },
        )
        assert status == 200
        assert compare["recommendation"]["recommended_option"]

        status, accept = _post_json(
            f"{base}/decisions/intelligence/accept/{evaluate['question']['id']}",
            {"operator": "tester", "selected_option": evaluate["recommendation"]["recommended_option"]},
        )
        assert status == 200
        assert accept["status"] == "accepted"

        status, history = _get_json(f"{base}/decisions/intelligence/history?project_id=demo")
        assert status == 200
        assert history["count"] >= 1

        status, requirements = _get_json(f"{base}/requirements/intelligence?project_id=demo")
        assert status == 200
        assert requirements["project_count"] == 1
        assert requirements["requirement_count"] >= 0

        status, refresh = _post_json(f"{base}/projects/demo/refresh", {"scan": False, "requirements": True, "work_queue": True})
        assert status == 200
        assert refresh["project_id"] == "demo"
        assert refresh["status"] == "completed"

        status, refresh_job = _get_json(f"{base}/refresh/{refresh['job_id']}")
        assert status == 200
        assert refresh_job["job_id"] == refresh["job_id"]

        status, session = _get_json(f"{base}/session")
        assert status == 200
        assert session["session_key"] == "workspace"

        status, requirement_inventory = _get_json(f"{base}/requirements/intelligence/inventory?project_id=demo")
        assert status == 200
        assert "items" in requirement_inventory

        status, requirement_gaps = _get_json(f"{base}/requirements/intelligence/gaps?project_id=demo")
        assert status == 200
        assert "items" in requirement_gaps

        status, registered = _post_json(f"{base}/projects/register", {"manifest_path": str(manifest)})
        assert status == 200
        assert registered["project_id"] == "demo"

        status, scan = _post_json(f"{base}/projects/demo/scan", {"repo_path": str(repo)})
        assert status == 200
        assert scan["project_id"] == "demo"
        assert scan["status"] == "scanned"

        status, summary = _get_json(f"{base}/projects/demo/summary")
        assert status == 200
        assert summary["project_id"] == "demo"

        status, genome = _get_json(f"{base}/projects/demo/genome")
        assert status == 200
        assert genome["project_id"] == "demo"

        status, project = _get_json(f"{base}/projects/demo")
        assert status == 200
        assert project["project"]["project_id"] == "demo"
        assert project["hardware"]["summary"]["board_count"] >= 1

        status, hardware_payload = _get_json(f"{base}/hardware/demo")
        assert status == 200
        assert hardware_payload["summary"]["board_count"] >= 1

        status, hardware_boards = _get_json(f"{base}/hardware/demo/boards")
        assert status == 200
        assert hardware_boards["boards"]

        status, hardware_pins = _get_json(f"{base}/hardware/demo/pins")
        assert status == 200
        assert hardware_pins["pins"]

        status, hardware_validation = _get_json(f"{base}/hardware/demo/validation")
        assert status == 200
        assert hardware_validation["validation_state"] in {"validated", "partial", "not_run", "unknown"}

        status, firmware_payload = _get_json(f"{base}/firmware/demo")
        assert status == 200
        assert firmware_payload["summary"]["environment_count"] >= 1
        assert firmware_payload["summary"]["target_count"] >= 1

        status, firmware_targets = _get_json(f"{base}/firmware/demo/targets")
        assert status == 200
        assert firmware_targets["targets"]

        status, firmware_variants = _get_json(f"{base}/projects/demo/firmware/build-variants")
        assert status == 200
        assert firmware_variants["build_variants"]

        status, firmware_envs = _get_json(f"{base}/firmware/demo/environments")
        assert status == 200
        assert firmware_envs["environments"]

        status, firmware_rtos = _get_json(f"{base}/projects/demo/firmware/rtos-primitives")
        assert status == 200
        assert "rtos_primitives" in firmware_rtos

        status, firmware_timing = _get_json(f"{base}/projects/demo/firmware/timing")
        assert status == 200
        assert "timing_facts" in firmware_timing

        status, firmware_buses = _get_json(f"{base}/projects/demo/firmware/buses")
        assert status == 200
        assert "buses" in firmware_buses

        status, firmware_gpio_conflicts = _get_json(f"{base}/projects/demo/firmware/gpio-conflicts")
        assert status == 200
        assert "gpio_conflicts" in firmware_gpio_conflicts

        status, firmware_packets = _get_json(f"{base}/projects/demo/firmware/packets")
        assert status == 200
        assert "packets" in firmware_packets

        status, firmware_compatibility = _get_json(f"{base}/firmware/demo/compatibility")
        assert status == 200
        assert firmware_compatibility["compatibility"]

        status, firmware_findings = _get_json(f"{base}/projects/demo/firmware/findings")
        assert status == 200
        assert "findings" in firmware_findings

        status, project_firmware = _get_json(f"{base}/projects/demo/firmware")
        assert status == 200
        assert project_firmware["summary"]["environment_count"] >= 1

        status, firmware_trace = _get_json(f"{base}/firmware/demo/impact/worker")
        assert status == 200
        assert firmware_trace["count"] >= 1

        status, memory = _get_json(f"{base}/projects/demo/memory")
        assert status == 200
        assert memory["project_id"] == "demo"

        status, flight = _get_json(f"{base}/projects/demo/flight")
        assert status == 200
        assert flight["project_id"] == "demo"

        status, timeline = _get_json(f"{base}/projects/demo/flight/timeline")
        assert status == 200
        assert timeline["project_id"] == "demo"

        status, regressions = _get_json(f"{base}/projects/demo/flight/regressions")
        assert status == 200
        assert regressions["project_id"] == "demo"

        status, forbidden = _post_json(f"{base}/shutdown", {"shutdown_token": "wrong"})
        assert status == 403
        assert forbidden["error"] == "forbidden"

        status, invalid = _get_json(f"{base}/projects/missing/summary")
        assert status == 404
        assert invalid["error"] == "not_found"

        with pytest.raises(ValueError):
            create_service_server(db, host="0.0.0.0", port=0)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
