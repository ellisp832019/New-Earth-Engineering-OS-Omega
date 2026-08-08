from __future__ import annotations

import json
import subprocess
from pathlib import Path

from neos.core import init_project, scan_project
from neos.decision_intelligence import (
    accept_decision,
    compare_options,
    decision_history,
    evaluate_decision_question,
    get_next_actions,
    get_release_readiness,
    review_reuse_candidate,
    run_scenario_analysis,
)
from neos.flight import build_project_flight
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


def _manifest(repo: Path, project_id: str, name: str, description: str) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": project_id,
            "name": name,
            "description": description,
            "repository": {"path": str(repo)},
        }
    )


def _project_repo(root: Path, project_id: str, label: str) -> Path:
    repo = root / project_id
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text(f"# {label}\n\nshared helper and test coverage evidence.\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    _commit(repo, f"feat: {label.lower()} initial")
    return repo


def _seed(tmp_path: Path) -> Path:
    alpha = _project_repo(tmp_path, "alpha", "Alpha")
    beta = _project_repo(tmp_path, "beta", "Beta")
    db = tmp_path / "neos.db"
    for project_id, repo in (("alpha", alpha), ("beta", beta)):
        manifest_path = tmp_path / f"{project_id}.json"
        manifest_path.write_text(_manifest(repo, project_id, project_id.title(), f"{project_id} repo"))
        init_project(db, manifest_path)
        scan_project(db, project_id, repo)
        build_project_genome(db, project_id)
        build_project_memory(db, project_id)
        build_project_flight(db, project_id)
    return db


def test_decision_intelligence_is_deterministic_and_persisted(tmp_path: Path):
    db = _seed(tmp_path)

    evaluation_one = evaluate_decision_question(
        db,
        "What should we do next?",
        "Prioritise the highest-impact work.",
        "engineering_next_action",
        project_ids=["alpha", "beta"],
        scope="portfolio",
        source="test",
    )
    evaluation_two = evaluate_decision_question(
        db,
        "What should we do next?",
        "Prioritise the highest-impact work.",
        "engineering_next_action",
        project_ids=["alpha", "beta"],
        scope="portfolio",
        source="test",
    )

    assert evaluation_one["question"]["decision_type"] == "engineering_next_action"
    assert evaluation_one["question"]["project_ids"] == ["alpha", "beta"]
    assert evaluation_one["recommendation"]["recommended_option"]
    assert evaluation_one["recommendation"]["strength"]
    assert evaluation_one["recommendation"]["id"] == evaluation_two["recommendation"]["id"]

    next_actions = get_next_actions(db, project_ids=["alpha", "beta"])
    assert next_actions["items"]

    readiness = get_release_readiness(db, "alpha")
    assert readiness["project_id"] == "alpha"
    assert readiness["status"] in {"READY", "READY_WITH_CONDITIONS", "NOT_READY", "INSUFFICIENT_EVIDENCE"}

    reuse = review_reuse_candidate(db, project_ids=["alpha", "beta"])
    assert "status" in reuse

    comparison = compare_options(
        db,
        "Compare the main architecture options.",
        "architecture",
        [
            {"name": "Option A", "description": "Keep the current architecture."},
            {"name": "Option B", "description": "Consolidate a shared module."},
        ],
        project_ids=["alpha", "beta"],
    )
    assert comparison["recommendation"]["recommended_option"]

    scenario = run_scenario_analysis(
        db,
        {"title": "Consolidate shared logic", "change": "Merge duplicated helpers.", "affected_entities": ["helpers"]},
        project_ids=["alpha", "beta"],
    )
    assert scenario["scenario"]["title"] == "Consolidate shared logic"

    accepted = accept_decision(db, evaluation_one["question"]["id"], operator="tester", selected_option=evaluation_one["recommendation"]["recommended_option"])
    assert accepted["status"] == "accepted"

    history = decision_history(db, project_ids=["alpha", "beta"])
    assert history["count"] >= 1
