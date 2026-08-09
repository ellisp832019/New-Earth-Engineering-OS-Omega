from __future__ import annotations

import json
import subprocess
from pathlib import Path

from neos.core import init_project, scan_project
from neos.registry import (
    architecture_impact,
    architecture_registry,
    discover_contract_sources,
    validate_contract_document,
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


def _manifest(repo: Path, project_id: str, name: str) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": project_id,
            "name": name,
            "repository": {"path": str(repo)},
            "technologies": ["Python", "Markdown"],
        }
    )


def test_registry_snapshot_and_contract_sources(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    (repo / "contracts").mkdir()
    contract_path = repo / "contracts" / "capabilities.json"
    contract_path.write_text(
        json.dumps(
            {
                "contract_type": "CAPABILITIES",
                "schema_version": 1,
                "project_id": "demo",
                "contract_version": "0.1",
                "status": "active",
                "declared_source": "contracts/capabilities.json",
            }
        )
    )
    _commit(repo, "feat: demo project")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo, "demo", "Demo"))
    init_project(db, manifest)
    scan_project(db, "demo", repo)

    sources = discover_contract_sources(repo, manifest)
    assert any(Path(item["path"]) == contract_path for item in sources)
    assert any(item["contract_type"] == "CAPABILITIES" for item in sources)
    assert validate_contract_document(sources[0]["document"])["project_id"] == "demo"

    registry = architecture_registry(db, "demo")
    assert registry["project_id"] == "demo"
    assert registry["identity"]["project_id"] == "demo"
    assert registry["contracts"]["project"]["contract_type"] == "PROJECT_CONTRACT"
    assert registry["contracts"]["project"]["provenance"]["declared"] == "manifest"
    assert registry["contracts"]["project"]["provenance"]["observed"] == "project_registry_v2"
    assert registry["contracts"]["project"]["provenance"]["derived"] == ["stable_identity", "project_type", "project_family"]
    assert registry["contracts"]["capabilities"]["contract_type"] == "CAPABILITIES"
    assert registry["contracts"]["capabilities"]["provenance"]["observed"] == "registry+scan"
    assert registry["contracts"]["dependencies"]["contract_type"] == "DEPENDENCIES"
    assert registry["contracts"]["dependencies"]["provenance"]["observed"] == "project_registry_v2"
    assert registry["contracts"]["safety_boundary"]["contract_type"] == "SAFETY_BOUNDARY"
    assert registry["contracts"]["release_state"]["contract_type"] == "RELEASE_STATE"
    assert registry["drift"]["contracts"]["project"]["contract_type"] == "PROJECT_CONTRACT"
    assert registry["drift"]["contracts"]["safety_boundary"]["contract_type"] == "SAFETY_BOUNDARY"
    assert registry["impact"]["summary"]["project_identity"]["project_id"] == "demo"
    assert registry["drift"]["status"] in {"healthy", "review_required"}
    assert registry["health"]["project_count"] == 1


def test_registry_cross_project_compare_is_read_only(tmp_path: Path):
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    _init_repo(source_repo)
    (source_repo / "README.md").write_text("# Source\n")
    (source_repo / "src").mkdir()
    (source_repo / "src" / "main.py").write_text("def run():\n    return 1\n")
    _commit(source_repo, "feat: source")

    peer_repo = tmp_path / "peer"
    peer_repo.mkdir()
    _init_repo(peer_repo)
    (peer_repo / "README.md").write_text("# Peer\n")
    (peer_repo / "src").mkdir()
    (peer_repo / "src" / "main.py").write_text("def run():\n    return 2\n")
    (peer_repo / "project.neos.json").write_text(_manifest(peer_repo, "peer", "Peer"))
    _commit(peer_repo, "feat: peer")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "source.json"
    manifest.write_text(_manifest(source_repo, "source", "Source"))
    init_project(db, manifest)
    scan_project(db, "source", source_repo)

    before_head = subprocess.check_output(["git", "-C", str(peer_repo), "rev-parse", "HEAD"], text=True).strip()
    before_status = subprocess.check_output(["git", "-C", str(peer_repo), "status", "--short"], text=True).strip()
    impact = architecture_impact(db, "source", peer_repo_path=peer_repo)
    after_head = subprocess.check_output(["git", "-C", str(peer_repo), "rev-parse", "HEAD"], text=True).strip()
    after_status = subprocess.check_output(["git", "-C", str(peer_repo), "status", "--short"], text=True).strip()

    assert before_head == after_head
    assert before_status == after_status
    assert impact["project_id"] == "source"
    assert impact["summary"]["peer_identity"]["project_id"] == "peer"
    assert impact["summary"]["relationship_state"] in {"independent", "related"}
