from __future__ import annotations

import json
from pathlib import Path

from neos.core import init_project, scan_project
from neos.db import connect
from neos.ecosystem import (
    analyse_portfolio,
    build_portfolio_snapshot,
    ecosystem_diff,
    project_registry_v2,
)


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "user.name", "Tester")


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _manifest(repo: Path, project_id: str, name: str, technologies: list[object], **extra: object) -> str:
    payload = {
        "schema_version": "1.0",
        "project_id": project_id,
        "name": name,
        "description": str(extra.get("description", "")),
        "lifecycle": extra.get("lifecycle", "active"),
        "repository": {"path": str(repo)},
        "technologies": technologies,
        "tags": extra.get("tags", []),
    }
    return json.dumps(payload)


def _insert_decision(db: Path, *, project_id: str, scan_id: str, decision_id: str, title: str, decision: str) -> None:
    conn = connect(db)
    now = "2026-08-08T00:00:00+00:00"
    conn.execute(
        """
        INSERT INTO engineering_decisions(
            id, project_id, scan_id, title, status, date, context, decision, rationale, alternatives,
            consequences, source_path, confidence, provenance, created_at, observed_at, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            decision_id,
            project_id,
            scan_id,
            title,
            "accepted",
            "2026-08-08",
            "portfolio architecture",
            decision,
            decision,
            "alternative architectures reviewed",
            "integration requires review",
            "docs/decisions.md",
            0.9,
            "test-fixture",
            now,
            now,
            "{}",
        ),
    )
    conn.commit()
    conn.close()


def _project_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    gamma = tmp_path / "gamma"
    for repo, label in ((alpha, "Alpha"), (beta, "Beta"), (gamma, "Gamma")):
        repo.mkdir()
        _init_repo(repo)
        (repo / "README.md").write_text(f"# {label}\n\nlogging configuration repository intelligence\n")
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("def run():\n    return True\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
        _commit(repo, f"feat: {label.lower()} initial")
    return alpha, beta, gamma


def _seed(tmp_path: Path) -> Path:
    alpha, beta, gamma = _project_fixture(tmp_path)
    db = tmp_path / "neos.db"
    manifests = {
        "alpha": _manifest(
            alpha,
            "alpha",
            "Project Alpha",
            ["Python"],
            description="local-first architecture",
            tags=["logging", "local-first"],
        ),
        "beta": _manifest(
            beta,
            "beta",
            "Project Beta",
            ["Python", "Flutter==3.0.0"],
            description="mandatory cloud service",
            lifecycle="experimental",
            tags=["cloud"],
        ),
        "gamma": _manifest(
            gamma,
            "gamma",
            "Project Gamma",
            ["Python"],
            description="depends-on:alpha integration bridge",
            tags=["integration"],
        ),
    }
    for project_id, manifest in manifests.items():
        manifest_path = tmp_path / f"{project_id}.json"
        manifest_path.write_text(manifest)
        init_project(db, manifest_path)
    for project_id, repo in (("alpha", alpha), ("beta", beta), ("gamma", gamma)):
        scan = scan_project(db, project_id, repo)
        if project_id == "alpha":
            _insert_decision(db, project_id="alpha", scan_id=scan["scan_id"], decision_id="decision-alpha", title="Architecture", decision="local-first architecture")
        if project_id == "beta":
            _insert_decision(db, project_id="beta", scan_id=scan["scan_id"], decision_id="decision-beta", title="Architecture", decision="mandatory cloud service")
    return db


def test_ecosystem_analysis_is_deterministic_and_evidence_backed(tmp_path: Path):
    db = _seed(tmp_path)

    registry = project_registry_v2(db)
    assert registry["project_count"] == 3
    assert {project["project_id"] for project in registry["projects"]} == {"alpha", "beta", "gamma"}

    analysis_one = analyse_portfolio(db)
    analysis_two = analyse_portfolio(db)

    assert analysis_one["technology_portfolio"]["shared_technologies"]
    assert analysis_one["capability_matrix"]["shared_capabilities"]
    assert analysis_one["reuse_candidates"]
    assert analysis_one["duplicate_findings"]
    assert analysis_one["cross_project_dependencies"]
    assert analysis_one["decision_conflicts"]
    assert analysis_one["portfolio_risks"]
    assert analysis_one["unknown_surface"]
    assert analysis_one["attention"]
    assert analysis_one["health"]["project_count"] == 3
    assert analysis_one["portfolio_snapshot"]["id"] == analysis_two["portfolio_snapshot"]["id"]

    snapshot = build_portfolio_snapshot(db, name="fixture")
    diff = ecosystem_diff(db, snapshot["portfolio_snapshot"]["id"], analysis_one["portfolio_snapshot"]["id"])
    assert diff["from_snapshot_id"]
    assert diff["to_snapshot_id"]
