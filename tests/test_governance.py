from __future__ import annotations

import copy
import hashlib
import os
import re

import pytest
import yaml
import neos.governance as governance_module

import json
import sqlite3
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

from neos.core import init_project, scan_project
from neos.governance import (
    governance_report,
    governance_snapshot,
    governance_status,
)
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


def _manifest(
    repo: Path,
    project_id: str,
    name: str,
    *,
    tags: list[str] | None = None,
    technologies: list[str] | None = None,
    dependencies: list[str] | None = None,
    lifecycle: str = "active",
    status: str = "active",
    capabilities: list[str] | None = None,
) -> str:
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "project_id": project_id,
        "name": name,
        "repository": {"path": str(repo)},
        "lifecycle": lifecycle,
        "tags": tags or [],
        "technologies": technologies or [],
    }
    return json.dumps(payload, sort_keys=True)


def _build_project(
    db: Path,
    repo: Path,
    project_id: str,
    name: str,
    *,
    tags: list[str] | None = None,
    technologies: list[str] | None = None,
    dependencies: list[str] | None = None,
    lifecycle: str = "active",
    status: str = "active",
    capabilities: list[str] | None = None,
    remote: str | None = None,
    extra_source: bool = True,
) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _init_repo(repo)
    (repo / "README.md").write_text(f"# {name}\n")
    if extra_source:
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("def run():\n    return True\n")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_app.py").write_text("def test_run():\n    assert True\n")
    manifest = repo / "project.json"
    manifest.write_text(
        _manifest(
            repo,
            project_id,
            name,
            tags=tags,
            technologies=technologies,
            dependencies=dependencies,
            lifecycle=lifecycle,
            status=status,
            capabilities=capabilities,
        )
    )
    if remote:
        _git(repo, "remote", "add", "origin", remote)
    _commit(repo, f"feat: {project_id}")
    init_project(db, manifest)
    scan_project(db, project_id, repo)


