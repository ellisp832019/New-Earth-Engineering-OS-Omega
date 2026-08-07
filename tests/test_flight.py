from __future__ import annotations

import json
import subprocess
from pathlib import Path

from neos.core import init_project, scan_project
from neos.flight import (
    build_project_flight,
    create_flight_checkpoint,
    flight_diff,
    flight_incidents,
    flight_regressions,
    flight_replay,
    flight_snapshots,
    flight_state,
    flight_timeline,
)
from neos.genome import build_project_genome
from neos.memory import build_project_memory


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
            "technologies": ["Python"],
        }
    )


def test_flight_snapshot_diff_and_replay(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    _commit(repo, "feat: initial demo")

    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    db = tmp_path / "neos.db"

    init_project(db, manifest)
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")
    build_project_memory(db, "demo")

    first = build_project_flight(db, "demo")
    repeat = build_project_flight(db, "demo")
    assert first["stored"] is True
    assert repeat["stored"] is False
    assert repeat["snapshot"]["id"] == first["snapshot"]["id"]

    checkpoint = create_flight_checkpoint(db, "demo", checkpoint_type="manual", label="baseline")
    assert checkpoint["checkpoint"]["snapshot_id"] == first["snapshot"]["id"]

    (repo / "tests" / "test_app.py").unlink()
    (repo / "notes.md").write_text("notes\n")
    _commit(repo, "test: remove test and add notes")
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")
    build_project_memory(db, "demo")
    second = build_project_flight(db, "demo")

    assert second["snapshot"]["id"] != first["snapshot"]["id"]
    snapshots = flight_snapshots(db, "demo")
    assert snapshots["count"] >= 2

    state = flight_state(db, "demo", at=first["snapshot"]["id"])
    assert state["snapshot"]["id"] == first["snapshot"]["id"]

    diff = flight_diff(db, "demo", first["snapshot"]["id"], second["snapshot"]["id"])
    assert diff["changes"]["tests"]["removed"]
    assert diff["changes"]["files"]["added"]

    timeline = flight_timeline(db, "demo")
    timestamps = [item["timestamp"] for item in timeline["items"]]
    assert timestamps == sorted(timestamps)

    replay = flight_replay(db, "demo", first["snapshot"]["id"], second["snapshot"]["id"])
    assert replay["count"] >= 2

    regressions = flight_regressions(db, "demo")
    incidents = flight_incidents(db, "demo")
    assert regressions["count"] >= 1
    assert incidents["count"] >= 1
    assert any(item["indicator_type"] == "test_count_decreased" for item in regressions["items"])


def test_flight_snapshot_lookup_is_deterministic(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    _commit(repo, "docs: initial")

    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    db = tmp_path / "neos.db"

    init_project(db, manifest)
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")
    build_project_memory(db, "demo")

    first = build_project_flight(db, "demo")
    second = build_project_flight(db, "demo")
    assert first["snapshot"]["id"] == second["snapshot"]["id"]
    assert second["stored"] is False
