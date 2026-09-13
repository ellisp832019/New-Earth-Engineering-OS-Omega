from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

yaml: Any
try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is available in the dev env, but keep safe fallback.
    yaml = None

from .db import connect
from .decision_intelligence import get_release_readiness
from .ecosystem import project_registry_v2
from .manifest import load_manifest

REGISTRY_SCHEMA_VERSION = 1
CONTRACT_SCHEMA_VERSION = 1
CONTRACT_VERSION = "0.1"
ALLOWED_CONTRACT_TYPES = {
    "PROJECT_CONTRACT",
    "CAPABILITIES",
    "DEPENDENCIES",
    "SAFETY_BOUNDARY",
    "RELEASE_STATE",
}


@dataclass(frozen=True)
class RepoIdentity:
    repo_path: str
    remote_url: str | None
    branch: str | None
    commit: str | None
    dirty: bool | None
    fingerprint: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _project_row(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown project: {project_id}")
    return row


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _git_output(repo_path: Path, *args: str) -> str | None:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return None
    return output.strip() or None


def _git_dirty(repo_path: Path) -> bool | None:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return None
    return bool(output.strip())


def _git_remote(repo_path: Path) -> str | None:
    return _git_output(repo_path, "remote", "get-url", "origin")


def _discover_manifest(repo_path: Path) -> Path | None:
    candidates = [
        repo_path / "project.neos.json",
        repo_path / "project.neos.yaml",
        repo_path / "project.neos.yml",
        repo_path / "project.json",
        repo_path / "project.yaml",
        repo_path / "project.yml",
        repo_path / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _load_structured_document(path: Path) -> dict[str, Any] | None:
    suffix = path.suffix.lower()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if suffix == ".json":
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return None
    elif suffix in {".yaml", ".yml"} and yaml is not None:
        try:
            loaded = yaml.safe_load(raw)
        except yaml.YAMLError:
            return None
    else:
        return None
    return loaded if isinstance(loaded, dict) else None


def _stable_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _project_manifest(row: Any) -> dict[str, Any]:
    return _json_loads(row["manifest_json"], {})


def _project_scan_snapshot(conn, project_id: str) -> dict[str, Any]:
    scan = _latest_scan_row(conn, project_id)
    if not scan:
        return {}
    return {
        "scan_id": scan["scan_id"],
        "created_at": scan["created_at"],
        "file_count": scan["file_count"],
        "git_branch": scan["git_branch"],
        "git_commit": scan["git_commit"],
        "repo_head": scan["repo_head"],
        "snapshot": _json_loads(scan["snapshot_json"], {}),
    }


def _project_technologies(project: dict[str, Any]) -> list[dict[str, Any]]:
    technologies = project.get("technologies", [])
    if not isinstance(technologies, list):
        return []
    result: list[dict[str, Any]] = []
    for entry in technologies:
        if isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("technology") or "").strip()
            version = str(entry.get("version") or "").strip()
            category = str(entry.get("category") or "unknown").strip()
            if name:
                result.append(
                    {
                        "name": name,
                        "version": version,
                        "category": category,
                        "raw": entry,
                    }
                )
        elif isinstance(entry, str) and entry.strip():
            result.append(
                {
                    "name": entry.strip(),
                    "version": "",
                    "category": "unknown",
                    "raw": entry,
                }
            )
    return result


def _project_type(repo_path: Path, manifest: dict[str, Any], technologies: list[dict[str, Any]]) -> str:
    declared = manifest.get("project_type")
    if isinstance(declared, str) and declared.strip():
        return declared.strip()
    tech_names = {tech["name"].lower() for tech in technologies}
    if (repo_path / "platformio.ini").exists() or "platformio" in tech_names:
        return "embedded_firmware"
    if (repo_path / "apps" / "desktop").exists() or (repo_path / "pubspec.yaml").exists():
        return "desktop_application"
    if (repo_path / "src").exists() and (repo_path / "tests").exists():
        return "software_project"
    return "repository"


def _project_family(manifest: dict[str, Any]) -> str:
    for key in ("family", "project_family", "portfolio_family"):
        value = manifest.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    tags = manifest.get("tags", [])
    if isinstance(tags, list):
        families = [str(tag).strip() for tag in tags if str(tag).strip()]
        if families:
            return families[0]
    return "unknown"


def _manifest_aliases(manifest: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for key in ("aliases", "alternate_names", "display_aliases"):
        value = manifest.get(key)
        if isinstance(value, list):
            aliases.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            aliases.append(value.strip())
    return sorted(set(aliases))


def _declared_dependencies(manifest: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("project_dependencies", "depends_on_projects", "dependencies"):
        value = manifest.get(key)
        for item in _safe_list(value):
            if isinstance(item, str) and item.strip():
                candidates.append(item.strip())
            elif isinstance(item, dict):
                for nested_key in ("project_id", "target_project_id", "id", "name"):
                    nested = item.get(nested_key)
                    if isinstance(nested, str) and nested.strip():
                        candidates.append(nested.strip())
                        break
    portfolio = manifest.get("portfolio")
    if isinstance(portfolio, dict):
        for key in ("dependencies", "depends_on_projects"):
            for item in _safe_list(portfolio.get(key)):
                if isinstance(item, str) and item.strip():
                    candidates.append(item.strip())
    return sorted({candidate for candidate in candidates if candidate})


def _observed_capabilities(project: dict[str, Any]) -> list[str]:
    capabilities: set[str] = set()
    for tech in _project_technologies(project):
        name = tech["name"].lower()
        if "platformio" in name:
            capabilities.add("embedded_build_support")
        elif "flutter" in name:
            capabilities.add("desktop_ui")
        elif "python" in name:
            capabilities.add("python_runtime")
        elif "markdown" in name:
            capabilities.add("documentation")
    if project.get("feature_count", 0):
        capabilities.add("feature_intelligence")
    if project.get("api_count", 0):
        capabilities.add("api_surface")
    if project.get("configuration_count", 0):
        capabilities.add("configuration_management")
    if project.get("dependency_project_ids"):
        capabilities.add("cross_project_dependencies")
    return sorted(capabilities)


def _declared_capabilities(manifest: dict[str, Any]) -> list[str]:
    candidates: set[str] = set()
    for value in _safe_list(manifest.get("technologies")):
        if isinstance(value, str) and value.strip():
            candidates.add(value.strip())
        elif isinstance(value, dict):
            name = value.get("name")
            if isinstance(name, str) and name.strip():
                candidates.add(name.strip())
    for value in _safe_list(manifest.get("tags")):
        if isinstance(value, str) and value.strip():
            candidates.add(value.strip())
    return sorted(candidates)


def _safety_boundary(manifest: dict[str, Any]) -> dict[str, Any]:
    declared = manifest.get("safety_boundary")
    if isinstance(declared, dict):
        data = declared
    else:
        data = {}
    return {
        "external_repositories_read_only": bool(data.get("external_repositories_read_only", True)),
        "local_only_operation": bool(data.get("local_only_operation", True)),
        "cloud_allowed": bool(data.get("cloud_allowed", False)),
        "device_flashing_allowed": bool(data.get("device_flashing_allowed", False)),
        "actuator_authority": bool(data.get("actuator_authority", False)),
        "automatic_deployment_allowed": bool(data.get("automatic_deployment_allowed", False)),
        "operator_approval_required": bool(data.get("operator_approval_required", True)),
        "deterministic_controller_authority": bool(data.get("deterministic_controller_authority", False)),
        "safety_notes": data.get("safety_notes") or "Conservative default boundary derived from project evidence.",
    }


def _release_state(db_path: Path, project_id: str, repo_path: Path, manifest: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    conn = connect(db_path)
    readiness = get_release_readiness(db_path, project_id)
    conn.close()
    tag = _git_output(repo_path, "describe", "--tags", "--exact-match")
    branch = _git_output(repo_path, "branch", "--show-current")
    commit = _git_output(repo_path, "rev-parse", "HEAD")
    dirty = _git_dirty(repo_path)
    blockers = []
    limitations = []
    if dirty:
        blockers.append("working_tree_dirty")
    if branch and branch not in {manifest.get("repository", {}).get("default_branch"), "main"}:
        limitations.append("branch_does_not_match_default_release_branch")
    if readiness.get("status") not in {None, "ready", "ready_with_conditions", "READY", "READY_WITH_CONDITIONS"}:
        limitations.append(str(readiness.get("status")))
    return {
        "released_version": manifest.get("version"),
        "release_tag": tag,
        "release_branch": branch,
        "release_commit": commit,
        "release_readiness": readiness,
        "release_evidence": project.get("last_scan", {}),
        "hardware_compatibility": project.get("health", {}).get("hardware_compatibility"),
        "firmware_compatibility": project.get("health", {}).get("firmware_compatibility"),
        "known_blockers": blockers,
        "known_limitations": limitations,
    }


def _project_contract(
    db_path: Path,
    project_id: str,
    project_row: Any,
    project: dict[str, Any],
    manifest: dict[str, Any],
    identity: RepoIdentity,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    project_contract = {
        "contract_type": "PROJECT_CONTRACT",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "project_id": project_id,
        "status": "active",
        "declared_source": project_row["manifest_path"],
        "source_identity": identity.repo_path,
        "observed_at": project["last_scan"]["created_at"] if project.get("last_scan") else utc_now(),
        "provenance": {
            "declared": "manifest",
            "observed": "project_registry_v2",
            "derived": ["stable_identity", "project_type", "project_family"],
        },
        "metadata": {
            "project_id": project_id,
            "canonical_name": manifest.get("name", project_row["name"]),
            "display_name": project_row["name"],
            "purpose": manifest.get("description") or "Engineering project managed by NEOS.",
            "project_type": _project_type(Path(project_row["repo_path"]), manifest, _project_technologies(project)),
            "canonical_repository": {
                "path": project_row["repo_path"],
                "remote": identity.remote_url,
                "default_branch": manifest.get("repository", {}).get("default_branch"),
            },
            "integration_boundaries": {
                "external_repositories_read_only": True,
                "local_only_operation": True,
                "operator_approval_required": True,
            },
            "major_interfaces": [
                "manifest",
                "sqlite_registry",
                "filesystem_scan",
                "git_metadata",
            ],
            "platforms": manifest.get("technologies", []),
            "status": project.get("status", project_row["lifecycle"] or "unknown"),
            "aliases": _manifest_aliases(manifest),
            "project_family": _project_family(manifest),
            "declared_sources": [item["path"] for item in sources],
            "identity_fingerprint": identity.fingerprint,
        },
    }
    return project_contract


def _capabilities_contract(project: dict[str, Any], manifest: dict[str, Any], project_row: Any, identity: RepoIdentity) -> dict[str, Any]:
    declared = _declared_capabilities(manifest)
    observed = _observed_capabilities(project)
    drift_missing = sorted(set(declared) - set(observed))
    drift_extra = sorted(set(observed) - set(declared))
    return {
        "contract_type": "CAPABILITIES",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "project_id": project["project_id"],
        "status": "active",
        "declared_source": project_row["manifest_path"],
        "source_identity": identity.repo_path,
        "observed_at": project["last_scan"]["created_at"] if project.get("last_scan") else utc_now(),
        "provenance": {"declared": "manifest", "observed": "registry+scan", "derived": "capability_alignment"},
        "metadata": {
            "declared_capabilities": declared,
            "observed_capabilities": observed,
            "capability_drift": {
                "missing": drift_missing,
                "extra": drift_extra,
                "status": "aligned" if not drift_missing and not drift_extra else "review_required",
            },
            "evidence": {
                "features": project.get("feature_count", 0),
                "api_endpoints": project.get("api_count", 0),
                "config_keys": project.get("configuration_count", 0),
            },
        },
    }


def _dependencies_contract(project: dict[str, Any], manifest: dict[str, Any], project_row: Any, identity: RepoIdentity) -> dict[str, Any]:
    declared = _declared_dependencies(manifest)
    observed = sorted(project.get("dependency_project_ids", []))
    drift_missing = sorted(set(declared) - set(observed))
    drift_extra = sorted(set(observed) - set(declared))
    return {
        "contract_type": "DEPENDENCIES",
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "project_id": project["project_id"],
        "status": "active",
        "declared_source": project_row["manifest_path"],
        "source_identity": identity.repo_path,
        "observed_at": project["last_scan"]["created_at"] if project.get("last_scan") else utc_now(),
        "provenance": {"declared": "manifest", "observed": "project_registry_v2", "derived": "dependency_alignment"},
        "metadata": {
            "declared_dependencies": declared,
            "observed_dependencies": observed,
            "dependency_drift": {
                "missing": drift_missing,
                "extra": drift_extra,
                "status": "aligned" if not drift_missing and not drift_extra else "review_required",
            },
            "categories": {
                "project_dependency": declared + observed,
                "service_api_dependency": [],
                "hardware_dependency": [],
                "firmware_dependency": [],
                "package_dependency": [],
            },
        },
    }


def _identity_conflicts(db_path: Path) -> list[dict[str, Any]]:
    conn = connect(db_path)
    rows = conn.execute("SELECT * FROM projects ORDER BY project_id").fetchall()
    conn.close()
    repo_paths: dict[str, list[str]] = {}
    remotes: dict[str, list[str]] = {}
    names: dict[str, list[str]] = {}
    for row in rows:
        manifest = _project_manifest(row)
        repo_path = str(Path(row["repo_path"]).resolve())
        repo_paths.setdefault(repo_path, []).append(row["project_id"])
        remote = _git_remote(Path(row["repo_path"]))
        if remote:
            remotes.setdefault(remote, []).append(row["project_id"])
        names.setdefault(str(manifest.get("name") or row["name"]), []).append(row["project_id"])
    conflicts: list[dict[str, Any]] = []
    for repo_path, project_ids in sorted(repo_paths.items()):
        if len(project_ids) > 1:
            conflicts.append(
                {
                    "type": "identity_conflict",
                    "reason": "same_repository_path_multiple_project_ids",
                    "evidence": {"repo_path": repo_path, "project_ids": sorted(project_ids)},
                    "confidence": 0.99,
                }
            )
    for remote, project_ids in sorted(remotes.items()):
        if len(project_ids) > 1:
            conflicts.append(
                {
                    "type": "identity_review_required",
                    "reason": "same_git_remote_multiple_project_ids",
                    "evidence": {"remote": remote, "project_ids": sorted(project_ids)},
                    "confidence": 0.85,
                }
            )
    for name, project_ids in sorted(names.items()):
        if len(project_ids) > 1:
            conflicts.append(
                {
                    "type": "identity_review_required",
                    "reason": "alias_ambiguity",
                    "evidence": {"alias": name, "project_ids": sorted(project_ids)},
                    "confidence": 0.7,
                }
            )
    return conflicts


def _repo_identity(repo_path: Path) -> RepoIdentity:
    repo_path = repo_path.resolve()
    remote_url = _git_remote(repo_path)
    branch = _git_output(repo_path, "branch", "--show-current")
    commit = _git_output(repo_path, "rev-parse", "HEAD")
    dirty = _git_dirty(repo_path)
    fingerprint = _stable_fingerprint(
        {
            "repo_path": str(repo_path),
            "remote_url": remote_url,
            "branch": branch,
            "commit": commit,
            "dirty": dirty,
        }
    )
    return RepoIdentity(
        repo_path=str(repo_path),
        remote_url=remote_url,
        branch=branch,
        commit=commit,
        dirty=dirty,
        fingerprint=fingerprint,
    )


def repo_profile(repo_path: Path) -> dict[str, Any]:
    repo_path = repo_path.resolve()
    manifest_path = _discover_manifest(repo_path)
    manifest = load_manifest(manifest_path) if manifest_path else {}
    identity = _repo_identity(repo_path)
    return {
        "repo_path": str(repo_path),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "project_id": manifest.get("project_id"),
        "name": manifest.get("name") or repo_path.name,
        "remote_url": identity.remote_url,
        "branch": identity.branch,
        "commit": identity.commit,
        "dirty": identity.dirty,
        "fingerprint": identity.fingerprint,
        "manifest": manifest,
        "project_type": _project_type(repo_path, manifest, _project_technologies({"technologies": manifest.get("technologies", [])})),
        "project_family": _project_family(manifest),
    }


def discover_contract_sources(repo_path: Path, manifest_path: Path | None = None) -> list[dict[str, Any]]:
    repo_path = repo_path.resolve()
    candidates: list[Path] = []
    if manifest_path and manifest_path.exists():
        candidates.append(manifest_path)
    else:
        discovered = _discover_manifest(repo_path)
        if discovered:
            candidates.append(discovered)
    for pattern in (
        "project.neos.json",
        "project.neos.yaml",
        "project.neos.yml",
        "contracts/*.json",
        "contracts/*.yaml",
        "contracts/*.yml",
        "contracts/**/*.json",
        "contracts/**/*.yaml",
        "contracts/**/*.yml",
    ):
        for path in repo_path.glob(pattern):
            if path.is_file() and path not in candidates:
                candidates.append(path)
    sources: list[dict[str, Any]] = []
    for path in sorted({candidate.resolve() for candidate in candidates}):
        document = _load_structured_document(path)
        if document is None:
            continue
        contract_type = str(document.get("contract_type") or "PROJECT_CONTRACT")
        manifest_like_names = {
            "project.neos.json",
            "project.neos.yaml",
            "project.neos.yml",
            "project.json",
            "project.yaml",
            "project.yml",
            "manifest.json",
        }
        is_manifest_source = (
            manifest_path is not None
            and path == manifest_path.resolve()
        ) or path.name in manifest_like_names
        if is_manifest_source and "contract_type" not in document:
            document = {
                "contract_type": "PROJECT_CONTRACT",
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "project_id": str(document.get("project_id") or repo_path.name),
                "contract_version": CONTRACT_VERSION,
                "status": "active",
                "declared_source": str(path),
                "source_identity": str(repo_path),
                "metadata": document,
            }
            contract_type = "PROJECT_CONTRACT"
        if contract_type not in ALLOWED_CONTRACT_TYPES and path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        sources.append(
            {
                "path": str(path),
                "contract_type": contract_type,
                "schema_version": document.get("schema_version", CONTRACT_SCHEMA_VERSION),
                "contract_version": document.get("contract_version", CONTRACT_VERSION),
                "status": document.get("status", "candidate"),
                "document": document,
            }
        )
    return sources


def validate_contract_document(document: dict[str, Any]) -> dict[str, Any]:
    contract_type = document.get("contract_type")
    if contract_type not in ALLOWED_CONTRACT_TYPES:
        raise ValueError(f"Unsupported contract_type: {contract_type!r}")
    schema_version = document.get("schema_version")
    if schema_version != CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported contract schema_version: {schema_version!r}")
    contract_version = document.get("contract_version")
    if not isinstance(contract_version, str) or not contract_version.strip():
        raise ValueError("Missing contract_version")
    project_id = document.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("Missing project_id")
    status = document.get("status")
    if status not in {"candidate", "active", "superseded", "deprecated", "invalid", "unknown"}:
        raise ValueError(f"Unsupported contract status: {status!r}")
    return document


def contract_drift(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project_row = _project_row(conn, project_id)
    project = project_registry_v2(db_path)["projects"]
    project_entry = next(item for item in project if item["project_id"] == project_id)
    manifest = _project_manifest(project_row)
    identity = _repo_identity(Path(project_row["repo_path"]))
    project_contract = _project_contract(db_path, project_id, project_row, project_entry, manifest, identity, discover_contract_sources(Path(project_row["repo_path"]), Path(project_row["manifest_path"])))
    capabilities = _capabilities_contract(project_entry, manifest, project_row, identity)
    dependencies = _dependencies_contract(project_entry, manifest, project_row, identity)
    safety = _safety_boundary(manifest)
    release = _release_state(db_path, project_id, Path(project_row["repo_path"]), manifest, project_entry)
    conn.close()
    drift_items: list[dict[str, Any]] = []
    capability_drift = capabilities["metadata"]["capability_drift"]
    if capability_drift["missing"] or capability_drift["extra"]:
        drift_items.append(
            {
                "type": "capability_drift",
                "severity": "medium" if capability_drift["missing"] else "low",
                "confidence": 0.9,
                "status": capability_drift["status"],
                "missing": capability_drift["missing"],
                "extra": capability_drift["extra"],
            }
        )
    dependency_drift = dependencies["metadata"]["dependency_drift"]
    if dependency_drift["missing"] or dependency_drift["extra"]:
        drift_items.append(
            {
                "type": "dependency_drift",
                "severity": "medium" if dependency_drift["missing"] else "low",
                "confidence": 0.9,
                "status": dependency_drift["status"],
                "missing": dependency_drift["missing"],
                "extra": dependency_drift["extra"],
            }
        )
    if safety["actuator_authority"] or safety["automatic_deployment_allowed"] or safety["device_flashing_allowed"]:
        drift_items.append(
            {
                "type": "safety_drift",
                "severity": "high",
                "confidence": 1.0,
                "status": "unsafe",
                "evidence": safety,
            }
        )
    if release["known_blockers"]:
        drift_items.append(
            {
                "type": "release_drift",
                "severity": "medium",
                "confidence": 0.8,
                "status": "blocked",
                "evidence": release["known_blockers"],
            }
        )
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "project_id": project_id,
        "status": "review_required" if drift_items else "healthy",
        "items": drift_items,
        "contracts": {
            "project": project_contract,
            "capabilities": capabilities,
            "dependencies": dependencies,
            "safety_boundary": {
                "contract_type": "SAFETY_BOUNDARY",
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "contract_version": CONTRACT_VERSION,
                "project_id": project_id,
                "status": "active",
                "declared_source": project_row["manifest_path"],
                "source_identity": identity.repo_path,
                "observed_at": project_entry["last_scan"]["created_at"] if project_entry.get("last_scan") else utc_now(),
                "provenance": {"declared": "manifest", "observed": "registry", "derived": "conservative_boundary"},
                "metadata": safety,
            },
            "release_state": {
                "contract_type": "RELEASE_STATE",
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "contract_version": CONTRACT_VERSION,
                "project_id": project_id,
                "status": "active" if not release["known_blockers"] else "candidate",
                "declared_source": project_row["manifest_path"],
                "source_identity": identity.repo_path,
                "observed_at": project_entry["last_scan"]["created_at"] if project_entry.get("last_scan") else utc_now(),
                "provenance": {"declared": "manifest", "observed": "git+readiness", "derived": "release_state"},
                "metadata": release,
            },
        },
    }


def architecture_impact(
    db_path: Path,
    project_id: str,
    *,
    peer_project_id: str | None = None,
    peer_repo_path: str | Path | None = None,
) -> dict[str, Any]:
    conn = connect(db_path)
    project_row = _project_row(conn, project_id)
    project = project_registry_v2(db_path)["projects"]
    project_entry = next(item for item in project if item["project_id"] == project_id)
    manifest = _project_manifest(project_row)
    source_identity = _repo_identity(Path(project_row["repo_path"]))
    if peer_project_id:
        peer_row = _project_row(conn, peer_project_id)
        peer_entry = next(item for item in project if item["project_id"] == peer_project_id)
        peer_manifest = _project_manifest(peer_row)
        peer_identity = _repo_identity(Path(peer_row["repo_path"]))
    elif peer_repo_path:
        peer_repo = Path(peer_repo_path).resolve()
        peer_profile = repo_profile(peer_repo)
        peer_row = None
        peer_entry = {
            "project_id": peer_profile.get("project_id") or peer_repo.name,
            "display_name": peer_profile.get("name") or peer_repo.name,
            "repository_path": str(peer_repo),
            "repository_type": "git",
            "status": "unknown",
            "family": peer_profile.get("project_family", "unknown"),
            "technologies": _project_technologies({"technologies": peer_profile.get("manifest", {}).get("technologies", [])}),
            "dependency_project_ids": [],
            "feature_count": 0,
            "api_count": 0,
            "configuration_count": 0,
            "last_scan": {},
            "health": {},
        }
        peer_manifest = peer_profile.get("manifest", {})
        peer_identity = _repo_identity(peer_repo)
    else:
        peer_row = None
        peer_entry = None
        peer_manifest = {}
        peer_identity = None

    source_capabilities = set(_observed_capabilities(project_entry)) | set(_declared_capabilities(manifest))
    peer_capabilities = set(_observed_capabilities(peer_entry)) | set(_declared_capabilities(peer_manifest)) if peer_entry else set()
    source_techs = {tech["name"].lower(): tech for tech in _project_technologies(project_entry)}
    peer_techs = {tech["name"].lower(): tech for tech in _project_technologies(peer_entry)} if peer_entry else {}
    shared_capabilities = sorted(source_capabilities & peer_capabilities)
    shared_technologies = sorted({source_techs[name]["name"] for name in source_techs.keys() & peer_techs.keys()})
    declared_dependencies = sorted(set(_declared_dependencies(manifest)) & set([peer_project_id] if peer_project_id else []))
    observed_dependencies = sorted(set(project_entry.get("dependency_project_ids", [])) & set([peer_project_id] if peer_project_id else []))
    non_relationships = []
    if peer_entry:
        if not shared_capabilities and not shared_technologies:
            non_relationships.append(
                {
                    "type": "no_shared_capability",
                    "reason": "no overlapping declared or observed capabilities",
                    "confidence": 0.9,
                }
            )
        if source_identity.remote_url and peer_identity and source_identity.remote_url == peer_identity.remote_url:
            non_relationships.append(
                {
                    "type": "shared_remote",
                    "reason": "same remote URL does not imply dependency",
                    "confidence": 0.95,
                }
            )
    relationship_score = 0.0
    relationship_score += 0.25 * min(len(shared_capabilities), 4)
    relationship_score += 0.2 * min(len(shared_technologies), 4)
    relationship_score += 0.4 * (1.0 if observed_dependencies else 0.0)
    if peer_entry and source_identity.remote_url and peer_identity and source_identity.remote_url == peer_identity.remote_url:
        relationship_score += 0.15
    relationship_score = min(relationship_score, 1.0)
    summary = {
        "project_id": project_id,
        "peer_project_id": peer_project_id,
        "peer_repo_path": str(peer_repo_path) if peer_repo_path else None,
        "relationship_score": round(relationship_score, 3),
        "relationship_state": "related" if relationship_score >= 0.5 else "independent",
        "shared_capabilities": shared_capabilities,
        "shared_technologies": shared_technologies,
        "declared_dependencies": declared_dependencies,
        "observed_dependencies": observed_dependencies,
        "non_relationships": non_relationships,
        "project_identity": {
            "project_id": project_id,
            "repository_path": source_identity.repo_path,
            "remote_url": source_identity.remote_url,
            "commit": source_identity.commit,
            "branch": source_identity.branch,
            "fingerprint": source_identity.fingerprint,
        },
        "peer_identity": None,
        "project_contract": _project_contract(
            db_path,
            project_id,
            project_row,
            project_entry,
            manifest,
            source_identity,
            discover_contract_sources(Path(project_row["repo_path"]), Path(project_row["manifest_path"])),
        ),
    }
    if peer_entry:
        summary["peer_identity"] = {
            "project_id": peer_entry.get("project_id"),
            "repository_path": peer_identity.repo_path if peer_identity else str(peer_repo_path),
            "remote_url": peer_identity.remote_url if peer_identity else None,
            "commit": peer_identity.commit if peer_identity else None,
            "branch": peer_identity.branch if peer_identity else None,
            "fingerprint": peer_identity.fingerprint if peer_identity else None,
        }
    conn.close()
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "project_id": project_id,
        "generated_at": utc_now(),
        "summary": summary,
        "impact_paths": [
            {
                "path_type": "declared_dependency" if peer_project_id in declared_dependencies else "observed_dependency" if peer_project_id in observed_dependencies else "shared_capability",
                "confidence": 0.8 if peer_entry else 0.0,
                "evidence": {
                    "shared_capabilities": shared_capabilities,
                    "shared_technologies": shared_technologies,
                    "declared_dependencies": declared_dependencies,
                    "observed_dependencies": observed_dependencies,
                },
            }
        ]
        if peer_entry
        else [],
    }


def architecture_registry(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project_row = _project_row(conn, project_id)
    project = project_registry_v2(db_path)["projects"]
    project_entry = next(item for item in project if item["project_id"] == project_id)
    manifest = _project_manifest(project_row)
    identity = _repo_identity(Path(project_row["repo_path"]))
    sources = discover_contract_sources(Path(project_row["repo_path"]), Path(project_row["manifest_path"]))
    project_contract = _project_contract(db_path, project_id, project_row, project_entry, manifest, identity, sources)
    capabilities = _capabilities_contract(project_entry, manifest, project_row, identity)
    dependencies = _dependencies_contract(project_entry, manifest, project_row, identity)
    safety = _safety_boundary(manifest)
    release = _release_state(db_path, project_id, Path(project_row["repo_path"]), manifest, project_entry)
    drift = contract_drift(db_path, project_id)
    conn.close()
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_version": CONTRACT_VERSION,
        "project_id": project_id,
        "identity": {
            "project_id": project_id,
            "name": project_row["name"],
            "repository_path": identity.repo_path,
            "repository_remote": identity.remote_url,
            "repository_fingerprint": identity.fingerprint,
            "branch": identity.branch,
            "commit": identity.commit,
            "dirty": identity.dirty,
            "project_family": _project_family(manifest),
            "project_type": _project_type(Path(project_row["repo_path"]), manifest, _project_technologies(project_entry)),
            "aliases": _manifest_aliases(manifest),
            "status": project_entry.get("status", project_row["lifecycle"] or "unknown"),
        },
        "contracts": {
            "project": project_contract,
            "capabilities": capabilities,
            "dependencies": dependencies,
            "safety_boundary": {
                "contract_type": "SAFETY_BOUNDARY",
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "contract_version": CONTRACT_VERSION,
                "project_id": project_id,
                "status": "active",
                "declared_source": project_row["manifest_path"],
                "source_identity": identity.repo_path,
                "observed_at": project_entry["last_scan"]["created_at"] if project_entry.get("last_scan") else utc_now(),
                "provenance": {"declared": "manifest", "observed": "registry", "derived": "conservative_boundary"},
                "metadata": safety,
            },
            "release_state": {
                "contract_type": "RELEASE_STATE",
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "contract_version": CONTRACT_VERSION,
                "project_id": project_id,
                "status": "active" if not release["known_blockers"] else "candidate",
                "declared_source": project_row["manifest_path"],
                "source_identity": identity.repo_path,
                "observed_at": project_entry["last_scan"]["created_at"] if project_entry.get("last_scan") else utc_now(),
                "provenance": {"declared": "manifest", "observed": "git+readiness", "derived": "release_state"},
                "metadata": release,
            },
        },
        "drift": drift,
        "impact": architecture_impact(db_path, project_id),
        "identity_conflicts": _identity_conflicts(db_path),
        "sources": sources,
        "health": {
            "status": "healthy" if not drift["items"] and not _identity_conflicts(db_path) else "review_required",
            "project_count": 1,
            "contract_count": len(ALLOWED_CONTRACT_TYPES),
            "discovered_contract_count": len(sources),
            "identity_conflict_count": len(_identity_conflicts(db_path)),
            "drift_count": len(drift["items"]),
        },
    }


def architecture_registry_inventory(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute("SELECT project_id FROM projects ORDER BY project_id").fetchall()
    conn.close()
    projects = [architecture_registry(db_path, row["project_id"]) for row in rows]
    conflicts = _identity_conflicts(db_path)
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_version": CONTRACT_VERSION,
        "project_count": len(projects),
        "projects": projects,
        "identity_conflicts": conflicts,
        "health": {
            "status": "healthy" if not conflicts and all(project["health"]["status"] == "healthy" for project in projects) else "review_required",
            "project_count": len(projects),
            "identity_conflict_count": len(conflicts),
        },
    }