def _seed_dependency_snapshot(db: Path, source_project_id: str, target_project_ids: list[str], *, snapshot_id: str) -> None:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    ecosystem_id = f"ecosystem-{snapshot_id}"
    conn.execute(
        "INSERT OR REPLACE INTO ecosystems(id, name, created_at, updated_at, project_ids, snapshot_id, schema_version, metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        (
            ecosystem_id,
            "default",
            "2026-08-10T00:00:00Z",
            "2026-08-10T00:00:00Z",
            json.dumps(sorted({source_project_id, *target_project_ids})),
            snapshot_id,
            1,
            json.dumps({"source": "test"}),
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO portfolio_snapshots(id, name, ecosystem_id, project_ids, source_fingerprint, created_at, snapshot_json, metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        (
            snapshot_id,
            "default",
            ecosystem_id,
            json.dumps(sorted({source_project_id, *target_project_ids})),
            f"fingerprint-{snapshot_id}",
            "2026-08-10T00:00:00Z",
            json.dumps({"project_ids": sorted({source_project_id, *target_project_ids})}),
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
                "2026-08-10T00:00:00Z",
                json.dumps({"source": "test"}),
            ),
        )
    conn.commit()
    conn.close()


CORE_ROOT = Path(os.environ.get("A04_CORE_ROOT", r"D:\Dev\Projects\New-Earth-Platform-Core-Omega"))
CORE_REVISION = "7dae83b5591393b62fb5fc7ed8a6a6560bc53e03"
CORE_HASHES = {
    "registry/governance.yaml": "E11BB6DEAACD1E9052AD810A7521E838C606088ED131332A257B0CA0BEAABAF0",
    "schemas/governance.schema.json": "199D02E4DBC49B16C25C8B6F1D1B3CCE29CB13506DC73E82995F89032145E71B",
}
_INTERNAL_RULE_INPUTS = {}


def _core_inputs():
    # Canonical producer provenance, never an independently invented producer schema.
    for relative, expected in CORE_HASHES.items():
        assert hashlib.sha256((CORE_ROOT / relative).read_bytes()).hexdigest().upper() == expected
    assert subprocess.check_output(["git", "-C", str(CORE_ROOT), "rev-parse", "HEAD"], text=True).strip() == CORE_REVISION
    return (yaml.safe_load((CORE_ROOT / "registry/governance.yaml").read_text(encoding="utf-8")),
            json.loads((CORE_ROOT / "schemas/governance.schema.json").read_text(encoding="utf-8")))


def _write_canonical(root, document=None, schema=None):
    canonical, canonical_schema = _core_inputs()
    (root / "registry").mkdir(parents=True, exist_ok=True)
    (root / "schemas").mkdir(parents=True, exist_ok=True)
    (root / "registry/governance.yaml").write_text(json.dumps(canonical if document is None else document), encoding="utf-8")
    (root / "schemas/governance.schema.json").write_text(json.dumps(canonical_schema if schema is None else schema), encoding="utf-8")
    return root


def _write_platform_core(root: Path, *, estate_roots: list[Path], systems: list[dict[str, object]]) -> Path:
    document, schema = _core_inputs()
    template = document["systems"][0]
    records = []
    for item in systems:
        record = copy.deepcopy(template)
        record["id"] = re.sub(r"[^a-z0-9_-]", "-", str(item["system_id"]).lower())
        record["canonical_name"] = item["name"]
        record["ownership"]["system_owner"] = item["canonical_owner"]
        record["repository"] = {"canonical_repo": item["name"], "current_location": item["name"]}
        records.append(record)
    document["systems"] = records
    document["planned_extractions"] = []
    _INTERNAL_RULE_INPUTS[str(root)] = {"systems": systems, "estate_roots": [str(p) for p in estate_roots]}
    return _write_canonical(root, document, schema)


def _use_internal_finding_inputs(monkeypatch):
    """Old broad rule cases test internal normalized findings, NOT producer acceptance."""
    real_load = governance_module._load_platform_core_document

    def load(root):
        normalized, document = real_load(root)
        internal = _INTERNAL_RULE_INPUTS.get(str(root))
        if internal is not None:
            assert normalized["status"] == "AVAILABLE"
            normalized["declared"]["systems"] = governance_module._normalize_declared_systems(internal, {})
            normalized["declared"]["repositories"] = governance_module._normalize_declared_repositories(internal, {})
            normalized["declared"]["estate_roots"] = internal["estate_roots"]
        return normalized, document

    monkeypatch.setattr(governance_module, "_load_platform_core_document", load)


def _find(report: dict[str, object], rule_id: str, system_id: str | None = None) -> list[dict[str, object]]:
    items = [item for item in report["findings"] if item["rule_id"] == rule_id]
    if system_id is not None:
        items = [item for item in items if item.get("system_id") == system_id]
    return items


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


def test_governance_report_covers_core_rules(tmp_path: Path, monkeypatch):
    _use_internal_finding_inputs(monkeypatch)
    db = tmp_path / "neos.db"
    estate_root = tmp_path / "estate"
    estate_root.mkdir()

    neos_repo = tmp_path / "neos"
    _build_project(
        db,
        neos_repo,
        "neos",
        "New-Earth-Engineering-OS-Omega",
        tags=["registry"],
        technologies=["registry"],
        dependencies=[],
        capabilities=["repository_intelligence"],
        remote="https://github.com/ellisp832019/New-Earth-Engineering-OS-Omega.git",
    )

    dashboard_repo = tmp_path / "dashboard"
    _build_project(
        db,
        dashboard_repo,
        "dashboard",
        "New_Earth_Command_Dashboard",
        tags=["registry"],
        technologies=["registry"],
        capabilities=["repository_intelligence"],
        remote="https://github.com/ellisp832019/New-Earth-Command-Dashboard.git",
    )

    microgrow_repo = tmp_path / "microgrow"
    _build_project(
        db,
        microgrow_repo,
        "microgrow",
        "microgrow",
        technologies=["flutter"],
        tags=["first_party"],
        capabilities=["application_shell"],
        dependencies=[],
        remote="https://github.com/ellisp832019/microgrow.git",
    )

    biocalm_repo = tmp_path / "biocalm"
    _build_project(
        db,
        biocalm_repo,
        "biocalm",
        "New-Earth---BioCalm",
        tags=["placeholder"],
        technologies=[],
        lifecycle="concept",
        status="planned",
        capabilities=["placeholder"],
        remote="https://github.com/ellisp832019/New-Earth---BioCalm.git",
        extra_source=False,
    )

    markxl_repo = tmp_path / "markxl"
    _build_project(
        db,
        markxl_repo,
        "markxl",
        "Mark-XL",
        tags=["legacy"],
        technologies=["python"],
        lifecycle="archived",
        status="archived",
        capabilities=["voice_intelligence"],
        remote="https://github.com/ellisp832019/Mark-XL.git",
    )

    reference_repo = tmp_path / "esp32-3248s035"
    _build_project(
        db,
        reference_repo,
        "esp32-3248s035",
        "esp32-3248s035",
        tags=["reference"],
        technologies=["platformio"],
        lifecycle="maintenance",
        status="reference",
        capabilities=["embedded_build_support"],
        remote="https://github.com/ellisp832019/esp32-3248s035.git",
    )

    dep_declared_repo = tmp_path / "dep-declared-only"
    _build_project(
        db,
        dep_declared_repo,
        "dep-declared-only",
        "Declared Only",
        technologies=["python"],
        dependencies=[],
        remote="https://github.com/ellisp832019/dep-declared-only.git",
    )

    dep_observed_repo = tmp_path / "dep-observed-only"
    _build_project(
        db,
        dep_observed_repo,
        "dep-observed-only",
        "Observed Only",
        technologies=["python"],
        remote="https://github.com/ellisp832019/dep-observed-only.git",
    )

    _seed_dependency_snapshot(db, "dep-observed-only", ["microgrow"], snapshot_id="gov-deps")

    rogue_root = estate_root / "New-Earth-Secret-Tool"
    rogue_root.mkdir(parents=True, exist_ok=True)
    _init_repo(rogue_root)
    (rogue_root / "README.md").write_text("# New-Earth-Secret-Tool\n")
    (rogue_root / "project.json").write_text(
        _manifest(
            rogue_root,
            "rogue-secret-tool",
            "New-Earth-Secret-Tool",
            tags=["registry"],
            technologies=["python"],
        )
    )
    _git(rogue_root, "remote", "add", "origin", "https://github.com/ellisp832019/New-Earth-Secret-Tool.git")
    _commit(rogue_root, "feat: rogue-secret-tool")

    missing_repo_path = tmp_path / "missing" / "New-Earth-Experiment-Validation-Engine"

    systems = [
        {
            "system_id": "neos",
            "project_id": "neos",
            "name": "New-Earth-Engineering-OS-Omega",
            "role": "ENGINEERING_INTELLIGENCE",
            "canonical_owner": "NEOS",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(neos_repo),
                "remote": "https://github.com/ellisp832019/New-Earth-Engineering-OS-Omega.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT", "CAPABILITIES"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "dashboard",
            "project_id": "dashboard",
            "name": "New_Earth_Command_Dashboard",
            "role": "OPERATIONS_UI",
            "canonical_owner": "Dashboard",
            "identity_kind": "active independent repository",
            "classification": "operations_ui",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(dashboard_repo),
                "remote": "ssh://git@example.com/wrong/dashboard.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "microgrow",
            "project_id": "microgrow",
            "name": "microgrow",
            "role": "PLATFORM",
            "canonical_owner": "MicroGrow",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(microgrow_repo),
                "remote": "https://github.com/ellisp832019/microgrow.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["application_shell"],
        },
        {
            "system_id": "MicroGrow-Hub",
            "project_id": "MicroGrow-Hub",
            "name": "MicroGrow-Hub",
            "role": "PLANNED_EXTRACTION",
            "canonical_owner": "MicroGrow",
            "identity_kind": "planned future repository",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "MicroGrow-Project-Control-Centre",
            "project_id": "MicroGrow-Project-Control-Centre",
            "name": "MicroGrow-Project-Control-Centre",
            "role": "SHELL",
            "canonical_owner": "MicroGrow",
            "identity_kind": "embedded system",
            "embedded_in": "microgrow",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["command_frontdoor"],
        },
        {
            "system_id": "New-Earth---BioCalm",
            "project_id": "biocalm",
            "name": "New-Earth---BioCalm",
            "role": "PRODUCT",
            "canonical_owner": "BioCalm",
            "identity_kind": "placeholder repository",
            "placeholder": True,
            "lifecycle": "concept",
            "canonical_repository": {
                "path": str(biocalm_repo),
                "remote": "https://github.com/ellisp832019/New-Earth---BioCalm.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["placeholder"],
        },
        {
            "system_id": "Life OS",
            "project_id": "Life OS",
            "name": "Life OS",
            "role": "PRODUCT",
            "canonical_owner": "Life OS",
            "identity_kind": "non-repository system/project identity",
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["non_repository_identity"],
        },
        {
            "system_id": "Embedded Engineering Lab",
            "project_id": "Embedded Engineering Lab",
            "name": "Embedded Engineering Lab",
            "role": "LAB",
            "canonical_owner": "Embedded Engineering Lab",
            "identity_kind": "non-repository system/project identity",
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["non_repository_identity"],
        },
        {
            "system_id": "Mark-XL",
            "project_id": "markxl",
            "name": "Mark-XL",
            "role": "LEGACY",
            "canonical_owner": "Mark-XL",
            "identity_kind": "legacy repository",
            "legacy": True,
            "canonical_repository": {
                "path": str(markxl_repo),
                "remote": "https://github.com/ellisp832019/Mark-XL.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["voice_intelligence"],
        },
        {
            "system_id": "esp32-3248s035",
            "project_id": "esp32-3248s035",
            "name": "esp32-3248s035",
            "role": "REFERENCE",
            "canonical_owner": "Reference",
            "identity_kind": "reference repository",
            "classification": "reference",
            "canonical_repository": {
                "path": str(reference_repo),
                "remote": "https://github.com/ellisp832019/esp32-3248s035.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["embedded_build_support"],
        },
        {
            "system_id": "dep-declared-only",
            "project_id": "dep-declared-only",
            "name": "Declared Only",
            "role": "PLATFORM",
            "canonical_owner": "Declared Only",
            "identity_kind": "active independent repository",
            "canonical_repository": {
                "path": str(dep_declared_repo),
                "remote": "https://github.com/ellisp832019/dep-declared-only.git",
                "branch": "main",
            },
            "dependencies": ["microgrow"],
            "interfaces": [],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "dep-observed-only",
            "project_id": "dep-observed-only",
            "name": "Observed Only",
            "role": "PLATFORM",
            "canonical_owner": "Observed Only",
            "identity_kind": "active independent repository",
            "canonical_repository": {
                "path": str(dep_observed_repo),
                "remote": "https://github.com/ellisp832019/dep-observed-only.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "dep-unknown",
            "project_id": "dep-unknown",
            "name": "Unknown Dependency",
            "role": "PLATFORM",
            "canonical_owner": "Unknown Dependency",
            "identity_kind": "active independent repository",
            "canonical_repository": {
                "path": str(tmp_path / "missing" / "dep-unknown"),
                "remote": "https://github.com/ellisp832019/dep-unknown.git",
                "branch": "main",
            },
            "dependencies": ["ghost-system"],
            "interfaces": [],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "New-Earth-Experiment-Validation-Engine",
            "project_id": "New-Earth-Experiment-Validation-Engine",
            "name": "New-Earth-Experiment-Validation-Engine",
            "role": "ENGINE",
            "canonical_owner": "Experiment Validation",
            "identity_kind": "active independent repository",
            "canonical_repository": {
                "path": str(missing_repo_path),
                "remote": "https://github.com/ellisp832019/New-Earth-Experiment-Validation-Engine.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["experiment_validation"],
        },
    ]

    platform_core = _write_platform_core(tmp_path / "platform-core", estate_roots=[estate_root], systems=systems)
    report = governance_report(db, platform_core_root=platform_core, estate_roots=[estate_root])

    assert report["platform_core"]["status"] == "AVAILABLE"
    assert report["summary"]["readiness"] in {"READY_WITH_WARNINGS", "NOT_READY"}
    assert report["snapshot"]["id"].startswith("gov-")
    assert governance_snapshot(db, platform_core_root=platform_core, estate_roots=[estate_root])["id"] == report["snapshot"]["id"]
    assert governance_report(db, platform_core_root=platform_core, estate_roots=[estate_root])["snapshot"]["id"] == report["snapshot"]["id"]

    assert _find(report, "NEOS-GOV-001", "neos")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-002", "dashboard")[0]["status"] == "ERROR"
    assert _find(report, "NEOS-GOV-003", "biocalm")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-004", "MicroGrow-Hub")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-004", "MicroGrow-Project-Control-Centre")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-005", "MicroGrow-Project-Control-Centre")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-006", "esp32-3248s035")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-007", "markxl")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-008", "dashboard")[0]["status"] == "ERROR"
    assert _find(report, "NEOS-GOV-009")
    assert "dashboard" in _find(report, "NEOS-GOV-009")[0]["affected"]["project_ids"]
    assert "neos" in _find(report, "NEOS-GOV-009")[0]["affected"]["project_ids"]

    dep_declared = _find(report, "NEOS-GOV-010", "dep-declared-only")[0]
    dep_observed = _find(report, "NEOS-GOV-010", "dep-observed-only")[0]
    dep_unknown = _find(report, "NEOS-GOV-010", "dep-unknown")[0]
    assert dep_declared["status"] in {"WARNING", "UNKNOWN"}
    assert dep_observed["status"] == "WARNING"
    assert dep_unknown["status"] == "UNKNOWN"

    assert _find(report, "NEOS-GOV-011", "neos")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-012")
    assert _find(report, "NEOS-GOV-013", "New-Earth-Experiment-Validation-Engine")[0]["status"] in {"ERROR", "UNKNOWN"}
    assert _find(report, "NEOS-GOV-014", "Life OS")[0]["status"] in {"PASS", "UNKNOWN"}


def test_governance_regression_identity_smoke_cases(tmp_path: Path, monkeypatch):
    _use_internal_finding_inputs(monkeypatch)
    db = tmp_path / "neos.db"
    estate_root = tmp_path / "estate"
    estate_root.mkdir()

    active_cases = [
        ("new-earth-ai-employee", "new-earth-ai-employee", "New-Earth-AI-Employee"),
        ("field-scanner", "field-scanner", "Field Scanner"),
        ("new-earth-living", "new-earth-living", "New Earth Living"),
        ("xr-os", "xr-os", "XR OS"),
        ("rehabilitation", "rehabilitation", "Rehabilitation"),
    ]
    for project_id, repo_slug, name in active_cases:
        repo = tmp_path / repo_slug
        _build_project(
            db,
            repo,
            project_id,
            name,
            technologies=["python"],
            remote=f"https://github.com/ellisp832019/{repo_slug}.git",
        )

    systems = [
        {
            "system_id": "GAIA",
            "project_id": "new-earth-ai-employee",
            "name": "New-Earth-AI-Employee",
            "role": "ENGINEERING_INTELLIGENCE",
            "canonical_owner": "GAIA",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(tmp_path / "new-earth-ai-employee"),
                "remote": "https://github.com/ellisp832019/new-earth-ai-employee.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "Field Scanner",
            "project_id": "field-scanner",
            "name": "Field Scanner",
            "role": "PLATFORM",
            "canonical_owner": "Field Scanner",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(tmp_path / "field-scanner"),
                "remote": "https://github.com/ellisp832019/field-scanner.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "New Earth Living",
            "project_id": "new-earth-living",
            "name": "New Earth Living",
            "role": "PLATFORM",
            "canonical_owner": "New Earth Living",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(tmp_path / "new-earth-living"),
                "remote": "https://github.com/ellisp832019/new-earth-living.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "XR OS",
            "project_id": "xr-os",
            "name": "XR OS",
            "role": "PLATFORM",
            "canonical_owner": "XR OS",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(tmp_path / "xr-os"),
                "remote": "https://github.com/ellisp832019/xr-os.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "Rehabilitation",
            "project_id": "rehabilitation",
            "name": "Rehabilitation",
            "role": "PLATFORM",
            "canonical_owner": "Rehabilitation",
            "identity_kind": "active independent repository",
            "classification": "first_party_active",
            "lifecycle": "active",
            "canonical_repository": {
                "path": str(tmp_path / "rehabilitation"),
                "remote": "https://github.com/ellisp832019/rehabilitation.git",
                "branch": "main",
            },
            "dependencies": [],
            "interfaces": ["PROJECT_CONTRACT"],
            "capabilities": ["repository_intelligence"],
        },
        {
            "system_id": "Command Centre",
            "project_id": "Command Centre",
            "name": "Command Centre",
            "role": "SHELL",
            "canonical_owner": "Command Centre",
            "identity_kind": "embedded system",
            "embedded_in": "GAIA",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["command_frontdoor"],
        },
        {
            "system_id": "Backup Guardian",
            "project_id": "Backup Guardian",
            "name": "Backup Guardian",
            "role": "PLANNED_EXTRACTION",
            "canonical_owner": "Backup Guardian",
            "identity_kind": "planned future repository",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["backup_engine"],
        },
        {
            "system_id": "Knowledge Librarian",
            "project_id": "Knowledge Librarian",
            "name": "Knowledge Librarian",
            "role": "PLANNED_EXTRACTION",
            "canonical_owner": "Knowledge Librarian",
            "identity_kind": "planned future repository",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["knowledge_librarian"],
        },
        {
            "system_id": "Planner",
            "project_id": "Planner",
            "name": "Planner",
            "role": "PLANNED_EXTRACTION",
            "canonical_owner": "Planner",
            "identity_kind": "planned future repository",
            "planned_extraction": True,
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["workflow_planning"],
        },
        {
            "system_id": "website",
            "project_id": "website",
            "name": "website",
            "role": "PRODUCT",
            "canonical_owner": "website",
            "identity_kind": "non-repository system/project identity",
            "canonical_repository": {"path": "", "remote": "", "branch": ""},
            "dependencies": [],
            "interfaces": [],
            "capabilities": ["non_repository_identity"],
        },
    ]

    platform_core = _write_platform_core(tmp_path / "platform-core", estate_roots=[estate_root], systems=systems)
    report = governance_report(db, platform_core_root=platform_core, estate_roots=[estate_root])

    for project_id in ["new-earth-ai-employee", "field-scanner", "new-earth-living", "xr-os", "rehabilitation"]:
        assert _find(report, "NEOS-GOV-001", project_id)[0]["status"] == "PASS"
        assert _find(report, "NEOS-GOV-014", project_id)[0]["status"] == "PASS"

    assert _find(report, "NEOS-GOV-004", "Command Centre")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-005", "Command Centre")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-014", "Command Centre")[0]["status"] == "PASS"

    for project_id in ["Backup Guardian", "Knowledge Librarian", "Planner"]:
        assert _find(report, "NEOS-GOV-001", project_id)[0]["status"] == "PASS"
        assert _find(report, "NEOS-GOV-004", project_id)[0]["status"] == "PASS"
        assert _find(report, "NEOS-GOV-014", project_id)[0]["status"] == "PASS"

    assert _find(report, "NEOS-GOV-001", "website")[0]["status"] == "PASS"
    assert _find(report, "NEOS-GOV-014", "website")[0]["status"] == "PASS"


def test_governance_unavailable_and_schema_mismatch(tmp_path: Path):
    db = tmp_path / "neos.db"
    repo = tmp_path / "repo"
    _build_project(db, repo, "demo", "Demo", technologies=["python"], remote="https://example.com/demo.git")

    missing_root = tmp_path / "missing-platform-core"
    status = governance_status(db, platform_core_root=missing_root)
    assert status["platform_core"]["status"] == "UNAVAILABLE"
    assert status["status"] == "UNKNOWN"

    mismatch_root = tmp_path / "mismatch"
    (mismatch_root / "registry").mkdir(parents=True)
    (mismatch_root / "schemas").mkdir(parents=True)
    (mismatch_root / "registry" / "governance.yaml").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "governance_version": "1.0",
                "systems": [],
            },
            indent=2,
            sort_keys=True,
        )
    )
    (mismatch_root / "schemas" / "governance.schema.json").write_text("{}")
    report = governance_report(db, platform_core_root=mismatch_root)
    assert report["platform_core"]["status"] == "SCHEMA_MISMATCH"
    assert report["summary"]["readiness"] == "UNKNOWN"


