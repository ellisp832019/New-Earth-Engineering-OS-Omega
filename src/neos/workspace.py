from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .core import decision_inventory, project_summary
from .db import connect
from .decision_intelligence import get_release_readiness
from .ecosystem import project_registry_v2
from .firmware import build_firmware_intelligence
from .flight import latest_project_flight
from .genome import latest_project_genome
from .hardware import build_hardware_intelligence
from .manifest import ManifestError, load_manifest
from .memory import latest_project_memory
from .registry import architecture_impact, architecture_registry, discover_contract_sources
from .requirements_intelligence import (
    architecture_without_requirement,
    requirement_gaps,
    requirement_history,
    requirement_inventory,
    unimplemented_requirements,
    untested_requirements,
    verification_readiness,
)

WORKSPACE_SCHEMA_VERSION = 1

WORKSPACE_CLASSIFICATIONS = {
    "FIRST_PARTY_ACTIVE",
    "FIRST_PARTY_PLANNED",
    "FIRST_PARTY_INCOMPLETE",
    "EXPERIMENTAL",
    "LEGACY",
    "REFERENCE",
    "VENDOR",
    "FORK",
    "ARCHIVED",
    "UNKNOWN",
}

FIRST_PARTY_CLASSIFICATIONS = {
    "FIRST_PARTY_ACTIVE",
    "FIRST_PARTY_PLANNED",
    "FIRST_PARTY_INCOMPLETE",
    "EXPERIMENTAL",
    "LEGACY",
    "ARCHIVED",
}

INTEGRATION_MODES = {"CONTRACTED", "OBSERVED", "DEGRADED"}
READINESS_STATES = {"READY", "READY_WITH_GAPS", "NOT_READY", "UNKNOWN"}
RECONCILIATION_STATES = {
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "DRIFTED",
    "UNKNOWN",
    "STALE",
    "CONFLICT",
    "NOT_APPLICABLE",
}
DEPENDENCY_RELATIONS = {
    "DECLARED_AND_OBSERVED",
    "DECLARED_ONLY",
    "OBSERVED_ONLY",
    "CONFLICT",
    "UNKNOWN",
}
FRESHNESS_STATES = {"LIVE", "FRESH", "STALE", "UNKNOWN", "NO_SCAN"}

