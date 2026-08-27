from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

import neos.ecosystem as ecosystem_module
from neos.core import init_project, scan_project
from neos.db import connect, ensure_database
from neos.flight import build_project_flight
from neos.genome import build_project_genome
from neos.memory import build_project_memory
from neos.service.app import create_service_server


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


def _manifest(repo: Path) -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "project_id": "microgrow-v1",
            "name": "MicroGrow",
            "repository": {"path": str(repo)},
        }
    )


def _start_server(db: Path):
    server = create_service_server(db, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _get_json(url: str, timeout: float = 4.0):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _table_counts(db: Path) -> dict[str, int]:
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        conn.row_factory = sqlite3.Row
        return {
            "ai_settings": conn.execute("SELECT COUNT(*) FROM ai_settings").fetchone()[0],
            "ecosystems": conn.execute("SELECT COUNT(*) FROM ecosystems").fetchone()[0],
            "portfolio_snapshots": conn.execute("SELECT COUNT(*) FROM portfolio_snapshots").fetchone()[0],
        }
    finally:
        conn.close()


def test_connect_skips_schema_reinitialization_for_current_db(tmp_path: Path):
    db = tmp_path / "neos.db"
    ensure_database(db)
    before = _table_counts(db)

    with patch("neos.db._initialize_database", side_effect=AssertionError("connect should not rerun schema init")) as init_mock:
        conn = connect(db)
        try:
            assert conn.execute("SELECT 1").fetchone()[0] == 1
        finally:
            conn.close()

    after = _table_counts(db)
    assert before == after
    assert init_mock.call_count == 0


def test_service_read_endpoints_are_prompt_and_read_only(tmp_path: Path):
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
    scan_project(db, "microgrow-v1", repo)
    build_project_genome(db, "microgrow-v1")
    build_project_memory(db, "microgrow-v1")
    build_project_flight(db, "microgrow-v1")

    before = _table_counts(db)
    server, thread = _start_server(db)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        endpoints = [
            ("/health", "status", "healthy"),
            ("/projects", "projects", None),
            ("/projects/microgrow-v1/summary", "project_id", "microgrow-v1"),
        ]
        for path, key, expected in endpoints:
            start = time.perf_counter()
            status, payload = _get_json(f"{base}{path}")
            elapsed = time.perf_counter() - start
            assert status == 200
            assert elapsed < 4.0
            if expected is not None:
                assert payload[key] == expected
            assert payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    after = _table_counts(db)
    assert before == after


def test_health_with_multiple_projects_remains_read_only(tmp_path: Path):
    def make_project(project_id: str, filename: str) -> tuple[Path, Path]:
        repo = tmp_path / project_id
        repo.mkdir()
        _init_repo(repo)
        (repo / "README.md").write_text(f"# {project_id}\n")
        (repo / "src").mkdir()
        (repo / "src" / filename).write_text("def run():\n    return True\n")
        _commit(repo, f"feat: {project_id}")
        manifest = tmp_path / f"{project_id}.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "project_id": project_id,
                    "name": project_id,
                    "repository": {"path": str(repo)},
                }
            )
        )
        return repo, manifest

    repo_a, manifest_a = make_project("alpha", "alpha.py")
    repo_b, manifest_b = make_project("beta", "beta.py")

    db = tmp_path / "neos-multi.db"
    init_project(db, manifest_a)
    scan_project(db, "alpha", repo_a)
    init_project(db, manifest_b)
    scan_project(db, "beta", repo_b)

    before = _table_counts(db)
    original_loader = ecosystem_module._load_project_entry
    with patch("neos.ecosystem._load_project_entry", wraps=original_loader) as loader:
        server, thread = _start_server(db)
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            start = time.perf_counter()
            status, payload = _get_json(f"{base}/health")
            elapsed = time.perf_counter() - start
            assert status == 200
            assert elapsed < 4.0
            assert payload["registered_projects"] == 2
            assert payload["portfolio_health"]["project_count"] == 2
            assert loader.call_count == 2
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    after = _table_counts(db)
    assert before == after
