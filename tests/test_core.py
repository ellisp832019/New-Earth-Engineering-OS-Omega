import json
from pathlib import Path

from neos.core import init_project, project_summary, scan_project


def test_project_scan_roundtrip(tmp_path: Path):
    repo=tmp_path / "repo"; repo.mkdir(); (repo/"README.md").write_text("# Demo")
    manifest=tmp_path/"project.json"
    manifest.write_text(json.dumps({"schema_version":"1.0","project_id":"demo","name":"Demo","repository":{"path":str(repo)}}))
    db=tmp_path/"neos.db"
    assert init_project(db,manifest)=="demo"
    result=scan_project(db,"demo",repo)
    assert result["file_count"]==1
    summary=project_summary(db,"demo")
    assert summary["counts"]["documentation"]==1