_VENDOR_TAGS = {"vendor", "third_party", "third-party", "external", "upstream", "partner", "dependency"}
_REFERENCE_TAGS = {"reference", "example", "examples", "sample", "benchmark", "docs_only", "documentation"}
_EXPERIMENTAL_TAGS = {"experimental", "experiment", "prototype", "spike", "incubating"}
_LEGACY_TAGS = {"legacy", "maintenance", "retired", "deprecated"}
_FIRST_PARTY_TAGS = {"first_party", "first-party", "neos", "core", "platform"}


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _stable_set(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return sorted(result)


def _project_row(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown project: {project_id}")
    return row


def _project_row_or_none(conn, project_id: str):
    return conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _discover_manifest_path(repo_path: Path) -> Path | None:
    for candidate in (
        repo_path / "project.neos.json",
        repo_path / "project.neos.yaml",
        repo_path / "project.neos.yml",
        repo_path / "project.json",
        repo_path / "project.yaml",
        repo_path / "project.yml",
        repo_path / "manifest.json",
    ):
        if candidate.exists():
            return candidate
    return None


def _load_manifest_safe(repo_path: Path | None) -> tuple[dict[str, Any], str | None]:
    if repo_path is None:
        return {}, None
    manifest_path = _discover_manifest_path(repo_path)
    if manifest_path is None:
        return {}, None
    try:
        return load_manifest(manifest_path), str(manifest_path)
    except ManifestError:
        return {"manifest_error": "invalid"}, str(manifest_path)


def _git_output(repo_path: Path | None, *args: str) -> str | None:
    if repo_path is None:
        return None
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return None
    return output.strip() or None


def _git_dirty(repo_path: Path | None) -> bool | None:
    output = _git_output(repo_path, "status", "--porcelain")
    if output is None:
        return None
    return bool(output)


def _git_state(repo_path: Path | None) -> dict[str, Any]:
    return {
        "repo_path": str(repo_path.resolve()) if repo_path else None,
        "branch": _git_output(repo_path, "branch", "--show-current"),
        "commit": _git_output(repo_path, "rev-parse", "HEAD"),
        "dirty": _git_dirty(repo_path),
    }


def _manifest_tags(manifest: dict[str, Any]) -> list[str]:
    tags = manifest.get("tags") or manifest.get("labels") or manifest.get("categories") or []
    if isinstance(tags, str):
        tags = [tags]
    return _stable_set([str(tag).strip().lower() for tag in tags if str(tag).strip()])


def _manifest_technologies(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    technologies = manifest.get("technologies", [])
    if not isinstance(technologies, list):
        return []
    items: list[dict[str, Any]] = []
    for entry in technologies:
        if isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("technology") or entry.get("id") or "").strip()
            version = str(entry.get("version") or entry.get("specifier") or "").strip()
            if name:
                items.append({"name": name, "version": version, "raw": entry})
        elif isinstance(entry, str) and entry.strip():
            items.append({"name": entry.strip(), "version": "", "raw": entry})
    return items


def _manifest_dependencies(manifest: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("project_dependencies", "depends_on_projects", "dependencies"):
        for item in _safe_list(manifest.get(key)):
            if isinstance(item, str) and item.strip():
                candidates.append(item.strip())
            elif isinstance(item, dict):
                for nested_key in ("project_id", "target_project_id", "id", "name"):
                    value = item.get(nested_key)
                    if isinstance(value, str) and value.strip():
                        candidates.append(value.strip())
                        break
    portfolio = manifest.get("portfolio")
    if isinstance(portfolio, dict):
        for key in ("dependencies", "depends_on_projects"):
            for item in _safe_list(portfolio.get(key)):
                if isinstance(item, str) and item.strip():
                    candidates.append(item.strip())
    return _stable_set(candidates)


def _safety_fact_value(value: Any) -> dict[str, str]:
    if isinstance(value, bool):
        return {
            "state": "TRUE" if value else "FALSE",
            "source": "DECLARED_CONTRACT",
        }
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return {
                "state": "TRUE" if lowered == "true" else "FALSE",
                "source": "DECLARED_CONTRACT",
            }
        if lowered == "unknown":
            return {"state": "UNKNOWN", "source": "UNKNOWN"}
    if value is None:
        return {"state": "UNKNOWN", "source": "UNKNOWN"}
    return {"state": "UNKNOWN", "source": "UNKNOWN"}


def _contract_document(contract_sources: list[dict[str, Any]], contract_type: str) -> dict[str, Any] | None:
    for source in contract_sources:
        if source.get("contract_type") == contract_type and isinstance(source.get("document"), dict):
            return source["document"]
    return None


def _stable_impact_payload(impact: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(impact, dict):
        return {"project_id": None, "count": 0, "items": []}
    normalized = dict(impact)
    normalized.pop("generated_at", None)
    return normalized


def _project_safety_summary(contract_sources: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    safety_document = _contract_document(contract_sources, "SAFETY_BOUNDARY")
    metadata: dict[str, Any] = {}
    if isinstance(safety_document, dict):
        candidate = safety_document.get("metadata")
        if isinstance(candidate, dict):
            metadata = candidate
        else:
            metadata = safety_document
    return {
        "local_only_operation": _safety_fact_value(metadata.get("local_only_operation")),
        "cloud_allowed": _safety_fact_value(metadata.get("cloud_allowed")),
        "device_flashing_allowed": _safety_fact_value(metadata.get("device_flashing_allowed")),
        "actuator_authority": _safety_fact_value(metadata.get("actuator_authority")),
        "operator_approval_required": _safety_fact_value(metadata.get("operator_approval_required")),
    }


def _declared_dependencies_from_sources(
    contract_sources: list[dict[str, Any]],
    *,
    manifest: dict[str, Any],
    registry_entry: dict[str, Any] | None,
) -> list[str]:
    dependency_document = _contract_document(contract_sources, "DEPENDENCIES")
    if isinstance(dependency_document, dict):
        metadata = dependency_document.get("metadata")
        if isinstance(metadata, dict):
            for key in ("declared_dependencies", "dependencies", "project_dependencies", "depends_on_projects"):
                candidate = metadata.get(key)
                if candidate:
                    values = [str(item).strip() for item in _safe_list(candidate) if str(item).strip()]
                    if values:
                        return _stable_set(values)
    contracts = registry_entry.get("contracts", {}) if registry_entry else {}
    dependencies_contract = contracts.get("dependencies", {}) if isinstance(contracts, dict) else {}
    if isinstance(dependencies_contract, dict):
        metadata = dependencies_contract.get("metadata")
        if isinstance(metadata, dict):
            declared = metadata.get("declared_dependencies")
            if declared:
                values = [str(item).strip() for item in _safe_list(declared) if str(item).strip()]
                if values:
                    return _stable_set(values)
    return _manifest_dependencies(manifest)


def _neos_platform_authority() -> dict[str, dict[str, str]]:
    return {
        "actuator_authority": {"state": "FALSE", "source": "NEOS_PLATFORM_BOUNDARY"},
        "firmware_flashing_authority": {"state": "FALSE", "source": "NEOS_PLATFORM_BOUNDARY"},
        "deployment_authority": {"state": "FALSE", "source": "NEOS_PLATFORM_BOUNDARY"},
        "external_repository_mutation_authority": {"state": "FALSE", "source": "NEOS_PLATFORM_BOUNDARY"},
    }


def _latest_portfolio_snapshot_id(conn: sqlite3.Connection, project_id: str) -> str | None:
    rows = conn.execute("SELECT id, project_ids FROM portfolio_snapshots ORDER BY created_at DESC, id DESC").fetchall()
    for row in rows:
        project_ids = _json_loads(row["project_ids"], [])
        if isinstance(project_ids, list):
            normalized = {str(item).strip() for item in project_ids if str(item).strip()}
            if project_id in normalized:
                return row["id"]
    return None


def _observed_dependencies(db_path: Path, project_id: str) -> dict[str, Any]:
    try:
        conn = connect(db_path)
    except sqlite3.Error:
        return {
            "project_id": project_id,
            "snapshot_id": None,
            "evidence_state": "UNKNOWN",
            "items": [],
        }
    snapshot_id: str | None = None
    try:
        snapshot_id = _latest_portfolio_snapshot_id(conn, project_id)
        if snapshot_id is None:
            return {
                "project_id": project_id,
                "snapshot_id": None,
                "evidence_state": "UNKNOWN",
                "items": [],
            }
        rows = conn.execute(
            """
            SELECT id, source_project_id, target_project_id, relationship_type, confidence, evidence_json, detector, created_at, metadata_json
            FROM project_relationships
            WHERE portfolio_snapshot_id=? AND source_project_id=? AND relationship_type=?
            ORDER BY target_project_id, id
            """,
            (snapshot_id, project_id, "cross_project_dependency"),
        ).fetchall()
    except sqlite3.Error:
        return {
            "project_id": project_id,
            "snapshot_id": snapshot_id,
            "evidence_state": "UNKNOWN",
            "items": [],
        }
    finally:
        conn.close()
    items: list[dict[str, Any]] = []
    for row in rows:
        target = str(row["target_project_id"]).strip()
        if not target:
            continue
        items.append(
            {
                "project_id": target,
                "source": "project_relationships",
                "snapshot_id": snapshot_id,
                "relationship_id": row["id"],
                "relationship_type": row["relationship_type"],
                "confidence": row["confidence"],
                "detector": row["detector"],
                "created_at": row["created_at"],
                "evidence": _json_loads(row["evidence_json"], {}),
                "metadata": _json_loads(row["metadata_json"], {}),
            }
        )
    return {
        "project_id": project_id,
        "snapshot_id": snapshot_id,
        "evidence_state": "PRESENT",
        "items": items,
    }


def _project_manifest(row: Any) -> dict[str, Any]:
    return _json_loads(row["manifest_json"], {}) if row is not None else {}


def _project_summary_payload(db_path: Path, project_id: str) -> dict[str, Any]:
    try:
        return project_summary(db_path, project_id)
    except ValueError:
        return {
            "project_id": project_id,
            "name": project_id,
            "repo_path": None,
            "lifecycle": "unknown",
            "counts": {},
            "semantic_counts": {},
            "last_scan": None,
        }


def _project_registry_entry(db_path: Path, project_id: str) -> dict[str, Any] | None:
    try:
        registry = project_registry_v2(db_path)
    except sqlite3.Error:
        return None
    for entry in registry.get("projects", []):
        if entry.get("project_id") == project_id:
            return entry
    return None


def _classification_reason(classification: str, signals: list[str]) -> str:
    if signals:
        return f"{classification.lower()} derived from {', '.join(signals[:4])}."
    return f"{classification.lower()} derived from available repository evidence."


def classify_project(
    *,
    project_id: str,
    manifest: dict[str, Any],
    project_row: Any | None,
    registry_entry: dict[str, Any] | None,
    scan: Any | None,
    repo_path: Path | None,
) -> dict[str, Any]:
    lifecycle = str((manifest.get("lifecycle") or (project_row["lifecycle"] if project_row is not None else "") or "").strip().lower())
    status_source = manifest.get("status") or manifest.get("project_status")
    if not status_source and project_row is not None:
        status_source = project_row["lifecycle"]
    status = str(status_source or "").strip().lower()
    repo_type = str((manifest.get("repository") or {}).get("type") or manifest.get("repository_type") or "").strip().lower()
    tags = set(_manifest_tags(manifest))
    signals: list[str] = []
    if project_row is not None:
        signals.append("registered-project")
    if scan is not None:
        signals.append("scan-present")
    if repo_path is not None and repo_path.exists():
        signals.append("repo-present")
    if lifecycle:
        signals.append(f"lifecycle:{lifecycle}")
    if status:
        signals.append(f"status:{status}")
    if repo_type:
        signals.append(f"repository:{repo_type}")
    if tags:
        signals.extend(f"tag:{tag}" for tag in sorted(tags))

    classification = "UNKNOWN"
    if lifecycle == "archived" or status == "archived" or "archived" in tags:
        classification = "ARCHIVED"
    elif repo_type in {"vendor", "third_party", "third-party", "external"} or tags & _VENDOR_TAGS:
        classification = "VENDOR"
    elif tags & _REFERENCE_TAGS or repo_type == "reference":
        classification = "REFERENCE"
    elif lifecycle == "experimental" or tags & _EXPERIMENTAL_TAGS:
        classification = "EXPERIMENTAL"
    elif tags & _LEGACY_TAGS or lifecycle == "maintenance":
        classification = "LEGACY"
    elif "fork" in tags or repo_type == "fork":
        classification = "FORK"
    elif project_row is not None:
        if lifecycle in {"active", "maintenance"} or status in {"active", "maintenance"}:
            classification = "FIRST_PARTY_ACTIVE" if scan is not None else "FIRST_PARTY_INCOMPLETE"
        elif lifecycle == "concept" or status in {"planned", "proposal"}:
            classification = "FIRST_PARTY_PLANNED"
        elif tags & _FIRST_PARTY_TAGS:
            classification = "FIRST_PARTY_ACTIVE" if scan is not None else "FIRST_PARTY_PLANNED"
        elif scan is not None:
            classification = "FIRST_PARTY_ACTIVE"
        else:
            classification = "FIRST_PARTY_INCOMPLETE"
    elif manifest:
        if lifecycle in {"active", "maintenance"} or tags & _FIRST_PARTY_TAGS:
            classification = "FIRST_PARTY_PLANNED" if scan is None else "FIRST_PARTY_ACTIVE"
        elif lifecycle == "concept":
            classification = "FIRST_PARTY_PLANNED"
        elif scan is not None or registry_entry is not None:
            classification = "FIRST_PARTY_ACTIVE" if scan is not None else "FIRST_PARTY_INCOMPLETE"

    if classification not in WORKSPACE_CLASSIFICATIONS:
        classification = "UNKNOWN"

    is_first_party = classification in FIRST_PARTY_CLASSIFICATIONS
    return {
        "project_id": project_id,
        "classification": classification,
        "is_first_party": is_first_party,
        "reason": _classification_reason(classification, signals),
        "signals": signals,
        "manifest_lifecycle": lifecycle or "unknown",
        "repository_type": repo_type or "unknown",
        "manifest_tags": sorted(tags),
    }


def derive_freshness(
    *,
    project_row: Any | None,
    scan: Any | None,
    current_state: dict[str, Any],
    repo_path: Path | None,
) -> dict[str, Any]:
    if project_row is None and scan is None and repo_path is None:
        return {"status": "UNKNOWN", "reason": "no_repository_context"}
    if scan is None:
        if repo_path is not None and repo_path.exists():
            return {
                "status": "LIVE",
                "reason": "live_repository_without_registered_scan",
                "current_commit": current_state.get("commit"),
                "current_branch": current_state.get("branch"),
                "dirty": current_state.get("dirty"),
            }
        return {"status": "NO_SCAN", "reason": "no_registered_scan"}
    current_commit = current_state.get("commit")
    scan_commit = scan["git_commit"] if scan is not None else None
    dirty = current_state.get("dirty")
    if current_commit and scan_commit and current_commit != scan_commit:
        return {
            "status": "STALE",
            "reason": "git_commit_changed",
            "current_commit": current_commit,
            "scan_commit": scan_commit,
            "dirty": dirty,
            "scan_id": scan["scan_id"],
        }
    if dirty:
        return {
            "status": "STALE",
            "reason": "working_tree_dirty",
            "current_commit": current_commit,
            "scan_commit": scan_commit,
            "dirty": dirty,
            "scan_id": scan["scan_id"],
        }
    return {
        "status": "FRESH",
        "reason": "current_git_state_matches_latest_scan",
        "current_commit": current_commit,
        "scan_commit": scan_commit,
        "dirty": dirty,
        "scan_id": scan["scan_id"],
    }


def reconcile_dependencies(
    *,
    declared: list[str],
    observed: list[str],
    project_id: str,
    observed_state: str = "PRESENT",
) -> dict[str, Any]:
    declared_set = set(declared)
    observed_set = set(observed)
    union = sorted(declared_set | observed_set)
    items: list[dict[str, Any]] = []
    for dependency_id in union:
        in_declared = dependency_id in declared_set
        in_observed = dependency_id in observed_set
        if in_declared and in_observed:
            relation = "DECLARED_AND_OBSERVED"
        elif in_declared:
            relation = "DECLARED_ONLY"
        elif in_observed:
            relation = "OBSERVED_ONLY"
        else:
            relation = "UNKNOWN"
        items.append(
            {
                "project_id": project_id,
                "dependency_project_id": dependency_id,
                "relation": relation,
                "declared": in_declared,
                "observed": in_observed,
            }
        )

    overlap = declared_set & observed_set
    observed_available = observed_state == "PRESENT"
    if not declared_set and not observed_set:
        status = "NOT_APPLICABLE"
    elif declared_set == observed_set and declared_set:
        status = "VERIFIED"
    elif overlap and (declared_set - observed_set or observed_set - declared_set):
        status = "PARTIALLY_VERIFIED"
    elif declared_set and not observed_set:
        status = "STALE" if observed_available else "UNKNOWN"
    elif observed_set and not declared_set:
        status = "DRIFTED"
    elif declared_set and observed_set and not overlap:
        status = "CONFLICT"
    elif declared_set and not observed_available:
        status = "UNKNOWN"
    else:
        status = "UNKNOWN"
    if status not in RECONCILIATION_STATES:
        status = "UNKNOWN"
    return {
        "project_id": project_id,
        "status": status,
        "observed_state": observed_state,
        "declared": _stable_set(declared),
        "observed": _stable_set(observed),
        "count": len(items),
        "items": items,
        "summary": {
            "declared_count": len(declared_set),
            "observed_count": len(observed_set),
            "shared_count": len(overlap),
        },
    }


def _section_or_empty(data: Any, project_id: str) -> dict[str, Any]:
    if isinstance(data, dict) and data:
        return data
    return {"project_id": project_id, "count": 0, "items": []}


def _registry_contract_adapter(
    *,
    project_id: str,
    project_row: Any | None,
    manifest: dict[str, Any],
    registry_entry: dict[str, Any] | None,
    contract_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    contracts = registry_entry.get("contracts", {}) if registry_entry else {}
    project_contract = contracts.get("project", {}) if isinstance(contracts, dict) else {}
    capabilities_contract = contracts.get("capabilities", {}) if isinstance(contracts, dict) else {}
    dependencies_contract = contracts.get("dependencies", {}) if isinstance(contracts, dict) else {}
    safety_contract = contracts.get("safety_boundary", {}) if isinstance(contracts, dict) else {}
    release_contract = contracts.get("release_state", {}) if isinstance(contracts, dict) else {}
    adapter_state = "connected" if project_contract else "missing"
    if registry_entry is None and not contract_sources:
        adapter_state = "missing"
    elif registry_entry is None:
        adapter_state = "observed"
    return {
        "project_id": project_id,
        "adapter_state": adapter_state,
        "contract_state": "present" if project_contract else "missing",
        "contract_sources": contract_sources,
        "project_contract": project_contract,
        "capabilities_contract": capabilities_contract,
        "dependencies_contract": dependencies_contract,
        "safety_boundary_contract": safety_contract,
        "release_state_contract": release_contract,
        "registry_contracts": contracts,
        "manifest": {
            "project_id": manifest.get("project_id"),
            "name": manifest.get("name"),
            "lifecycle": manifest.get("lifecycle"),
            "tags": _manifest_tags(manifest),
            "dependencies": _manifest_dependencies(manifest),
            "technologies": _manifest_technologies(manifest),
        },
    }


def _project_artifacts(
    db_path: Path,
    project_id: str,
    *,
    repo_path: Path | None = None,
) -> dict[str, Any]:
    conn = connect(db_path)
    project_row = _project_row_or_none(conn, project_id)
    scan = _latest_scan_row(conn, project_id) if project_row is not None else None
    declared_repo_path = Path(project_row["repo_path"]) if project_row is not None and project_row["repo_path"] else None
    observed_repo_path = repo_path or declared_repo_path
    manifest = _project_manifest(project_row)
    manifest_path = str(project_row["manifest_path"]) if project_row is not None else None
    if not manifest:
        manifest, discovered_manifest_path = _load_manifest_safe(observed_repo_path)
        if discovered_manifest_path:
            manifest_path = discovered_manifest_path
    registry_entry = _project_registry_entry(db_path, project_id) if project_row is not None else None
    current_state = _git_state(observed_repo_path)
    freshness = derive_freshness(project_row=project_row, scan=scan, current_state=current_state, repo_path=observed_repo_path)
    classification = classify_project(
        project_id=project_id,
        manifest=manifest,
        project_row=project_row,
        registry_entry=registry_entry,
        scan=scan,
        repo_path=observed_repo_path,
    )
    contract_sources = discover_contract_sources(observed_repo_path, Path(manifest_path) if manifest_path else None) if observed_repo_path else []
    declared_dependencies = _declared_dependencies_from_sources(contract_sources, manifest=manifest, registry_entry=registry_entry)
    observed_dependency_state: dict[str, Any] = {
        "project_id": project_id,
        "snapshot_id": None,
        "evidence_state": "UNKNOWN",
        "items": [],
    }
    if project_row is not None:
        observed_dependency_state = _observed_dependencies(db_path, project_id)
    observed_items = observed_dependency_state.get("items", [])
    if not isinstance(observed_items, list):
        observed_items = []
    observed_dependencies = [str(item["project_id"]).strip() for item in observed_items if isinstance(item, dict) and str(item.get("project_id", "")).strip()]
    dependency_reconciliation = reconcile_dependencies(
        declared=declared_dependencies,
        observed=observed_dependencies,
        project_id=project_id,
        observed_state=str(observed_dependency_state.get("evidence_state", "UNKNOWN")),
    )
    release_readiness = get_release_readiness(db_path, project_id) if project_row is not None else {
        "project_id": project_id,
        "status": "INSUFFICIENT_EVIDENCE",
        "blocking_criteria": ["project not registered"],
        "passed_criteria": [],
        "warnings": ["project not registered"],
        "unknowns": ["project not registered"],
        "evidence": [],
        "recommendation": {},
    }
    registry = architecture_registry(db_path, project_id) if project_row is not None else {
        "project_id": project_id,
        "identity": {
            "project_id": project_id,
            "repo_path": str(observed_repo_path.resolve()) if observed_repo_path else None,
            "source": "workspace",
        },
        "contracts": {},
        "drift": {"status": "unknown", "reason": "project not registered"},
        "impact": {"project_id": project_id, "count": 0, "items": []},
        "health": {"status": "unknown"},
        "identity_conflicts": [],
        "sources": [],
    }
    genome = latest_project_genome(db_path, project_id) if project_row is not None else {}
    memory = latest_project_memory(db_path, project_id) if project_row is not None else {}
    flight = latest_project_flight(db_path, project_id) if project_row is not None else {}
    hardware = build_hardware_intelligence(db_path, project_id) if project_row is not None else {"project_id": project_id, "summary": {"board_count": 0, "component_count": 0, "pin_mapping_count": 0}, "items": []}
    firmware = build_firmware_intelligence(db_path, project_id) if project_row is not None else {"project_id": project_id, "summary": {"environment_count": 0, "target_count": 0, "task_count": 0}, "items": []}
    requirements = requirement_inventory(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_gap_state = requirement_gaps(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_verification = verification_readiness(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_architecture_gaps = architecture_without_requirement(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_unimplemented = unimplemented_requirements(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_untested = untested_requirements(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    requirement_history_state = requirement_history(db_path, project_ids=[project_id]) if project_row is not None else {"project_id": project_id, "count": 0, "items": []}
    contract_adapter = _registry_contract_adapter(
        project_id=project_id,
        project_row=project_row,
        manifest=manifest,
        registry_entry=registry_entry,
        contract_sources=contract_sources,
    )
    integration_mode = "DEGRADED"
    if classification["is_first_party"] and contract_adapter["contract_state"] == "present" and freshness["status"] in {"FRESH", "LIVE"}:
        integration_mode = "CONTRACTED"
    elif project_row is not None and (scan is not None or contract_sources):
        integration_mode = "OBSERVED"
    if integration_mode not in INTEGRATION_MODES:
        integration_mode = "DEGRADED"
    readiness = "UNKNOWN"
    if integration_mode == "CONTRACTED" and release_readiness.get("status") == "READY":
        readiness = "READY"
    elif integration_mode in {"CONTRACTED", "OBSERVED"} and release_readiness.get("status") == "READY_WITH_CONDITIONS":
        readiness = "READY_WITH_GAPS"
    elif release_readiness.get("status") == "NOT_READY" or classification["classification"] in {"VENDOR", "REFERENCE", "FORK", "UNKNOWN"}:
        readiness = "NOT_READY"
    elif project_row is None and not contract_sources and not observed_repo_path:
        readiness = "UNKNOWN"
    elif project_row is None or scan is None:
        readiness = "NOT_READY"
    attention: list[dict[str, Any]] = []
    for warning in release_readiness.get("warnings", []):
        attention.append({"project_id": project_id, "source": "release_readiness", "message": warning, "severity": "medium"})
    if freshness["status"] == "STALE":
        attention.append({"project_id": project_id, "source": "freshness", "message": freshness.get("reason", "stale"), "severity": "high"})
    if dependency_reconciliation["status"] not in {"VERIFIED", "NOT_APPLICABLE"}:
        attention.append({"project_id": project_id, "source": "dependencies", "message": dependency_reconciliation["status"], "severity": "medium"})
    if contract_adapter["contract_state"] == "missing":
        attention.append({"project_id": project_id, "source": "contract_adapter", "message": "platform core contract not available", "severity": "medium"})
    drift = registry.get("drift")
    drift_status = drift.get("status") if isinstance(drift, dict) else None
    if drift_status not in {None, "ok", "aligned", "unknown"}:
        attention.append({"project_id": project_id, "source": "drift", "message": str(drift_status), "severity": "high"})
    project_summary_payload = _project_summary_payload(db_path, project_id)
    conn.close()
    return {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "project_id": project_id,
        "identity": {
            "project_id": project_id,
            "name": project_summary_payload.get("name", project_id),
            "repo_path": project_summary_payload.get("repo_path"),
            "manifest_path": manifest_path,
        },
        "project": project_summary_payload,
        "summary": workspace_summary(
            db_path,
            project_id,
            project_row=project_row,
            registry_entry=registry_entry,
            manifest=manifest,
            scan=scan,
            current_state=current_state,
            freshness=freshness,
            classification=classification,
            integration_mode=integration_mode,
            readiness=readiness,
            contract_state=contract_adapter["contract_state"],
        ),
        "classification": classification,
        "integration": {
            "mode": integration_mode,
            "readiness": readiness,
            "release_readiness": release_readiness,
            "contract_state": contract_adapter["contract_state"],
        },
        "contract": contract_adapter,
        "repository": {
            "project_id": project_id,
            "declared_path": str(declared_repo_path.resolve()) if declared_repo_path else None,
            "observed_path": str(observed_repo_path.resolve()) if observed_repo_path else None,
            "exists": bool(observed_repo_path and observed_repo_path.exists()),
            "git": current_state,
            "manifest_status": "invalid" if manifest.get("manifest_error") else ("present" if manifest else "missing"),
            "manifest_path": manifest_path,
            "scan_id": scan["scan_id"] if scan is not None else None,
        },
        "declared": {
            "manifest": manifest,
            "dependencies": declared_dependencies,
            "technologies": _manifest_technologies(manifest),
        },
        "observed": {
            "registry": registry_entry or {},
            "genome": genome,
            "memory": memory,
            "flight": flight,
            "hardware": hardware,
            "firmware": firmware,
            "requirements": requirements,
            "requirement_gaps": requirement_gap_state,
            "requirement_verification": requirement_verification,
            "requirement_architecture_gaps": requirement_architecture_gaps,
            "requirement_unimplemented": requirement_unimplemented,
            "requirement_untested": requirement_untested,
            "requirement_history": requirement_history_state,
        },
        "reconciled": {
            "dependencies": dependency_reconciliation,
            "release": release_readiness,
        },
        "dependencies": {
            "declared": declared_dependencies,
            "observed": observed_dependencies,
            "observed_details": observed_dependency_state["items"],
            "observed_provenance": {
                "source": "project_relationships" if observed_dependency_state["evidence_state"] == "PRESENT" else "unknown",
                "snapshot_id": observed_dependency_state["snapshot_id"],
                "evidence_state": observed_dependency_state["evidence_state"],
            },
            "reconciled": dependency_reconciliation,
        },
        "requirements": requirements,
        "decisions": decision_inventory(db_path, project_id) if project_row is not None else {"project_id": project_id, "count": 0, "items": []},
        "memory": memory,
        "flight": flight,
        "hardware": hardware,
        "firmware": firmware,
        "release": release_readiness,
        "safety": {
            "project_id": project_id,
            "platform_authority": _neos_platform_authority(),
            "boundary": _contract_document(contract_sources, "SAFETY_BOUNDARY") or {},
            "summary": _project_safety_summary(contract_sources),
        },
        "evidence": {
            "project_registered": project_row is not None,
            "scan_present": scan is not None,
            "manifest_present": bool(manifest),
            "contract_sources_count": len(contract_sources),
            "genome_present": bool(genome),
            "memory_present": bool(memory),
            "flight_present": bool(flight),
            "hardware_present": bool(hardware),
            "firmware_present": bool(firmware),
            "readiness": release_readiness.get("status"),
        },
        "drift": registry.get("drift", {}),
        "impact": _stable_impact_payload(
            registry.get("impact", architecture_impact(db_path, project_id) if project_row is not None else {"project_id": project_id, "count": 0, "items": []})
        ),
        "freshness": freshness,
        "provenance": {
            "declared_sources": [source for source in ([manifest_path] if manifest_path else []) if source],
            "observed_sources": [
                item
                for item in (
                    {"kind": "git", "repo_path": current_state.get("repo_path"), "commit": current_state.get("commit"), "branch": current_state.get("branch")},
                    {"kind": "scan", "scan_id": scan["scan_id"], "created_at": scan["created_at"]} if scan is not None else None,
                )
                if item is not None
            ],
            "contract_sources": contract_sources,
            "analysis_sources": [
                "project_registry_v2" if project_row is not None else "workspace",
                "architecture_registry" if project_row is not None else "workspace",
                "release_readiness" if project_row is not None else "workspace",
            ],
        },
        "attention": attention,
    }


def workspace_summary(
    db_path: Path,
    project_id: str,
    *,
    project_row: Any | None = None,
    registry_entry: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    scan: Any | None = None,
    current_state: dict[str, Any] | None = None,
    freshness: dict[str, Any] | None = None,
    classification: dict[str, Any] | None = None,
    integration_mode: str | None = None,
    readiness: str | None = None,
    contract_state: str | None = None,
) -> dict[str, Any]:
    if project_row is None:
        conn = connect(db_path)
        project_row = _project_row_or_none(conn, project_id)
        conn.close()
    manifest = manifest or _project_manifest(project_row)
    registry_entry_data = registry_entry if isinstance(registry_entry, dict) else _project_registry_entry(db_path, project_id)
    if scan is None and project_row is not None:
        conn = connect(db_path)
        scan = _latest_scan_row(conn, project_id)
        conn.close()
    current_state = current_state or _git_state(Path(project_row["repo_path"]) if project_row is not None else None)
    freshness = freshness or derive_freshness(
        project_row=project_row,
        scan=scan,
        current_state=current_state,
        repo_path=Path(project_row["repo_path"]) if project_row is not None and project_row["repo_path"] else None,
    )
    classification = classification or classify_project(
        project_id=project_id,
        manifest=manifest,
        project_row=project_row,
        registry_entry=registry_entry_data,
        scan=scan,
        repo_path=Path(project_row["repo_path"]) if project_row is not None and project_row["repo_path"] else None,
    )
    integration_mode = integration_mode or (
        "CONTRACTED"
        if classification["is_first_party"] and contract_state == "present" and freshness["status"] in {"FRESH", "LIVE"}
        else "OBSERVED"
        if project_row is not None and (scan is not None or registry_entry_data is not None)
        else "DEGRADED"
    )
    readiness = readiness or (
        "READY"
        if integration_mode == "CONTRACTED" and scan is not None
        else "READY_WITH_GAPS"
        if integration_mode == "OBSERVED"
        else "NOT_READY"
        if project_row is not None
        else "UNKNOWN"
    )
    registry_contracts = registry_entry_data.get("contracts") if registry_entry_data is not None else None
    project_contract = registry_contracts.get("project") if isinstance(registry_contracts, dict) else None
    contract_state = contract_state or ("present" if project_contract else "missing")
    return {
        "project_id": project_id,
        "name": project_row["name"] if project_row is not None else manifest.get("name") or project_id,
        "repo_path": project_row["repo_path"] if project_row is not None else None,
        "lifecycle": project_row["lifecycle"] if project_row is not None else manifest.get("lifecycle", "unknown"),
        "classification": classification["classification"],
        "is_first_party": classification["is_first_party"],
        "integration_mode": integration_mode,
        "readiness": readiness,
        "freshness": freshness["status"],
        "contract_state": contract_state,
        "needs_attention": readiness not in {"READY"} or freshness["status"] == "STALE" or contract_state != "present",
        "project_registered": project_row is not None,
        "scan_present": scan is not None,
        "manifest_present": bool(manifest),
        "summary": _project_summary_payload(db_path, project_id),
    }


def workspace_inventory(
    db_path: Path,
    *,
    project_ids: list[str] | None = None,
    exclude_non_first_party: bool = True,
) -> dict[str, Any]:
    registry = project_registry_v2(db_path)
    wanted = {item for item in project_ids or [] if item}
    items: list[dict[str, Any]] = []
    for entry in registry.get("projects", []):
        if wanted and entry.get("project_id") not in wanted:
            continue
        project_id = entry["project_id"]
        repo_path = Path(entry["repository_path"]) if entry.get("repository_path") else None
        current_state = _git_state(repo_path)
        manifest = entry.get("manifest", {}) if isinstance(entry.get("manifest"), dict) else {}
        scan = entry.get("last_scan")
        classification = classify_project(
            project_id=project_id,
            manifest=manifest,
            project_row=None,
            registry_entry=entry,
            scan=scan,
            repo_path=repo_path,
        )
        freshness = derive_freshness(
            project_row=None,
            scan=scan,
            current_state=current_state,
            repo_path=repo_path,
        )
        contract_state = "present" if entry.get("contracts", {}).get("project") else "missing"
        integration_mode = (
            "CONTRACTED"
            if classification["is_first_party"] and contract_state == "present" and freshness["status"] in {"FRESH", "LIVE"}
            else "OBSERVED"
            if scan is not None or contract_state == "present"
            else "DEGRADED"
        )
        readiness = (
            "READY"
            if integration_mode == "CONTRACTED"
            else "READY_WITH_GAPS"
            if integration_mode == "OBSERVED"
            else "NOT_READY"
        )
        summary = workspace_summary(
            db_path,
            project_id,
            project_row=None,
            registry_entry=entry,
            manifest=manifest,
            scan=scan,
            current_state=current_state,
            freshness=freshness,
            classification=classification,
            integration_mode=integration_mode,
            readiness=readiness,
            contract_state=contract_state,
        )
        if exclude_non_first_party and not summary["is_first_party"]:
            continue
        items.append(summary)
    return {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "project_count": len(items),
        "items": items,
    }


def workspace_section(db_path: Path, project_id: str, section: str, *, repo_path: str | Path | None = None) -> dict[str, Any]:
    context = workspace_context(db_path, project_id, repo_path=Path(repo_path) if repo_path else None)
    if section == "summary":
        return context["summary"]
    if section == "classification":
        return context["classification"]
    if section == "integration":
        return context["integration"]
    if section == "contracts":
        return context["contract"]
    if section == "dependencies":
        return context["dependencies"]
    if section == "evidence":
        return context["evidence"]
    if section == "drift":
        return context["drift"]
    if section == "impact":
        return context["impact"]
    if section == "freshness":
        return context["freshness"]
    if section == "provenance":
        return context["provenance"]
    if section == "release":
        return context["release"]
    if section == "safety":
        return context["safety"]
    raise ValueError(f"Unknown workspace section: {section}")


def workspace_context(db_path: Path, project_id: str, *, repo_path: Path | None = None) -> dict[str, Any]:
    return _project_artifacts(db_path, project_id, repo_path=repo_path)
