from __future__ import annotations

import json
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

from neos.cli import main
from neos.core import init_project, scan_project
from neos.flight import build_project_flight
from neos.genome import build_project_genome
from neos.memory import build_project_memory
from neos.service.app import create_service_server
from neos.workspace import workspace_context, workspace_inventory


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "user.name", "Tester")


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _manifest(repo: Path, project_id: str, name: str, *, tags: list[str] | None = None) -> str:
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "project_id": project_id,
        "name": name,
        "repository": {"path": str(repo)},
    }
    if tags:
        payload["tags"] = tags
    return json.dumps(payload)


def _start_server(db: Path):
    server = create_service_server(db, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _get_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _build_registered_project(db: Path, repo: Path, project_id: str, *, name: str, tags: list[str] | None = None) -> None:
    manifest = repo.parent / f"{project_id}.json"
    manifest.write_text(_manifest(repo, project_id, name, tags=tags))
    init_project(db, manifest)
    scan_project(db, project_id, repo)
    build_project_genome(db, project_id)
    build_project_memory(db, project_id)
    build_project_flight(db, project_id)


def test_workspace_context_and_inventory_filtering(tmp_path: Path):
    db = tmp_path / "neos.db"

    first_repo = tmp_path / "first"
    first_repo.mkdir()
    _init_repo(first_repo)
    (first_repo / "README.md").write_text("# First\n")
    (first_repo / "src").mkdir()
    (first_repo / "src" / "app.py").write_text("def run():\n    return True\n")
    _commit(first_repo, "feat: first")
    _build_registered_project(db, first_repo, "first", name="First Project")

    vendor_repo = tmp_path / "vendor"
    vendor_repo.mkdir()
    _init_repo(vendor_repo)
    (vendor_repo / "README.md").write_text("# Vendor\n")
    _commit(vendor_repo, "feat: vendor")
    _build_registered_project(db, vendor_repo, "vendor", name="Vendor Project", tags=["vendor"])

    context = workspace_context(db, "first")
    assert context["project_id"] == "first"
    assert context["classification"]["is_first_party"] is True
    assert context["summary"]["project_id"] == "first"
    assert context["integration"]["readiness"] in {"READY", "READY_WITH_GAPS", "NOT_READY", "UNKNOWN"}
    assert context["dependencies"]["reconciled"]["status"] in {"NOT_APPLICABLE", "VERIFIED", "PARTIALLY_VERIFIED", "STALE", "DRIFTED", "CONFLICT", "UNKNOWN"}

    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()
    _init_repo(empty_repo)
    (empty_repo / "notes.txt").write_text("just an empty repository\n")
    _commit(empty_repo, "chore: empty")
    degraded = workspace_context(db, "ghost", repo_path=empty_repo)
    assert degraded["project_id"] == "ghost"
    assert degraded["classification"]["classification"] == "UNKNOWN"
    assert degraded["integration"]["readiness"] == "NOT_READY"
    assert degraded["repository"]["exists"] is True
    assert degraded["freshness"]["status"] in {"LIVE", "NO_SCAN", "UNKNOWN"}

    inventory = workspace_inventory(db)
    assert inventory["project_count"] == 1
    assert inventory["items"][0]["project_id"] == "first"

    inventory_all = workspace_inventory(db, exclude_non_first_party=False)
    assert inventory_all["project_count"] == 2


def test_workspace_service_routes_and_cli(tmp_path: Path, capsys):
    db = tmp_path / "neos.db"
    repo = tmp_path / "demo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    _commit(repo, "feat: demo")
    _build_registered_project(db, repo, "demo", name="Demo Project")

    server, _thread = _start_server(db)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, workspace = _get_json(f"{base}/workspace")
        assert status == 200
        assert workspace["project_count"] == 1

        status, project_workspace = _get_json(f"{base}/workspace/demo")
        assert status == 200
        assert project_workspace["project_id"] == "demo"

        status, project_payload = _get_json(f"{base}/projects/demo")
        assert status == 200
        assert project_payload["workspace"]["project_id"] == "demo"

        status, classification = _get_json(f"{base}/workspace/demo/classification")
        assert status == 200
        assert classification["project_id"] == "demo"
        assert classification["classification"] in {"FIRST_PARTY_ACTIVE", "FIRST_PARTY_INCOMPLETE", "EXPERIMENTAL", "LEGACY", "ARCHIVED"}

        status, summary = _get_json(f"{base}/workspace/demo/summary")
        assert status == 200
        assert summary["project_id"] == "demo"

        status, inventory_all = _get_json(f"{base}/workspace?include_non_first_party=true")
        assert status == 200
        assert inventory_all["project_count"] == 1

        exit_code = main(["--db", str(db), "workspace", "summary", "demo"])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert '"project_id": "demo"' in output
    finally:
        server.shutdown()
        server.server_close()
