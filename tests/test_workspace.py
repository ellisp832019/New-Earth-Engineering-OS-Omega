from __future__ import annotations

import json
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

from neos.cli import main
from neos.core import init_project, scan_project
from neos.db import connect
from neos.flight import build_project_flight
from neos.genome import build_project_genome
from neos.memory import build_project_memory
from neos.service.app import create_service_server
from neos.workspace import (
    workspace_context,
    workspace_inventory,
    workspace_section,
    workspace_summary,
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


def _manifest(
    repo: Path,
    project_id: str,
    name: str,
    *,
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
    safety_boundary: dict[str, object] | None = None,
) -> str:
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


def _build_registered_project(
    db: Path,
    repo: Path,
    project_id: str,
    *,
    name: str,
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
    safety_boundary: dict[str, object] | None = None,
) -> None:
    manifest = repo.parent / f"{project_id}.json"
    manifest.write_text(_manifest(repo, project_id, name, tags=tags))
    if dependencies is not None or safety_boundary is not None:
        contract_dir = repo / "contracts"
        contract_dir.mkdir(exist_ok=True)
    if dependencies is not None:
        (contract_dir / "dependencies.json").write_text(
            json.dumps(
                {
                    "contract_type": "DEPENDENCIES",
                    "schema_version": 1,
                    "project_id": project_id,
                    "contract_version": "0.1",
                    "status": "active",
                    "declared_source": str(contract_dir / "dependencies.json"),
                    "source_identity": str(repo),
                    "metadata": {"declared_dependencies": dependencies},
                }
            )
        )
    if safety_boundary is not None:
        (contract_dir / "safety_boundary.json").write_text(
            json.dumps(
                {
                    "contract_type": "SAFETY_BOUNDARY",
                    "schema_version": 1,
                    "project_id": project_id,
                    "contract_version": "0.1",
                    "status": "active",
                    "declared_source": str(contract_dir / "safety_boundary.json"),
                    "source_identity": str(repo),
                    "metadata": safety_boundary,
                }
            )
        )
    init_project(db, manifest)
    scan_project(db, project_id, repo)
    build_project_genome(db, project_id)
    build_project_memory(db, project_id)
    build_project_flight(db, project_id)


def _db_counts(db: Path) -> dict[str, int]:
    conn = connect(db)
    tables = [
        "scans",
        "memory_records",
        "memory_relationships",
        "memory_snapshots",
        "flight_snapshots",
        "flight_events",
        "flight_transitions",
        "ecosystems",
        "portfolio_snapshots",
        "project_relationships",
    ]
    counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    conn.close()
    return counts


def _seed_dependency_snapshot(db: Path, source_project_id: str, target_project_ids: list[str], *, snapshot_id: str) -> None:
    conn = connect(db)
    project_ids = [source_project_id, *target_project_ids]
    ecosystem_id = f"ecosystem-{snapshot_id}"
    conn.execute(
        "INSERT OR REPLACE INTO ecosystems(id, name, created_at, updated_at, project_ids, snapshot_id, schema_version, metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        (
            ecosystem_id,
            "test",
            "2026-08-07T00:00:00Z",
            "2026-08-07T00:00:00Z",
            json.dumps(project_ids),
            snapshot_id,
            1,
            json.dumps({"source": "test"}),
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO portfolio_snapshots(id, name, ecosystem_id, project_ids, source_fingerprint, created_at, snapshot_json, metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        (
            snapshot_id,
            "test",
            ecosystem_id,
            json.dumps(project_ids),
            f"fingerprint-{snapshot_id}",
            "2026-08-07T00:00:00Z",
            json.dumps({"project_ids": project_ids, "projects": []}),
            json.dumps({"source": "test"}),
        ),
    )
    for index, target_project_id in enumerate(target_project_ids):
        relationship_id = f"rel-{snapshot_id}-{index}"
        conn.execute(
            "INSERT OR REPLACE INTO project_relationships(id, portfolio_snapshot_id, source_project_id, target_project_id, relationship_type, confidence, evidence_json, detector, created_at, metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                relationship_id,
                snapshot_id,
                source_project_id,
                target_project_id,
                "cross_project_dependency",
                0.9,
                json.dumps({"source": "manifest", "project_id": source_project_id, "target_project_id": target_project_id}),
                "test",
                "2026-08-07T00:00:00Z",
                json.dumps({"source": "test"}),
            ),
        )
    conn.commit()
    conn.close()


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


def test_workspace_safety_provenance_and_read_purity(tmp_path: Path):
    db = tmp_path / "neos.db"

    none_repo = tmp_path / "none"
    none_repo.mkdir()
    _init_repo(none_repo)
    (none_repo / "README.md").write_text("# None\n")
    _commit(none_repo, "feat: none")
    _build_registered_project(db, none_repo, "safety-none", name="Safety None")

    true_repo = tmp_path / "true"
    true_repo.mkdir()
    _init_repo(true_repo)
    (true_repo / "README.md").write_text("# True\n")
    _commit(true_repo, "feat: true")
    _build_registered_project(
        db,
        true_repo,
        "safety-true",
        name="Safety True",
        safety_boundary={
            "local_only_operation": True,
            "cloud_allowed": False,
            "device_flashing_allowed": False,
            "actuator_authority": False,
            "operator_approval_required": True,
        },
    )

    false_repo = tmp_path / "false"
    false_repo.mkdir()
    _init_repo(false_repo)
    (false_repo / "README.md").write_text("# False\n")
    _commit(false_repo, "feat: false")
    _build_registered_project(
        db,
        false_repo,
        "safety-false",
        name="Safety False",
        safety_boundary={
            "local_only_operation": False,
            "cloud_allowed": True,
            "device_flashing_allowed": True,
            "actuator_authority": True,
            "operator_approval_required": False,
        },
    )

    partial_repo = tmp_path / "partial"
    partial_repo.mkdir()
    _init_repo(partial_repo)
    (partial_repo / "README.md").write_text("# Partial\n")
    _commit(partial_repo, "feat: partial")
    _build_registered_project(
        db,
        partial_repo,
        "safety-partial",
        name="Safety Partial",
        safety_boundary={
            "cloud_allowed": True,
            "operator_approval_required": False,
        },
    )

    none_workspace = workspace_context(db, "safety-none")
    assert none_workspace["safety"]["platform_authority"]["actuator_authority"] == {
        "state": "FALSE",
        "source": "NEOS_PLATFORM_BOUNDARY",
    }
    for key in ("local_only_operation", "cloud_allowed", "device_flashing_allowed", "actuator_authority", "operator_approval_required"):
        assert none_workspace["safety"]["summary"][key]["state"] == "UNKNOWN"
        assert none_workspace["safety"]["summary"][key]["source"] == "UNKNOWN"

    true_workspace = workspace_context(db, "safety-true")
    assert true_workspace["safety"]["summary"]["local_only_operation"] == {
        "state": "TRUE",
        "source": "DECLARED_CONTRACT",
    }
    assert true_workspace["safety"]["summary"]["cloud_allowed"] == {
        "state": "FALSE",
        "source": "DECLARED_CONTRACT",
    }

    false_workspace = workspace_context(db, "safety-false")
    assert false_workspace["safety"]["summary"]["local_only_operation"] == {
        "state": "FALSE",
        "source": "DECLARED_CONTRACT",
    }
    assert false_workspace["safety"]["summary"]["cloud_allowed"] == {
        "state": "TRUE",
        "source": "DECLARED_CONTRACT",
    }

    partial_workspace = workspace_context(db, "safety-partial")
    assert partial_workspace["safety"]["summary"]["cloud_allowed"] == {
        "state": "TRUE",
        "source": "DECLARED_CONTRACT",
    }
    assert partial_workspace["safety"]["summary"]["operator_approval_required"] == {
        "state": "FALSE",
        "source": "DECLARED_CONTRACT",
    }
    assert partial_workspace["safety"]["summary"]["local_only_operation"]["state"] == "UNKNOWN"
    assert partial_workspace["safety"]["summary"]["device_flashing_allowed"]["state"] == "UNKNOWN"
    assert partial_workspace["safety"]["summary"]["actuator_authority"]["state"] == "UNKNOWN"

    before = _db_counts(db)
    context_one = workspace_context(db, "safety-partial")
    summary_one = workspace_summary(db, "safety-partial")
    inventory_one = workspace_inventory(db, exclude_non_first_party=False)
    section_one = workspace_section(db, "safety-partial", "safety")
    after = _db_counts(db)

    assert before == after
    assert workspace_context(db, "safety-partial")["safety"] == context_one["safety"]
    assert workspace_context(db, "safety-partial")["dependencies"] == context_one["dependencies"]
    assert workspace_context(db, "safety-partial")["classification"] == context_one["classification"]
    assert workspace_context(db, "safety-partial")["integration"] == context_one["integration"]
    assert workspace_context(db, "safety-partial")["repository"] == context_one["repository"]
    assert workspace_context(db, "safety-partial")["provenance"] == context_one["provenance"]
    assert workspace_context(db, "safety-partial")["evidence"] == context_one["evidence"]
    assert workspace_context(db, "safety-partial")["freshness"] == context_one["freshness"]
    assert workspace_summary(db, "safety-partial") == summary_one
    assert workspace_inventory(db, exclude_non_first_party=False) == inventory_one
    assert workspace_section(db, "safety-partial", "safety") == section_one


def test_workspace_dependency_reconciliation_and_provenance(tmp_path: Path):
    db = tmp_path / "neos.db"

    peer_a_repo = tmp_path / "peer-a"
    peer_a_repo.mkdir()
    _init_repo(peer_a_repo)
    (peer_a_repo / "README.md").write_text("# Peer A\n")
    _commit(peer_a_repo, "feat: peer-a")
    _build_registered_project(db, peer_a_repo, "peer-a", name="Peer A")

    peer_b_repo = tmp_path / "peer-b"
    peer_b_repo.mkdir()
    _init_repo(peer_b_repo)
    (peer_b_repo / "README.md").write_text("# Peer B\n")
    _commit(peer_b_repo, "feat: peer-b")
    _build_registered_project(db, peer_b_repo, "peer-b", name="Peer B")

    peer_c_repo = tmp_path / "peer-c"
    peer_c_repo.mkdir()
    _init_repo(peer_c_repo)
    (peer_c_repo / "README.md").write_text("# Peer C\n")
    _commit(peer_c_repo, "feat: peer-c")
    _build_registered_project(db, peer_c_repo, "peer-c", name="Peer C")

    empty_repo = tmp_path / "dep-empty"
    empty_repo.mkdir()
    _init_repo(empty_repo)
    (empty_repo / "README.md").write_text("# Empty\n")
    _commit(empty_repo, "feat: empty")
    _build_registered_project(db, empty_repo, "dep-empty", name="Dependency Empty")

    declared_only_repo = tmp_path / "dep-declared-only"
    declared_only_repo.mkdir()
    _init_repo(declared_only_repo)
    (declared_only_repo / "README.md").write_text("# Declared Only\n")
    _commit(declared_only_repo, "feat: declared-only")
    _build_registered_project(
        db,
        declared_only_repo,
        "dep-declared-only",
        name="Dependency Declared Only",
        dependencies=["peer-a"],
    )

    stale_repo = tmp_path / "dep-stale"
    stale_repo.mkdir()
    _init_repo(stale_repo)
    (stale_repo / "README.md").write_text("# Stale\n")
    _commit(stale_repo, "feat: stale")
    _build_registered_project(
        db,
        stale_repo,
        "dep-stale",
        name="Dependency Stale",
        dependencies=["peer-a"],
    )
    _seed_dependency_snapshot(db, "dep-stale", [], snapshot_id="snapshot-dep-stale")

    match_repo = tmp_path / "dep-match"
    match_repo.mkdir()
    _init_repo(match_repo)
    (match_repo / "README.md").write_text("# Match\n")
    _commit(match_repo, "feat: match")
    _build_registered_project(
        db,
        match_repo,
        "dep-match",
        name="Dependency Match",
        dependencies=["peer-a"],
    )
    _seed_dependency_snapshot(db, "dep-match", ["peer-a"], snapshot_id="snapshot-dep-match")

    observed_only_repo = tmp_path / "dep-observed-only"
    observed_only_repo.mkdir()
    _init_repo(observed_only_repo)
    (observed_only_repo / "README.md").write_text("# Observed Only\n")
    _commit(observed_only_repo, "feat: observed-only")
    _build_registered_project(db, observed_only_repo, "dep-observed-only", name="Dependency Observed Only")
    _seed_dependency_snapshot(db, "dep-observed-only", ["peer-a"], snapshot_id="snapshot-dep-observed-only")

    partial_repo = tmp_path / "dep-partial"
    partial_repo.mkdir()
    _init_repo(partial_repo)
    (partial_repo / "README.md").write_text("# Partial\n")
    _commit(partial_repo, "feat: partial")
    _build_registered_project(
        db,
        partial_repo,
        "dep-partial",
        name="Dependency Partial",
        dependencies=["peer-a", "peer-b"],
    )
    _seed_dependency_snapshot(db, "dep-partial", ["peer-a", "peer-c"], snapshot_id="snapshot-dep-partial")

    conflict_repo = tmp_path / "dep-conflict"
    conflict_repo.mkdir()
    _init_repo(conflict_repo)
    (conflict_repo / "README.md").write_text("# Conflict\n")
    _commit(conflict_repo, "feat: conflict")
    _build_registered_project(
        db,
        conflict_repo,
        "dep-conflict",
        name="Dependency Conflict",
        dependencies=["peer-a"],
    )
    _seed_dependency_snapshot(db, "dep-conflict", ["peer-b"], snapshot_id="snapshot-dep-conflict")

    empty_workspace = workspace_context(db, "dep-empty")
    assert empty_workspace["dependencies"]["reconciled"]["status"] == "NOT_APPLICABLE"
    assert empty_workspace["dependencies"]["observed_provenance"]["evidence_state"] == "UNKNOWN"
    assert empty_workspace["dependencies"]["observed_provenance"]["source"] == "unknown"

    declared_only_workspace = workspace_context(db, "dep-declared-only")
    assert declared_only_workspace["dependencies"]["reconciled"]["status"] == "UNKNOWN"
    assert declared_only_workspace["dependencies"]["observed_provenance"]["evidence_state"] == "UNKNOWN"
    assert declared_only_workspace["dependencies"]["observed_provenance"]["snapshot_id"] is None

    stale_workspace = workspace_context(db, "dep-stale")
    assert stale_workspace["dependencies"]["reconciled"]["status"] == "STALE"
    assert stale_workspace["dependencies"]["observed_provenance"]["evidence_state"] == "PRESENT"
    assert stale_workspace["dependencies"]["observed_provenance"]["source"] == "project_relationships"
    assert stale_workspace["dependencies"]["observed_provenance"]["snapshot_id"] == "snapshot-dep-stale"

    match_workspace = workspace_context(db, "dep-match")
    assert match_workspace["dependencies"]["reconciled"]["status"] == "VERIFIED"
    assert match_workspace["dependencies"]["reconciled"]["items"][0]["relation"] == "DECLARED_AND_OBSERVED"
    assert match_workspace["dependencies"]["observed_provenance"]["snapshot_id"] == "snapshot-dep-match"

    observed_only_workspace = workspace_context(db, "dep-observed-only")
    assert observed_only_workspace["dependencies"]["reconciled"]["status"] == "DRIFTED"
    assert observed_only_workspace["dependencies"]["reconciled"]["items"][0]["relation"] == "OBSERVED_ONLY"

    partial_workspace = workspace_context(db, "dep-partial")
    assert partial_workspace["dependencies"]["reconciled"]["status"] == "PARTIALLY_VERIFIED"
    assert {item["relation"] for item in partial_workspace["dependencies"]["reconciled"]["items"]} == {"DECLARED_AND_OBSERVED", "DECLARED_ONLY", "OBSERVED_ONLY"}

    conflict_workspace = workspace_context(db, "dep-conflict")
    assert conflict_workspace["dependencies"]["reconciled"]["status"] == "CONFLICT"
    assert {item["relation"] for item in conflict_workspace["dependencies"]["reconciled"]["items"]} == {"DECLARED_ONLY", "OBSERVED_ONLY"}


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
