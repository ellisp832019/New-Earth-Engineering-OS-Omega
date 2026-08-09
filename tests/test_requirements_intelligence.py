from __future__ import annotations

import json
import subprocess
from pathlib import Path

from neos.core import init_project, scan_project
from neos.genome import build_project_genome
from neos.requirements_intelligence import (
    build_requirement_intelligence,
    confirm_requirement,
    requirement_gaps,
    requirement_inventory,
    requirement_trace,
)


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


def test_requirement_intelligence_is_deterministic_and_reviewable(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "requirements.md").write_text(
        "# Requirements\n\n- The system must keep a traceable link between intent and implementation.\n- Release evidence shall be recorded.\n- Tests must be recorded.\n"
    )
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    _commit(repo, "feat: add requirements doc")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    init_project(db, manifest)
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")

    build_one = build_requirement_intelligence(db, project_ids=["demo"])
    build_two = build_requirement_intelligence(db, project_ids=["demo"])

    assert build_one["project_count"] == 1
    assert build_one["summary"]["candidate_count"] == build_two["summary"]["candidate_count"]
    assert build_one["requirements"]

    inventory = requirement_inventory(db, ["demo"])
    assert inventory["count"] >= 1

    gaps = requirement_gaps(db, ["demo"])
    assert gaps["count"] >= 0

    trace = requirement_trace(db, inventory["items"][0]["id"])
    assert trace["requirement"]["id"] == inventory["items"][0]["id"]

    confirmed = confirm_requirement(db, inventory["items"][0]["id"], notes="operator confirmed")
    assert confirmed["status"] == "confirmed"
