from __future__ import annotations

import json
from pathlib import Path

from neos.core import init_project
from neos.hardware import build_hardware_intelligence, hardware_impact, hardware_trace


def test_hardware_intelligence_extracts_synthetic_evidence(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hardware").mkdir()
    (repo / "hardware" / "board.kicad_pro").write_text("{\"board\": \"Demo Board\"}")
    (repo / "hardware" / "board.kicad_sch").write_text("(kicad_sch (version 20211014))")
    (repo / "hardware" / "board.kicad_pcb").write_text("(kicad_pcb (version 20211014))")
    (repo / "hardware" / "demo_bom.csv").write_text(
        "reference,manufacturer,mpn,description,footprint,value\n"
        "U1,ST,STM32F401,MCU,QFN-48,STM32F401\n"
        "J1,Amphenol,124015,Connector,USB-C,USB-C\n"
    )
    (repo / "hardware" / "pin_map.md").write_text("GPIO21 -> I2C_SDA\nGPIO22 -> I2C_SCL\n")
    (repo / "hardware" / "bringup.md").write_text("Hardware validation passed after bench test.\n")

    manifest = tmp_path / "project.neos.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": "demo",
                "name": "Demo",
                "repository": {"path": str(repo)},
            }
        )
    )
    db = tmp_path / "neos.db"
    init_project(db, manifest)

    snapshot = build_hardware_intelligence(db, "demo")
    assert snapshot["summary"]["board_count"] >= 1
    assert snapshot["summary"]["component_count"] >= 1
    assert snapshot["summary"]["pin_mapping_count"] >= 1
    assert snapshot["validation_state"] in {"validated", "partial", "not_run", "unknown"}

    trace = hardware_trace(snapshot, "GPIO21")
    assert trace["count"] >= 1

    impact = hardware_impact(snapshot, "GPIO21")
    assert impact["entity_id"] == "GPIO21"
