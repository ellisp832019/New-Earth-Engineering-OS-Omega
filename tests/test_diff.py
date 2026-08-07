import json
from pathlib import Path

from neos.core import init_project, scan_diff, scan_project


def test_scan_diff_tracks_added_removed_modified(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n")
    (repo / "main.py").write_text("print('one')\n")
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
    first = scan_project(db, "demo", repo)
    assert first["file_count"] == 2

    (repo / "README.md").write_text("# Demo v2\n")
    (repo / "main.py").unlink()
    (repo / "notes.md").write_text("notes\n")
    scan_project(db, "demo", repo)

    diff = scan_diff(db, "demo")
    assert {item["source_path"] for item in diff["diff"]["added"]} == {"notes.md"}
    assert {item["source_path"] for item in diff["diff"]["removed"]} == {"main.py"}
    assert diff["diff"]["modified"][0]["before"]["source_path"] == "README.md"
    assert diff["diff"]["unchanged"] == []
