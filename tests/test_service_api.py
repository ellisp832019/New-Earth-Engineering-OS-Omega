from __future__ import annotations

import json
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from neos.core import init_project, scan_project
from neos.flight import build_project_flight
from neos.genome import build_project_genome
from neos.memory import build_project_memory
from neos.service.app import create_service_server


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


def _post_json(url: str, payload: dict[str, object]):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_service_endpoints_and_local_binding(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "README.md").write_text("# Demo\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    _commit(repo, "feat: initial demo")

    db = tmp_path / "neos.db"
    manifest = tmp_path / "project.json"
    manifest.write_text(_manifest(repo))
    init_project(db, manifest)
    scan_project(db, "demo", repo)
    build_project_genome(db, "demo")
    build_project_memory(db, "demo")
    build_project_flight(db, "demo")

    server, thread = _start_server(db)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, health = _get_json(f"{base}/health")
        assert status == 200
        assert health["status"] == "healthy"
        assert health["service_name"] == "NEOS Local Service"
        assert health["service_version"] == "1.0.0"
        assert health["api_version"] == "v1"
        assert health["schema_version"] == 11
        assert health["instance_id"]
        assert health["ai"]["settings"]["provider_id"] == "mock"
        assert health["command_centre"]["open_work_items"] >= 0

        status, projects = _get_json(f"{base}/projects")
        assert status == 200
        assert projects["projects"][0]["project_id"] == "demo"

        status, ecosystem_search = _get_json(f"{base}/ecosystem/search?q=demo")
        assert status == 200
        assert ecosystem_search["count"] >= 1

        status, today = _get_json(f"{base}/today")
        assert status == 200
        assert today["work_queue"]["count"] >= 0

        status, queue = _get_json(f"{base}/work")
        assert status == 200
        assert "items" in queue

        status, search = _get_json(f"{base}/search?q=demo")
        assert status == 200
        assert search["query"] == "demo"

        status, providers = _get_json(f"{base}/ai/providers")
        assert status == 200
        assert providers["providers"][0]["provider_id"] in {"none", "mock"}

        status, ai_settings = _get_json(f"{base}/ai/settings")
        assert status == 200
        assert ai_settings["settings"]["provider_id"] == "mock"

        status, ai_response = _post_json(
            f"{base}/ai/query",
            {
                "project_ids": ["demo"],
                "question": "What should I work on next?",
                "mode": "plan",
            },
        )
        assert status == 200
        assert ai_response["status"] == "success"
        assert ai_response["request_id"]
        assert ai_response["conversation_id"]
        assert ai_response["project_ids"] == ["demo"]

        status, citations = _get_json(f"{base}/ai/requests/{ai_response['request_id']}/citations")
        assert status == 200
        assert citations["request_id"] == ai_response["request_id"]

        status, inbox = _get_json(f"{base}/decisions/intelligence/inbox?project_id=demo")
        assert status == 200
        assert "items" in inbox

        status, next_actions = _get_json(f"{base}/decisions/intelligence/next-actions?project_id=demo")
        assert status == 200
        assert "items" in next_actions

        status, readiness = _get_json(f"{base}/decisions/intelligence/release-readiness?project_id=demo")
        assert status == 200
        assert readiness["project_id"] == "demo"

        status, evaluate = _post_json(
            f"{base}/decisions/intelligence/evaluate",
            {
                "project_id": "demo",
                "title": "What should we do next?",
                "description": "Prioritise the highest-impact work.",
                "decision_type": "engineering_next_action",
                "scope": "project",
            },
        )
        assert status == 200
        assert evaluate["recommendation"]["recommended_option"]

        status, compare = _post_json(
            f"{base}/decisions/intelligence/compare",
            {
                "question": "Compare architectures",
                "decision_type": "architecture",
                "options": [
                    {"name": "Option A", "description": "Keep current architecture."},
                    {"name": "Option B", "description": "Introduce a shared module."},
                ],
            },
        )
        assert status == 200
        assert compare["recommendation"]["recommended_option"]

        status, accept = _post_json(
            f"{base}/decisions/intelligence/accept/{evaluate['question']['id']}",
            {"operator": "tester", "selected_option": evaluate["recommendation"]["recommended_option"]},
        )
        assert status == 200
        assert accept["status"] == "accepted"

        status, history = _get_json(f"{base}/decisions/intelligence/history?project_id=demo")
        assert status == 200
        assert history["count"] >= 1

        status, requirements = _get_json(f"{base}/requirements/intelligence?project_id=demo")
        assert status == 200
        assert requirements["project_count"] == 1
        assert requirements["requirement_count"] >= 0

        status, refresh = _post_json(f"{base}/projects/demo/refresh", {"scan": False, "requirements": True, "work_queue": True})
        assert status == 200
        assert refresh["project_id"] == "demo"
        assert refresh["status"] == "completed"

        status, refresh_job = _get_json(f"{base}/refresh/{refresh['job_id']}")
        assert status == 200
        assert refresh_job["job_id"] == refresh["job_id"]

        status, session = _get_json(f"{base}/session")
        assert status == 200
        assert session["session_key"] == "workspace"

        status, requirement_inventory = _get_json(f"{base}/requirements/intelligence/inventory?project_id=demo")
        assert status == 200
        assert "items" in requirement_inventory

        status, requirement_gaps = _get_json(f"{base}/requirements/intelligence/gaps?project_id=demo")
        assert status == 200
        assert "items" in requirement_gaps

        status, registered = _post_json(f"{base}/projects/register", {"manifest_path": str(manifest)})
        assert status == 200
        assert registered["project_id"] == "demo"

        status, scan = _post_json(f"{base}/projects/demo/scan", {"repo_path": str(repo)})
        assert status == 200
        assert scan["project_id"] == "demo"
        assert scan["status"] == "scanned"

        status, summary = _get_json(f"{base}/projects/demo/summary")
        assert status == 200
        assert summary["project_id"] == "demo"

        status, genome = _get_json(f"{base}/projects/demo/genome")
        assert status == 200
        assert genome["project_id"] == "demo"

        status, project = _get_json(f"{base}/projects/demo")
        assert status == 200
        assert project["project"]["project_id"] == "demo"

        status, memory = _get_json(f"{base}/projects/demo/memory")
        assert status == 200
        assert memory["project_id"] == "demo"

        status, flight = _get_json(f"{base}/projects/demo/flight")
        assert status == 200
        assert flight["project_id"] == "demo"

        status, timeline = _get_json(f"{base}/projects/demo/flight/timeline")
        assert status == 200
        assert timeline["project_id"] == "demo"

        status, regressions = _get_json(f"{base}/projects/demo/flight/regressions")
        assert status == 200
        assert regressions["project_id"] == "demo"

        status, forbidden = _post_json(f"{base}/shutdown", {"shutdown_token": "wrong"})
        assert status == 403
        assert forbidden["error"] == "forbidden"

        status, invalid = _get_json(f"{base}/projects/missing/summary")
        assert status == 404
        assert invalid["error"] == "not_found"

        with pytest.raises(ValueError):
            create_service_server(db, host="0.0.0.0", port=0)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
