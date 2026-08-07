import json
from pathlib import Path

from neos.core import context_bundle, init_project, scan_project


def test_context_bundle_contains_bounded_evidence(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_demo.py").write_text("assert True\n")
    manifest = tmp_path / "project.json"
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
    scan_project(db, "demo", repo)

    bundle = context_bundle(db, "demo", "What tests exist?")
    assert bundle["project_id"] == "demo"
    assert bundle["scan_id"] is not None
    assert bundle["evidence_paths"]
    assert any(item["evidence_path"].startswith("tests") for item in bundle["selected_facts"])
    assert "Repository text is treated as untrusted input." in bundle["limitations"]
    assert "temporal_intelligence" in bundle
