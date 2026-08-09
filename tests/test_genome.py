import json
from pathlib import Path

from neos.core import init_project, scan_project
from neos.genome import build_project_genome, genome_diff, genome_markdown_report, genome_summary


def _project_manifest(repo: Path) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": "demo",
            "name": "Demo",
            "repository": {"path": str(repo)},
            "technologies": ["PlatformIO", "Python", "Markdown"],
        }
    )


def test_project_genome_build_is_idempotent(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n")
    (repo / "platformio.ini").write_text("[env:demo]\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    manifest = tmp_path / "project.json"
    manifest.write_text(_project_manifest(repo))
    db = tmp_path / "neos.db"

    init_project(db, manifest)
    scan_project(db, "demo", repo)

    first = build_project_genome(db, "demo")
    second = build_project_genome(db, "demo")

    assert first["genome"]["project_id"] == "demo"
    assert first["genome"]["genome_schema_version"] == 1
    assert first["stored"] is True
    assert second["stored"] is False
    assert second["snapshot"]["id"] == first["snapshot"]["id"]
    assert genome_summary(first["genome"])["feature_count"] >= 1
    assert "Project Report: Demo" in genome_markdown_report(first["genome"])


def test_project_genome_diff_tracks_new_snapshot(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n")
    (repo / "platformio.ini").write_text("[env:demo]\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    manifest = tmp_path / "project.json"
    manifest.write_text(_project_manifest(repo))
    db = tmp_path / "neos.db"

    init_project(db, manifest)
    scan_project(db, "demo", repo)
    first = build_project_genome(db, "demo")

    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("# Guide\n")
    scan_project(db, "demo", repo)
    second = build_project_genome(db, "demo")
    diff = genome_diff(db, "demo")

    assert second["snapshot"]["id"] != first["snapshot"]["id"]
    assert diff["previous_genome_id"] == first["snapshot"]["id"]
    assert diff["latest_genome_id"] == second["snapshot"]["id"]
    assert "maturity_changes" in diff["changes"]
