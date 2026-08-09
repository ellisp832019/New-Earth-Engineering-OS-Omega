import json
import subprocess
import sys
from pathlib import Path

from neos.core import init_project, scan_project


def _manifest(repo: Path) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": "demo",
            "name": "Demo",
            "repository": {"path": str(repo)},
        }
    )


def test_cli_firmware_summary_json(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "platformio.ini").write_text("[env:demo]\nplatform=espressif32\nboard=esp32dev\n")
    (repo / "src").mkdir()
    (repo / "src" / "main.cpp").write_text("void setup() {}\n")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    init_project(db, manifest)
    scan_project(db, "demo", repo)

    result = subprocess.run(
        [sys.executable, "-m", "neos", "--db", str(db), "firmware", "summary", "demo", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["project_id"] == "demo"
    assert payload["environment_count"] >= 1

    result = subprocess.run(
        [sys.executable, "-m", "neos", "--db", str(db), "firmware", "rtos-primitives", "demo", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["count"] >= 0