def test_governance_cli_and_service_json_surfaces(tmp_path: Path):
    db = tmp_path / "neos.db"
    repo = tmp_path / "repo"
    _build_project(db, repo, "demo", "Demo", technologies=["registry"], remote="https://github.com/ellisp832019/demo.git")

    platform_core = _write_platform_core(
        tmp_path / "platform-core",
        estate_roots=[tmp_path],
        systems=[
            {
                "system_id": "demo",
                "project_id": "demo",
                "name": "Demo",
                "role": "PLATFORM",
                "canonical_owner": "Demo",
                "identity_kind": "active independent repository",
                "canonical_repository": {
                    "path": str(repo),
                    "remote": "https://github.com/ellisp832019/demo.git",
                    "branch": "main",
                },
                "dependencies": [],
                "interfaces": ["PROJECT_CONTRACT"],
                "capabilities": ["repository_intelligence"],
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "neos",
            "--db",
            str(db),
            "governance",
            "status",
            "--platform-core-root",
            str(platform_core),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] in {"READY", "READY_WITH_WARNINGS", "NOT_READY", "UNKNOWN"}
    assert payload["snapshot"]["id"].startswith("gov-")

    server, thread = _start_server(db)
    try:
        base = f"http://{server.server_address[0]}:{server.server_port}"
        status_code, response = _get_json(f"{base}/governance/status?platform_core_root={platform_core}&estate_root={tmp_path}")
        assert status_code == 200
        assert response["status"] in {"READY", "READY_WITH_WARNINGS", "NOT_READY", "UNKNOWN"}

        status_code, response = _get_json(f"{base}/governance/project/demo?platform_core_root={platform_core}&estate_root={tmp_path}")
        assert status_code == 200
        assert response["project_id"] == "demo"
        assert response["system"]["system_id"] == "demo"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.mark.parametrize("value,reason", [
    (None, "invalid"), (1.0, "invalid"), (1, "invalid"), (True, "invalid"),
    ([], "invalid"), ({}, "invalid"), ("2.0", "unsupported"), (" 1.0", "unsupported"),
])
def test_canonical_version_rejections(tmp_path, value, reason):
    document, schema = _core_inputs()
    document["governance_version"] = value
    result, _ = governance_module._load_platform_core_document(_write_canonical(tmp_path, document, schema))
    assert result["status"] == "SCHEMA_MISMATCH"
    assert result["reason"] == "platform_core_governance_version_" + reason


def test_missing_and_synthetic_producer_versions(tmp_path):
    for index, mode in enumerate(("missing", "schema_only", "both")):
        document, schema = _core_inputs()
        if mode != "both":
            del document["governance_version"]
        if mode != "missing":
            document["schema_version"] = 1
        result, _ = governance_module._load_platform_core_document(_write_canonical(tmp_path / str(index), document, schema))
        assert result["status"] == "SCHEMA_MISMATCH"
        assert result["reason"] == ("platform_core_governance_schema_invalid" if mode == "both" else "platform_core_governance_version_missing")


def test_actual_core_canonical_mapping_and_supplement_collision(tmp_path):
    root = _write_canonical(tmp_path)
    document, _ = _core_inputs()
    victim = document["systems"][0]
    (root / "registry/projects.json").write_text(json.dumps({"systems": [{"id": victim["id"], "owner": "ATTACKER"}]}))
    result, _ = governance_module._load_platform_core_document(root)
    assert result["status"] == "AVAILABLE"
    assert result["schema_version"] == 1
    assert result["governance_version"] == "1.0"
    records = result["declared"]["systems"]
    assert len(records) == len(document["systems"]) + len(document["planned_extractions"])
    for original in document["systems"] + document["planned_extractions"]:
        matches = [r for r in records if r["system_id"] == original["id"]]
        assert len(matches) == 1
        record = matches[0]
        assert record["owner"] == original["ownership"]["system_owner"]
        assert record["repository"]["canonical_repo"] == original["repository"].get("canonical_repo")
        assert record["repository"]["current_location"] == original["repository"]["current_location"]
        assert record["repository"]["path"] == record["repository"]["remote"] == ""
        if original in document["planned_extractions"]:
            assert record["planned_extraction"] is True
            assert record["source_system"] == original.get("source_system")
            assert not governance_module._declared_requires_observed_repo(record)
            assert not record["embedded_in"]


@pytest.mark.parametrize("field,value", [("systems", {}), ("ownership", "bad"),
    ("repository", []), ("planned_extractions", [None]), ("architecture_notes", []),
    ("supersedes", ["same", "same"])])
def test_canonical_malformed_shapes(tmp_path, field, value):
    document, schema = _core_inputs()
    if field in {"systems", "planned_extractions"}:
        document[field] = value
    else:
        document["systems"][0][field] = value
    result, _ = governance_module._load_platform_core_document(_write_canonical(tmp_path, document, schema))
    assert result["status"] == "SCHEMA_MISMATCH"
    assert result["reason"] == "platform_core_governance_schema_invalid"


@pytest.mark.parametrize("kind", ["external", "missing", "cycle", "assertion"])
def test_core_unsupported_schema_fails_closed(tmp_path, kind):
    document, schema = _core_inputs()
    if kind == "assertion":
        schema["allOf"] = []
    elif kind == "cycle":
        schema["$defs"]["record"] = {"$ref": "#/$defs/record"}
    else:
        schema["properties"]["systems"]["items"] = {"$ref": "https://invalid/schema" if kind == "external" else "#/$defs/missing"}
    result, _ = governance_module._load_platform_core_document(_write_canonical(tmp_path, document, schema))
    assert result["status"] == "SCHEMA_MISMATCH"
    assert result["reason"] == "platform_core_governance_schema_unsupported"


def test_canonical_identity_ambiguity_preserved(tmp_path):
    result, _ = governance_module._load_platform_core_document(_write_canonical(tmp_path))
    record = next(r for r in result["declared"]["systems"] if r["repository"]["canonical_repo"])
    identity = governance_module._normalize_text(record["repository"]["canonical_repo"])
    observed = [{"project_id": "one"}, {"project_id": "two"}]
    matches = governance_module._match_declared_system(record, {identity: observed})
    assert {p["project_id"] for p in matches} == {"one", "two"}


def test_canonical_response_contract_and_determinism(tmp_path):
    db = tmp_path / "neos.db"
    _build_project(db, tmp_path / "repo", "demo", "Demo", technologies=["python"], remote="https://example.com/demo.git")
    root = _write_canonical(tmp_path / "core")
    first = governance_report(db, platform_core_root=root, estate_roots=[tmp_path / "absent"])
    second = governance_report(db, platform_core_root=root, estate_roots=[tmp_path / "absent"])
    assert first["schema_version"] == first["snapshot"]["schema_version"] == 1
    assert first["governance_version"] == "1.0"
    assert first["platform_core"]["status"] == "AVAILABLE"
    assert first["snapshot"]["id"] == second["snapshot"]["id"]
    assert [f["id"] for f in first["findings"]] == [f["id"] for f in second["findings"]]
    planned = {r["id"] for r in _core_inputs()[0]["planned_extractions"]}
    assert planned <= {f["system_id"] for f in first["findings"] if f["rule_id"] == "NEOS-GOV-004"}
