from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

yaml: Any
try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is available in the dev env, but keep safe fallback.
    yaml = None

from . import __version__
from .db import connect
from .ecosystem import project_registry_v2
from .registry import discover_contract_sources, repo_profile
from .manifest import ManifestError, _validate_schema

GOVERNANCE_SCHEMA_VERSION = 1
GOVERNANCE_RESULT_STATES = {"READY", "READY_WITH_WARNINGS", "NOT_READY", "UNKNOWN"}
GOVERNANCE_FINDING_STATUSES = {"PASS", "WARNING", "ERROR", "UNKNOWN"}
GOVERNANCE_SEVERITIES = {"INFO", "WARNING", "ERROR", "BLOCKER"}
PLATFORM_CORE_GOVERNANCE_REFERENCE = "62d7b43"

_DEFAULT_PLATFORM_CORE_ENV_VARS = ("NEOS_PLATFORM_CORE_ROOT", "NEOS_PLATFORM_CORE_REPO")
_DEFAULT_ESTATE_ROOT_ENV_VARS = ("NEOS_GOVERNANCE_ESTATE_ROOTS", "NEOS_ESTATE_ROOTS")

_REPOSITORY_MARKERS = (
    "new-earth",
    "new_earth",
    "microgrow",
    "gaia",
    "command-centre",
    "command_centre",
    "dashboard",
    "biocalm",
    "life os",
    "life-os",
    "omega",
    "rehabilitation",
    "knowledge librarian",
    "knowledge-librarian",
    "backup guardian",
    "experiment validation engine",
    "project control centre",
)

_CAPABILITY_MARKERS = {
    "architecture truth": "architecture_truth",
    "architecture registry": "architecture_truth",
    "governance": "architecture_governance",
    "drift": "engineering_drift",
    "registry": "repository_intelligence",
    "ai": "ai_reasoning",
    "gaia": "ai_reasoning",
    "backup": "backup_engine",
    "validation": "experiment_validation",
    "experiment": "experiment_validation",
    "librarian": "knowledge_librarian",
    "knowledge": "knowledge_librarian",
    "voice": "voice_intelligence",
    "dashboard": "operations_ui",
    "command centre": "command_frontdoor",
    "command center": "command_frontdoor",
    "workspace": "workspace_intelligence",
    "portfolio": "portfolio_intelligence",
}


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


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").replace("_", " ").replace("-", " ").split()).strip().lower()


def _git_output(repo_path: Path | None, *args: str) -> str | None:
    if repo_path is None:
        return None
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), *args],
            stdin=subprocess.DEVNULL,
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


def _module_repo_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / ".git").exists() else None


def _current_neos_commit() -> str | None:
    repo_root = _module_repo_root()
    if repo_root is None:
        return None
    return _git_output(repo_root, "rev-parse", "HEAD")


def _read_structured_document(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    suffix = path.suffix.lower()
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


def _first_existing_path(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def resolve_platform_core_root(platform_core_root: str | Path | None = None) -> Path | None:
    if platform_core_root is not None:
        path = Path(platform_core_root).expanduser()
        return path.resolve()
    for env_var in _DEFAULT_PLATFORM_CORE_ENV_VARS:
        raw = os.environ.get(env_var, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return None


def resolve_estate_roots(
    estate_roots: Iterable[str | Path] | str | Path | None = None,
    *,
    platform_core: dict[str, Any] | None = None,
) -> list[Path]:
    items: list[Path] = []
    if estate_roots is not None:
        if isinstance(estate_roots, (str, Path)):
            items.append(Path(estate_roots).expanduser().resolve())
        else:
            items.extend(Path(item).expanduser().resolve() for item in estate_roots if str(item).strip())
    else:
        for env_var in _DEFAULT_ESTATE_ROOT_ENV_VARS:
            raw = os.environ.get(env_var, "").strip()
            if raw:
                for value in raw.split(os.pathsep):
                    if value.strip():
                        items.append(Path(value).expanduser().resolve())
                break
        if platform_core is not None:
            for value in platform_core.get("declared", {}).get("estate_roots", []):
                if isinstance(value, str) and value.strip():
                    items.append(Path(value).expanduser().resolve())
    unique: list[Path] = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return unique


def _core_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Prepare only the assertion subset used by Core governance v1."""
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type",
                 "required", "properties", "additionalProperties", "items", "enum",
                 "minLength", "pattern", "minItems", "uniqueItems"}

    def expand(node: Any, refs: tuple[str, ...] = ()) -> dict[str, Any]:
        if not isinstance(node, dict) or set(node) - supported:
            raise ValueError("unsupported schema assertion")
        if "$ref" in node:
            ref = node["$ref"]
            if (set(node) != {"$ref"} or not isinstance(ref, str)
                    or not ref.startswith("#/$defs/") or ref in refs):
                raise ValueError("unsupported schema reference")
            name = ref[len("#/$defs/"):]
            if "/" in name or name not in schema.get("$defs", {}):
                raise ValueError("unresolved schema reference")
            return expand(schema["$defs"][name], refs + (ref,))
        result = dict(node)
        result.pop("$defs", None)
        if "properties" in node:
            result["properties"] = {key: expand(value, refs) for key, value in node["properties"].items()}
        if "items" in node:
            result["items"] = expand(node["items"], refs)
        if "additionalProperties" in node and not isinstance(node["additionalProperties"], bool):
            raise ValueError("unsupported additionalProperties")
        kinds = node.get("type", [])
        if isinstance(kinds, str):
            kinds = [kinds]
        if not isinstance(kinds, list) or any(k not in {"object", "array", "string", "boolean", "null"} for k in kinds):
            raise ValueError("unsupported schema type")
        return result

    for definition in schema.get("$defs", {}).values():
        expand(definition)
    return expand(schema)


def _validate_core_collections(value: Any, schema: dict[str, Any], path: str = "") -> None:
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ManifestError(f"{path}: too few items")
        if schema.get("uniqueItems"):
            serialized = [_json_dumps(item) for item in value]
            if len(set(serialized)) != len(serialized):
                raise ManifestError(f"{path}: duplicate items")
        for index, item in enumerate(value):
            _validate_core_collections(item, schema.get("items", {}), f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_core_collections(item, schema.get("properties", {}).get(key, {}), f"{path}.{key}")


def _canonical_core_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt Core identity metadata without fabricating observation paths."""
    records = []
    for collection in ("systems", "planned_extractions"):
        for record in document[collection]:
            repository = record["repository"]
            planned = collection == "planned_extractions" or record["record_type"] == "planned_extraction"
            records.append({
                "system_id": record["id"], "project_id": record["id"],
                "name": record["canonical_name"], "role": record["architecture_role"],
                "canonical_owner": record["ownership"]["system_owner"],
                "owner": record["ownership"]["system_owner"],
                "identity_kind": "embedded system" if record["lifecycle"] == "embedded" else "",
                "classification": record["canonical_status"], "lifecycle": record["lifecycle"],
                "canonical_repository": {"path": "", "remote": "", "branch": ""},
                "planned_extraction": planned, "placeholder": record["canonical_status"] == "placeholder",
                "legacy": record["canonical_status"] == "legacy",
                "source_system": record.get("source_system"), "_core_record": record,
                "_core_repository": {"canonical_repo": repository.get("canonical_repo"),
                                     "current_location": repository["current_location"]},
            })
    return records


def _load_platform_core_document(root: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if root is None or not root.exists():
        return {
            "status": "UNAVAILABLE",
            "reason": "platform_core_root_unavailable",
            "root": str(root) if root is not None else None,
        }, {}

    governance_path = _first_existing_path(
        [
            root / "registry" / "governance.yaml",
            root / "registry" / "governance.yml",
            root / "registry" / "governance.json",
        ]
    )
    schema_path = _first_existing_path(
        [
            root / "schemas" / "governance.schema.json",
        ]
    )
    if governance_path is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "platform_core_governance_file_missing",
            "root": str(root),
            "governance_path": None,
        }, {}

    governance_doc = _read_structured_document(governance_path)
    if governance_doc is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "platform_core_governance_file_unreadable",
            "root": str(root),
            "governance_path": str(governance_path),
        }, {}

    declared_version = governance_doc.get("governance_version")
    reason = None
    if "governance_version" not in governance_doc:
        reason = "platform_core_governance_version_missing"
    elif not isinstance(declared_version, str):
        reason = "platform_core_governance_version_invalid"
    elif declared_version != "1.0":
        reason = "platform_core_governance_version_unsupported"
    if reason is None:
        schema = _read_structured_document(schema_path) if schema_path else None
        if schema is None:
            return {"status": "UNAVAILABLE", "reason": "platform_core_governance_schema_unavailable",
                    "root": str(root)}, governance_doc
        try:
            prepared = _core_schema(schema)
            # A substitute permissive schema must not authorize a different producer.
            if (set(prepared.get("required", [])) != {"governance_version", "ownership_model", "systems", "planned_extractions"}
                    or prepared.get("additionalProperties") is not False
                    or prepared.get("properties", {}).get("governance_version", {}).get("enum") != ["1.0"]):
                raise ValueError("unsupported governance schema binding")
        except (ValueError, TypeError, KeyError, AttributeError):
            reason = "platform_core_governance_schema_unsupported"
        else:
            try:
                _validate_schema(governance_doc, prepared, "governance.")
                _validate_core_collections(governance_doc, prepared)
                ids = [item["id"] for key in ("systems", "planned_extractions") for item in governance_doc[key]]
                if len(ids) != len(set(ids)):
                    raise ManifestError("duplicate canonical identity")
            except (ManifestError, TypeError, KeyError):
                reason = "platform_core_governance_schema_invalid"
    if reason:
        return {"status": "SCHEMA_MISMATCH", "reason": reason, "root": str(root),
                "governance_path": str(governance_path),
                "schema_path": str(schema_path) if schema_path else None,
                "governance_version": declared_version}, governance_doc
    schema_version = GOVERNANCE_SCHEMA_VERSION  # NEOS response version, not a Core input alias.
    canonical_input = {"systems": _canonical_core_records(governance_doc)}

    supplemental_documents: dict[str, Any] = {}
    supplemental_paths = {
        "projects": root / "registry" / "projects.yaml",
        "projects_json": root / "registry" / "projects.json",
        "dependencies": root / "registry" / "dependencies.yaml",
        "dependencies_json": root / "registry" / "dependencies.json",
        "interfaces": root / "registry" / "interfaces.yaml",
        "interfaces_json": root / "registry" / "interfaces.json",
        "services": root / "registry" / "services.yaml",
        "services_json": root / "registry" / "services.json",
        "platform": root / "architecture" / "platform.yaml",
        "platform_json": root / "architecture" / "platform.json",
        "compatibility": root / "compatibility" / "index.yaml",
        "compatibility_json": root / "compatibility" / "index.json",
    }
    for key, path in supplemental_paths.items():
        document = _read_structured_document(path) if path.exists() else None
        if document is not None:
            supplemental_documents[key] = document

    normalized = {
        "platform_core_merge_commit": governance_doc.get("platform_core_merge_commit")
        or governance_doc.get("merge_commit")
        or governance_doc.get("baseline_commit")
        or PLATFORM_CORE_GOVERNANCE_REFERENCE,
        "governance_version": str(declared_version or "unknown"),
        "schema_version": schema_version,
        "governance_path": str(governance_path),
        "schema_path": str(schema_path) if schema_path else None,
        "registry_hash": _stable_hash(
            {
                "governance": governance_doc,
                "supplemental": supplemental_documents,
            }
        ),
        "declared": {
            "estate_roots": _normalize_declared_estate_roots(governance_doc),
            "systems": _normalize_declared_systems(canonical_input, {}),
            "repositories": _normalize_declared_repositories(canonical_input, {}),
            "dependencies": _normalize_declared_dependencies(governance_doc, supplemental_documents),
            "interfaces": _normalize_declared_interfaces(governance_doc, supplemental_documents),
            "services": _normalize_declared_services(governance_doc, supplemental_documents),
        },
        "source": {
            "root": str(root),
            "governance_path": str(governance_path),
            "schema_path": str(schema_path) if schema_path else None,
            "files": sorted(str(path) for path in (governance_path, schema_path) if path is not None),
        },
        "status": "AVAILABLE",
    }
    return normalized, governance_doc


def _normalize_declared_estate_roots(governance_doc: dict[str, Any]) -> list[str]:
    roots: list[str] = []
    for key in ("estate_roots", "estateRoots", "roots"):
        for entry in _safe_list(governance_doc.get(key)):
            if isinstance(entry, str) and entry.strip():
                roots.append(str(Path(entry).expanduser().resolve()))
    estate = governance_doc.get("estate")
    if isinstance(estate, dict):
        for key in ("roots", "estate_roots"):
            for entry in _safe_list(estate.get(key)):
                if isinstance(entry, str) and entry.strip():
                    roots.append(str(Path(entry).expanduser().resolve()))
    return sorted(dict.fromkeys(roots))


def _normalize_declared_repositories(
    governance_doc: dict[str, Any],
    supplemental_documents: dict[str, Any],
) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    sources: list[Any] = []
    for key in ("repositories", "projects", "systems", "declared_systems"):
        sources.extend(_safe_list(governance_doc.get(key)))
    for document in supplemental_documents.values():
        if isinstance(document, dict):
            for key in ("repositories", "projects", "systems"):
                sources.extend(_safe_list(document.get(key)))
    for entry in sources:
        if not isinstance(entry, dict):
            continue
        repo = entry.get("canonical_repository") or entry.get("repository") or {}
        if not isinstance(repo, dict):
            repo = {}
        repositories.append(
            {
                "system_id": str(entry.get("system_id") or entry.get("project_id") or entry.get("id") or entry.get("name") or "").strip(),
                "name": str(entry.get("name") or entry.get("canonical_name") or entry.get("project_id") or "").strip(),
                "role": str(entry.get("role") or entry.get("architecture_role") or "").strip(),
                "identity_kind": str(
                    entry.get("identity_kind")
                    or entry.get("system_identity_kind")
                    or entry.get("repository_identity_kind")
                    or repo.get("identity_kind")
                    or repo.get("kind")
                    or ""
                ).strip(),
                "state": str(entry.get("state") or entry.get("status") or entry.get("lifecycle") or "").strip(),
                "canonical_owner": str(entry.get("canonical_owner") or entry.get("owner") or entry.get("owned_by") or entry.get("system_owner") or "").strip(),
                "repository": {
                    "path": str(repo.get("path") or repo.get("repo_path") or entry.get("repo_path") or "").strip(),
                    "remote": str(repo.get("remote") or repo.get("url") or repo.get("git_remote") or entry.get("remote") or "").strip(),
                    "branch": str(repo.get("branch") or repo.get("default_branch") or entry.get("branch") or "").strip(),
                    **entry.get("_core_repository", {}),
                },
                "capabilities": _normalize_string_list(entry.get("capabilities")),
                "dependencies": _normalize_string_list(entry.get("dependencies")),
                "interfaces": _normalize_string_list(entry.get("interfaces")),
                "embedded_in": str(entry.get("embedded_in") or entry.get("host_system") or entry.get("host_project") or "").strip(),
                "planned_extraction": bool(entry.get("planned_extraction") or entry.get("planned") or entry.get("future_repository")),
                "placeholder": bool(entry.get("placeholder") or entry.get("is_placeholder")),
                "legacy": bool(entry.get("legacy") or entry.get("is_legacy") or entry.get("superseded")),
                "classification": str(entry.get("classification") or entry.get("repository_classification") or "").strip(),
                "source": governance_doc.get("governance_path"),
                "raw": entry.get("_core_record", entry),
                "source_system": entry.get("source_system"),
            }
        )
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in repositories:
        repo_key = (item["system_id"], item["repository"]["path"], item["repository"]["remote"])
        if repo_key in seen:
            continue
        seen.add(repo_key)
        unique.append(item)
    return sorted(unique, key=lambda item: (item["system_id"], item["name"], item["repository"]["path"]))


def _normalize_declared_systems(
    governance_doc: dict[str, Any],
    supplemental_documents: dict[str, Any],
) -> list[dict[str, Any]]:
    systems: list[dict[str, Any]] = []
    sources: list[Any] = []
    for key in ("systems", "declared_systems", "repositories", "projects"):
        sources.extend(_safe_list(governance_doc.get(key)))
    for document in supplemental_documents.values():
        if isinstance(document, dict):
            for key in ("systems", "projects", "repositories"):
                sources.extend(_safe_list(document.get(key)))
    for entry in sources:
        if not isinstance(entry, dict):
            continue
        repo = entry.get("canonical_repository") or entry.get("repository") or {}
        if not isinstance(repo, dict):
            repo = {}
        system_id = str(entry.get("system_id") or entry.get("project_id") or entry.get("id") or entry.get("name") or "").strip()
        if not system_id:
            continue
        systems.append(
            {
                "system_id": system_id,
                "project_id": str(entry.get("project_id") or system_id).strip(),
                "name": str(entry.get("name") or entry.get("canonical_name") or system_id).strip(),
                "role": str(entry.get("role") or entry.get("architecture_role") or "").strip(),
                "owner": str(entry.get("canonical_owner") or entry.get("owner") or entry.get("system_owner") or entry.get("owned_by") or "").strip(),
                "identity_kind": str(
                    entry.get("identity_kind")
                    or entry.get("system_identity_kind")
                    or entry.get("repository_identity_kind")
                    or repo.get("identity_kind")
                    or repo.get("kind")
                    or ""
                ).strip(),
                "classification": str(entry.get("classification") or entry.get("repository_classification") or "").strip(),
                "lifecycle": str(entry.get("lifecycle") or entry.get("state") or entry.get("status") or "").strip(),
                "repository": {
                    "path": str(repo.get("path") or repo.get("repo_path") or entry.get("repo_path") or "").strip(),
                    "remote": str(repo.get("remote") or repo.get("url") or repo.get("git_remote") or entry.get("remote") or "").strip(),
                    "branch": str(repo.get("branch") or repo.get("default_branch") or entry.get("branch") or "").strip(),
                    **entry.get("_core_repository", {}),
                },
                "dependencies": _normalize_string_list(entry.get("dependencies")),
                "interfaces": _normalize_string_list(entry.get("interfaces")),
                "capabilities": _normalize_string_list(entry.get("capabilities")),
                "embedded_in": str(entry.get("embedded_in") or entry.get("host_system") or entry.get("host_project") or "").strip(),
                "planned_extraction": bool(entry.get("planned_extraction") or entry.get("planned") or entry.get("future_repository")),
                "placeholder": bool(entry.get("placeholder") or entry.get("is_placeholder")),
                "legacy": bool(entry.get("legacy") or entry.get("is_legacy") or entry.get("superseded")),
                "canonical": bool(entry.get("canonical", True)),
                "observed_repo_hint": str(entry.get("observed_repo_hint") or "").strip(),
                "source": governance_doc.get("governance_path"),
                "raw": entry.get("_core_record", entry),
                "source_system": entry.get("source_system"),
            }
        )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in systems:
        system_key = (item["system_id"], item["repository"]["path"], item["repository"]["remote"])
        if system_key in seen:
            continue
        seen.add(system_key)
        deduped.append(item)
    return sorted(deduped, key=lambda item: (item["system_id"], item["name"]))


def _normalize_declared_dependencies(governance_doc: dict[str, Any], supplemental_documents: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    sources: list[Any] = []
    for key in ("dependencies", "project_dependencies"):
        sources.extend(_safe_list(governance_doc.get(key)))
    for document in supplemental_documents.values():
        if isinstance(document, dict):
            for key in ("dependencies", "project_dependencies"):
                sources.extend(_safe_list(document.get(key)))
    for entry in sources:
        if isinstance(entry, str) and entry.strip():
            items.append({"source": None, "target": entry.strip(), "kind": "project_dependency", "raw": entry})
        elif isinstance(entry, dict):
            source = str(entry.get("source") or entry.get("source_project_id") or entry.get("project_id") or "").strip()
            target = str(entry.get("target") or entry.get("target_project_id") or entry.get("dependency_project_id") or entry.get("id") or "").strip()
            if source or target:
                items.append(
                    {
                        "source": source or None,
                        "target": target or None,
                        "kind": str(entry.get("kind") or entry.get("dependency_type") or "project_dependency").strip(),
                        "raw": entry,
                    }
                )
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str]] = set()
    for item in items:
        dep_key = (item["source"], item["target"], item["kind"])
        if dep_key in seen:
            continue
        seen.add(dep_key)
        unique.append(item)
    return sorted(unique, key=lambda item: (item["source"] or "", item["target"] or "", item["kind"]))


def _normalize_declared_interfaces(governance_doc: dict[str, Any], supplemental_documents: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    sources: list[Any] = []
    for key in ("interfaces", "service_contracts"):
        sources.extend(_safe_list(governance_doc.get(key)))
    for document in supplemental_documents.values():
        if isinstance(document, dict):
            for key in ("interfaces", "service_contracts"):
                sources.extend(_safe_list(document.get(key)))
    for entry in sources:
        if isinstance(entry, str) and entry.strip():
            items.append({"name": entry.strip(), "kind": "interface", "raw": entry})
        elif isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("interface") or entry.get("id") or "").strip()
            if name:
                items.append({"name": name, "kind": str(entry.get("kind") or entry.get("type") or "interface").strip(), "raw": entry})
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        interface_key = (item["name"], item["kind"])
        if interface_key in seen:
            continue
        seen.add(interface_key)
        unique.append(item)
    return sorted(unique, key=lambda item: (item["kind"], item["name"]))


def _normalize_declared_services(governance_doc: dict[str, Any], supplemental_documents: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    sources: list[Any] = []
    for key in ("services", "endpoints"):
        sources.extend(_safe_list(governance_doc.get(key)))
    for document in supplemental_documents.values():
        if isinstance(document, dict):
            for key in ("services", "endpoints"):
                sources.extend(_safe_list(document.get(key)))
    for entry in sources:
        if isinstance(entry, str) and entry.strip():
            items.append({"name": entry.strip(), "raw": entry})
        elif isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("service") or entry.get("id") or "").strip()
            if name:
                items.append({"name": name, "owner": str(entry.get("owner") or "").strip(), "raw": entry})
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        service_name = item["name"]
        if service_name in seen:
            continue
        seen.add(service_name)
        unique.append(item)
    return sorted(unique, key=lambda item: item["name"])


def _normalize_string_list(value: Any) -> list[str]:
    items: list[str] = []
    for entry in _safe_list(value):
        if isinstance(entry, str) and entry.strip():
            items.append(entry.strip())
        elif isinstance(entry, dict):
            for key in ("name", "id", "project_id", "target_project_id", "interface", "dependency", "capability"):
                candidate = entry.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    items.append(candidate.strip())
                    break
    unique: list[str] = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return sorted(unique)


def _project_lookup_key(entry: dict[str, Any]) -> str:
    return _normalize_text(entry.get("project_id") or entry.get("name") or entry.get("repository_path"))


def _observed_classification(project: dict[str, Any]) -> str:
    lifecycle = _normalize_text(project.get("lifecycle"))
    status = _normalize_text(project.get("status"))
    repo_type = _normalize_text(project.get("project_type") or project.get("repository_type"))
    tags = {_normalize_text(tag) for tag in project.get("tags", []) if str(tag).strip()}

    if lifecycle == "archived" or status == "archived" or "archived" in tags:
        return "ARCHIVED"
    if repo_type in {"vendor", "third party", "external"} or tags & {"vendor", "third_party", "third-party", "external", "upstream", "partner"}:
        return "VENDOR"
    if lifecycle == "concept" or status in {"planned", "proposal"}:
        return "FIRST_PARTY_PLANNED"
    if "placeholder" in tags:
        return "FIRST_PARTY_PLANNED"
    if lifecycle == "experimental" or tags & {"experimental", "experiment", "prototype", "spike", "incubating"}:
        return "EXPERIMENTAL"
    if tags & {"legacy", "maintenance", "retired", "deprecated"}:
        return "LEGACY"
    if "fork" in tags or repo_type == "fork":
        return "FORK"
    if tags & {"reference", "examples", "sample", "benchmark", "docs_only", "documentation"}:
        return "REFERENCE"
    if lifecycle in {"active", "maintenance"} or status in {"active", "maintenance"} or tags & {"first_party", "first-party", "neos", "core", "platform"}:
        return "FIRST_PARTY_ACTIVE" if project.get("scan_id") else "FIRST_PARTY_INCOMPLETE"
    if project.get("scan_id"):
        return "FIRST_PARTY_ACTIVE"
    return "UNKNOWN"


def _observed_dependency_state(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    snapshot_id = None
    try:
        rows = conn.execute("SELECT id, project_ids FROM portfolio_snapshots ORDER BY created_at DESC, id DESC").fetchall()
        for row in rows:
            project_ids = _json_loads(row["project_ids"], [])
            if isinstance(project_ids, list):
                normalized = {str(item).strip() for item in project_ids if str(item).strip()}
                if project_id in normalized:
                    snapshot_id = row["id"]
                    break
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


def _observed_contract_surface(project: dict[str, Any], repo_path: Path) -> list[str]:
    surface: set[str] = {"PROJECT_CONTRACT"}
    capabilities = _project_capabilities(project)
    if capabilities:
        surface.add("CAPABILITIES")
    for capability in capabilities:
        if capability in {"embedded_build_support", "desktop_ui", "python_runtime", "documentation"}:
            surface.add("CAPABILITIES")
        if capability == "cross_project_dependencies":
            surface.add("DEPENDENCIES")
    manifest = project.get("manifest", {})
    if isinstance(manifest, dict):
        for item in _normalize_string_list(manifest.get("interfaces")):
            surface.add(item)
    for source in discover_contract_sources(repo_path):
        contract_type = str(source.get("contract_type") or "").strip()
        if contract_type:
            surface.add(contract_type)
    surface.add("SAFETY_BOUNDARY")
    surface.add("RELEASE_STATE")
    return sorted(surface)


def _project_capabilities(project: dict[str, Any]) -> list[str]:
    capabilities: set[str] = set()
    text_source = " ".join(
        str(part)
        for part in (
            project.get("project_id"),
            project.get("name"),
            project.get("family"),
            project.get("lifecycle"),
            project.get("status"),
            " ".join(project.get("tags", [])),
            " ".join(tech.get("name", "") for tech in project.get("technologies", [])),
            " ".join(project.get("dependency_project_ids", [])),
        )
    ).lower()
    for marker, capability in _CAPABILITY_MARKERS.items():
        if marker in text_source:
            capabilities.add(capability)
    for tech in project.get("technologies", []):
        tech_name = _normalize_text(tech.get("name"))
        if "platformio" in tech_name:
            capabilities.add("embedded_build_support")
        if "flutter" in tech_name:
            capabilities.add("desktop_ui")
        if "python" in tech_name:
            capabilities.add("python_runtime")
        if "markdown" in tech_name:
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


def _observed_project_record(db_path: Path, project: dict[str, Any]) -> dict[str, Any]:
    repo_path = Path(project["repository_path"]).expanduser().resolve()
    profile = repo_profile(repo_path)
    dependency_state = _observed_dependency_state(db_path, project["project_id"])
    classification = _observed_classification(project)
    return {
        "project_id": project["project_id"],
        "name": project["name"],
        "repo_path": str(repo_path),
        "remote_url": profile.get("remote_url"),
        "branch": profile.get("branch"),
        "commit": profile.get("commit"),
        "dirty": profile.get("dirty"),
        "status": project.get("status"),
        "lifecycle": project.get("lifecycle"),
        "family": project.get("family"),
        "tags": project.get("tags", []),
        "technologies": project.get("technologies", []),
        "classification": classification,
        "is_first_party": classification.startswith("FIRST_PARTY"),
        "repository_role": profile.get("project_type") or project.get("repository_type") or "unknown",
        "capabilities": _project_capabilities(project),
        "declared_dependencies": project.get("dependency_project_ids", []),
        "observed_dependencies": [item["project_id"] for item in dependency_state.get("items", [])],
        "contract_drift": {"status": "unknown", "items": []},
        "contracts": {"project": {"contract_type": "PROJECT_CONTRACT"}, "capabilities": {"contract_type": "CAPABILITIES"}, "dependencies": {"contract_type": "DEPENDENCIES"}},
        "provenance": {
            "project": project,
            "dependency_state": dependency_state,
        },
        "profile": profile,
        "observed_interfaces": _observed_contract_surface(project, repo_path),
    }


def _observed_projects(db_path: Path) -> list[dict[str, Any]]:
    registry = project_registry_v2(db_path)
    projects = registry.get("projects", [])
    return [_observed_project_record(db_path, project) for project in sorted(projects, key=lambda item: item["project_id"])]


def _index_observed_projects(projects: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in projects:
        keys = {
            _normalize_text(project["project_id"]),
            _normalize_text(project["name"]),
            _normalize_text(Path(project["repo_path"]).name),
            _normalize_text(project.get("remote_url")),
        }
        manifest = project.get("profile", {}).get("manifest", {})
        if isinstance(manifest, dict):
            for alias in _normalize_string_list(manifest.get("aliases") or manifest.get("alternate_names") or manifest.get("display_aliases")):
                keys.add(_normalize_text(alias))
            if isinstance(manifest.get("name"), str):
                keys.add(_normalize_text(manifest["name"]))
        for key in keys:
            if key:
                index[key].append(project)
    return index


def _declared_is_repository(system: dict[str, Any]) -> bool:
    identity_kind = _normalize_text(system.get("identity_kind"))
    if any(token in identity_kind for token in ("active independent repository", "placeholder repository", "legacy repository", "prototype repository", "reference repository", "vendor repository")):
        return True
    return bool(system.get("repository", {}).get("canonical_repo") or system.get("repository", {}).get("path") or system.get("repository", {}).get("remote"))


def _declared_requires_observed_repo(system: dict[str, Any]) -> bool:
    identity_kind = _normalize_text(system.get("identity_kind"))
    if "embedded" in identity_kind:
        return False
    if "non repository" in identity_kind:
        return False
    if "planned future repository" in identity_kind:
        return False
    if system.get("planned_extraction"):
        return False
    return _declared_is_repository(system)


def _match_declared_system(
    system: dict[str, Any],
    observed_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    keys = {
        _normalize_text(system["system_id"]),
        _normalize_text(system["project_id"]),
        _normalize_text(system["name"]),
        _normalize_text(Path(system["repository"]["path"]).name) if system["repository"]["path"] else "",
        _normalize_text(system["repository"]["remote"]),
        _normalize_text(system["repository"].get("canonical_repo")),
    }
    matches: list[dict[str, Any]] = []
    for key in keys:
        matches.extend(observed_index.get(key, []))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for project in matches:
        if project["project_id"] in seen:
            continue
        seen.add(project["project_id"])
        unique.append(project)
    return sorted(unique, key=lambda item: item["project_id"])


def _finding(
    *,
    rule_id: str,
    status: str,
    severity: str,
    system_id: str | None,
    canonical_owner: str | None,
    declared_state: dict[str, Any],
    observed_state: dict[str, Any],
    explanation: str,
    recommended_owner: str | None,
    remediation_category: str,
    evidence: dict[str, Any],
    affected: dict[str, Any] | None = None,
    confidence: float | None = None,
    platform_core: dict[str, Any] | None = None,
    source_commit: str | None,
) -> dict[str, Any]:
    if status not in GOVERNANCE_FINDING_STATUSES:
        status = "UNKNOWN"
    if severity not in GOVERNANCE_SEVERITIES:
        severity = "INFO"
    payload = {
        "id": f"gov-{rule_id.lower().replace('neos-gov-', '')}-{_stable_hash({'rule_id': rule_id, 'system_id': system_id, 'declared': declared_state, 'observed': observed_state, 'evidence': evidence})[:16]}",
        "rule_id": rule_id,
        "status": status,
        "severity": severity,
        "system_id": system_id,
        "canonical_owner": canonical_owner,
        "declared_state": declared_state,
        "observed_state": observed_state,
        "evidence": evidence,
        "affected": affected or {},
        "explanation": explanation,
        "recommended_owner": recommended_owner,
        "remediation_category": remediation_category,
        "confidence": confidence,
        "timestamp": utc_now(),
        "platform_core_governance_version": (platform_core or {}).get("governance_version"),
        "platform_core_governance_hash": (platform_core or {}).get("registry_hash"),
        "platform_core_merge_commit": (platform_core or {}).get("platform_core_merge_commit") or PLATFORM_CORE_GOVERNANCE_REFERENCE,
        "neos_version": __version__,
        "source_commit": source_commit,
    }
    return payload


def _evaluate_system(
    declared: dict[str, Any],
    *,
    observed_matches: list[dict[str, Any]],
    platform_core: dict[str, Any],
    db_path: Path,
    source_commit: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    declared_system_id = declared["system_id"]
    finding_system_id = declared.get("project_id") or declared_system_id
    owner = declared.get("owner") or declared.get("canonical_owner") or declared.get("role") or declared_system_id
    match = observed_matches[0] if observed_matches else None
    observed_state = {
        "matches": [
            {
                "project_id": item["project_id"],
                "repo_path": item["repo_path"],
                "remote_url": item["remote_url"],
                "classification": item["classification"],
                "role": item["repository_role"],
                "status": item["status"],
            }
            for item in observed_matches
        ],
        "state": "OBSERVED" if match else "MISSING",
        "project_id": match["project_id"] if match else None,
        "repo_path": match["repo_path"] if match else declared["repository"]["path"] or None,
        "remote_url": match["remote_url"] if match else None,
        "classification": match["classification"] if match else "UNKNOWN",
        "capabilities": match["capabilities"] if match else [],
        "dependencies": match["observed_dependencies"] if match else [],
        "contract_drift": match["contract_drift"] if match else {},
        "repository_role": match["repository_role"] if match else "unknown",
        "profile": match["profile"] if match else {},
        "interfaces": match["observed_interfaces"] if match else [],
    }
    findings: list[dict[str, Any]] = []
    canonical_repo = declared.get("repository", {})
    declared_state = {
        "system_id": declared_system_id,
        "project_id": declared.get("project_id"),
        "name": declared.get("name"),
        "role": declared.get("role"),
        "owner": owner,
        "identity_kind": declared.get("identity_kind"),
        "classification": declared.get("classification"),
        "lifecycle": declared.get("lifecycle"),
        "repository": canonical_repo,
        "dependencies": declared.get("dependencies", []),
        "interfaces": declared.get("interfaces", []),
        "capabilities": declared.get("capabilities", []),
        "embedded_in": declared.get("embedded_in"),
        "planned_extraction": declared.get("planned_extraction"),
        "placeholder": declared.get("placeholder"),
        "legacy": declared.get("legacy"),
    }

    if _declared_requires_observed_repo(declared):
        if not match:
            if canonical_repo.get("path"):
                severity = "BLOCKER"
                status = "ERROR"
                explanation = "Declared canonical repository was not observed in the configured estate."
                remediation = "repository_registration"
            else:
                severity = "WARNING"
                status = "UNKNOWN"
                explanation = "Declared canonical system has no configured repository path, so NEOS cannot prove observation."
                remediation = "configuration"
        else:
            severity = "INFO"
            status = "PASS"
            explanation = "Declared canonical system is observable in NEOS."
            remediation = "none"
    else:
        if match and declared.get("identity_kind") and "embedded" in _normalize_text(declared.get("identity_kind")) and match:
            severity = "ERROR"
            status = "ERROR"
            explanation = "Embedded system is being represented as an independent repository."
            remediation = "architecture_boundary"
        else:
            severity = "INFO"
            status = "PASS"
            explanation = "Declared non-repository or embedded identity is preserved."
            remediation = "none"
    findings.append(
        _finding(
            rule_id="NEOS-GOV-001",
            status=status,
            severity=severity,
            system_id=finding_system_id,
            canonical_owner=owner,
            declared_state=declared_state,
            observed_state=observed_state,
            explanation=explanation,
            recommended_owner=owner,
            remediation_category=remediation,
            evidence={
                "declared_repository": canonical_repo,
                "observed_match_count": len(observed_matches),
                "matches": observed_state["matches"],
            },
            affected={"project_ids": [item["project_id"] for item in observed_matches]},
            confidence=0.99 if status == "PASS" and match else 0.88 if status == "ERROR" else 0.75,
            platform_core=platform_core,
            source_commit=source_commit,
        )
    )

    if _declared_requires_observed_repo(declared) and not match:
        missing_state = "missing"
        if not canonical_repo.get("path") and not canonical_repo.get("remote"):
            missing_state = "unconfigured"
        elif canonical_repo.get("path") and Path(str(canonical_repo["path"])).expanduser().exists() is False:
            missing_state = "unavailable"
        elif not platform_core.get("declared", {}).get("estate_roots"):
            missing_state = "unknown"
        findings.append(
            _finding(
                rule_id="NEOS-GOV-013",
                status="ERROR" if missing_state in {"missing", "unavailable"} else "UNKNOWN",
                severity="BLOCKER" if missing_state == "missing" else "WARNING" if missing_state == "unavailable" else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state={**observed_state, "missing_state": missing_state},
                explanation="Declared canonical repository could not be observed in the configured NEOS estate.",
                recommended_owner=owner,
                remediation_category="registration",
                evidence={
                    "missing_state": missing_state,
                    "configured_estate_roots": platform_core.get("declared", {}).get("estate_roots", []),
                    "declared_repository": canonical_repo,
                },
                affected={"project_ids": []},
                confidence=0.92 if missing_state == "missing" else 0.7,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if len(observed_matches) > 1:
        findings.append(
            _finding(
                rule_id="NEOS-GOV-002",
                status="ERROR",
                severity="ERROR",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Multiple NEOS projects match the same declared canonical system identity.",
                recommended_owner=owner,
                remediation_category="identity",
                evidence={"matches": observed_state["matches"]},
                affected={"project_ids": [item["project_id"] for item in observed_matches]},
                confidence=0.9,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if match:
        declared_repo_path = _normalize_text(canonical_repo.get("path"))
        declared_remote = _normalize_text(canonical_repo.get("remote"))
        observed_repo_path = _normalize_text(match.get("repo_path"))
        observed_remote = _normalize_text(match.get("remote_url"))
        if declared_repo_path and observed_repo_path and declared_repo_path != observed_repo_path:
            findings.append(
                _finding(
                    rule_id="NEOS-GOV-002",
                    status="ERROR",
                    severity="ERROR",
                    system_id=finding_system_id,
                    canonical_owner=owner,
                    declared_state=declared_state,
                    observed_state=observed_state,
                    explanation="Observed repository path does not match the declared canonical repository identity.",
                    recommended_owner=owner,
                    remediation_category="identity",
                    evidence={"declared_path": canonical_repo.get("path"), "observed_path": match.get("repo_path")},
                    affected={"project_ids": [match["project_id"]]},
                    confidence=0.97,
                    platform_core=platform_core,
                    source_commit=source_commit,
                )
            )
        if declared_remote and observed_remote and declared_remote != observed_remote:
            findings.append(
                _finding(
                    rule_id="NEOS-GOV-002",
                    status="ERROR",
                    severity="ERROR",
                    system_id=finding_system_id,
                    canonical_owner=owner,
                    declared_state=declared_state,
                    observed_state=observed_state,
                    explanation="Observed remote identity does not match the declared canonical repository identity.",
                    recommended_owner=owner,
                    remediation_category="identity",
                    evidence={"declared_remote": canonical_repo.get("remote"), "observed_remote": match.get("remote_url")},
                    affected={"project_ids": [match["project_id"]]},
                    confidence=0.97,
                    platform_core=platform_core,
                    source_commit=source_commit,
                )
            )

    if declared.get("placeholder"):
        implemented = bool(match and match["classification"] == "FIRST_PARTY_ACTIVE")
        findings.append(
            _finding(
                rule_id="NEOS-GOV-003",
                status="ERROR" if implemented else "PASS",
                severity="ERROR" if implemented else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Placeholder repositories must not be represented as fully implemented.",
                recommended_owner=owner,
                remediation_category="classification",
                evidence={"implemented": implemented, "match": observed_state["matches"][:1]},
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.95,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if declared.get("planned_extraction"):
        independent = bool(match and match["classification"] in {"FIRST_PARTY_ACTIVE", "FIRST_PARTY_INCOMPLETE"} and not declared.get("embedded_in"))
        findings.append(
            _finding(
                rule_id="NEOS-GOV-004",
                status="WARNING" if independent else "PASS",
                severity="WARNING" if independent else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Planned extractions must remain distinguishable from already independent repositories until Platform Core is updated.",
                recommended_owner=owner,
                remediation_category="architecture_review",
                evidence={"independent": independent, "match": observed_state["matches"][:1]},
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.92,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if "embedded" in _normalize_text(declared.get("identity_kind")):
        independent = bool(match and match["classification"] in {"FIRST_PARTY_ACTIVE", "FIRST_PARTY_INCOMPLETE"})
        findings.append(
            _finding(
                rule_id="NEOS-GOV-005",
                status="ERROR" if independent else "PASS",
                severity="ERROR" if independent else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Embedded systems must not be mistaken for independent repositories.",
                recommended_owner=owner,
                remediation_category="architecture_boundary",
                evidence={"independent": independent, "embedded_in": declared.get("embedded_in")},
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.95,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if any(token in _normalize_text(declared.get("classification")) or token in _normalize_text(declared.get("identity_kind")) for token in ("vendor", "reference")):
        non_canonical = bool(match and match["classification"] in {"FIRST_PARTY_ACTIVE", "FIRST_PARTY_PLANNED", "FIRST_PARTY_INCOMPLETE"})
        findings.append(
            _finding(
                rule_id="NEOS-GOV-006",
                status="ERROR" if non_canonical else "PASS",
                severity="ERROR" if non_canonical else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Reference and vendor identities must not be treated as canonical New Earth product owners.",
                recommended_owner=owner,
                remediation_category="classification",
                evidence={"observed_classification": match["classification"] if match else None},
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.93,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if declared.get("legacy") or "legacy" in _normalize_text(declared.get("identity_kind")):
        active_canonical = bool(match and match["classification"] in {"FIRST_PARTY_ACTIVE", "FIRST_PARTY_INCOMPLETE"})
        findings.append(
            _finding(
                rule_id="NEOS-GOV-007",
                status="WARNING" if active_canonical else "PASS",
                severity="WARNING" if active_canonical else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Legacy or superseded systems must remain represented as legacy unless succession has been explicitly updated.",
                recommended_owner=owner,
                remediation_category="succession",
                evidence={"observed_classification": match["classification"] if match else None},
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.9,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if match and declared.get("role") in {"SHELL", "OPERATIONS_UI"}:
        observed_capabilities = set(match["capabilities"])
        authority_capabilities = {
            "architecture_truth",
            "architecture_governance",
            "engineering_drift",
            "repository_intelligence",
            "portfolio_intelligence",
        }
        boundary_violation = bool(observed_capabilities & authority_capabilities)
        findings.append(
            _finding(
                rule_id="NEOS-GOV-008",
                status="ERROR" if boundary_violation else "PASS",
                severity="ERROR" if boundary_violation else "INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="Thin front-door and dashboard systems must not become authoritative truth scanners.",
                recommended_owner=owner,
                remediation_category="boundary",
                evidence={"observed_capabilities": sorted(observed_capabilities)},
                affected={"project_ids": [match["project_id"]]},
                confidence=0.9,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if match:
        declared_interfaces = {item for item in declared.get("interfaces", []) if item}
        observed_interfaces = {item for item in observed_state.get("interfaces", []) if item}
        if declared_interfaces and observed_interfaces and declared_interfaces <= observed_interfaces:
            contract_status = "PASS"
            contract_severity = "INFO"
            explanation = "Declared interfaces are visible in the observed contract surface."
        elif declared_interfaces and observed_interfaces and declared_interfaces & observed_interfaces:
            contract_status = "WARNING"
            contract_severity = "WARNING"
            explanation = "Declared interfaces partially overlap with the observed contract surface."
        elif declared_interfaces:
            contract_status = "UNKNOWN"
            contract_severity = "INFO"
            explanation = "Declared interfaces could not be verified against the observed contract surface."
        else:
            contract_status = "PASS"
            contract_severity = "INFO"
            explanation = "No declared interfaces were supplied for comparison."
        findings.append(
            _finding(
                rule_id="NEOS-GOV-011",
                status=contract_status,
                severity=contract_severity,
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation=explanation,
                recommended_owner=owner,
                remediation_category="contract",
                evidence={
                    "declared_interfaces": sorted(declared_interfaces),
                    "observed_interfaces": sorted(observed_interfaces),
                },
                affected={"project_ids": [match["project_id"]]},
                confidence=0.92,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    declared_dependencies = {item for item in declared.get("dependencies", []) if item}
    observed_dependencies = {item for item in observed_state.get("dependencies", []) if item}
    if declared_dependencies or observed_dependencies:
        if not match and declared_dependencies:
            dep_status = "UNKNOWN"
            dep_severity = "INFO"
            explanation = "Dependency evidence exists in Platform Core, but NEOS cannot verify the repository directly."
        elif declared_dependencies == observed_dependencies and declared_dependencies:
            dep_status = "PASS"
            dep_severity = "INFO"
            explanation = "Declared and observed dependencies align."
        elif declared_dependencies and observed_dependencies and declared_dependencies & observed_dependencies:
            dep_status = "WARNING"
            dep_severity = "WARNING"
            explanation = "Declared and observed dependencies overlap but do not fully align."
        elif declared_dependencies and not observed_dependencies:
            dep_status = "WARNING"
            dep_severity = "WARNING"
            explanation = "Declared dependencies are not yet observed in NEOS evidence."
        elif observed_dependencies and not declared_dependencies:
            dep_status = "WARNING"
            dep_severity = "WARNING"
            explanation = "Observed dependencies are not declared in Platform Core."
        else:
            dep_status = "UNKNOWN"
            dep_severity = "INFO"
            explanation = "Dependency evidence is insufficient to decide."
        findings.append(
            _finding(
                rule_id="NEOS-GOV-010",
                status=dep_status,
                severity=dep_severity,
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation=explanation,
                recommended_owner=owner,
                remediation_category="dependency",
                evidence={
                    "declared_dependencies": sorted(declared_dependencies),
                    "observed_dependencies": sorted(observed_dependencies),
                },
                affected={"project_ids": [match["project_id"]] if match else []},
                confidence=0.9 if dep_status != "UNKNOWN" else 0.5,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    if match:
        findings.append(
            _finding(
                rule_id="NEOS-GOV-014",
                status="PASS",
                severity="INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="System identity is preserved separately from repository identity.",
                recommended_owner=owner,
                remediation_category="identity",
                evidence={
                    "declared_identity_kind": declared.get("identity_kind"),
                    "observed_classification": match["classification"],
                    "observed_repo_path": match["repo_path"],
                },
                affected={"project_ids": [match["project_id"]]},
                confidence=0.9,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )
    else:
        findings.append(
            _finding(
                rule_id="NEOS-GOV-014",
                status="PASS" if not _declared_requires_observed_repo(declared) else "UNKNOWN",
                severity="INFO",
                system_id=finding_system_id,
                canonical_owner=owner,
                declared_state=declared_state,
                observed_state=observed_state,
                explanation="System identity remains distinct from repository identity even when the repository is absent or non-repository by design.",
                recommended_owner=owner,
                remediation_category="identity",
                evidence={
                    "declared_identity_kind": declared.get("identity_kind"),
                    "observed_state": observed_state["state"],
                },
                affected={"project_ids": []},
                confidence=0.86,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )

    system_report = {
        "system_id": declared_system_id,
        "project_id": declared.get("project_id"),
        "name": declared.get("name"),
        "role": declared.get("role"),
        "owner": owner,
        "declared_state": declared_state,
        "observed_state": observed_state,
        "matches": observed_matches,
        "finding_count": len(findings),
        "status": _system_status(findings),
    }
    return system_report, findings


def _system_status(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "UNKNOWN"
    if any(item["severity"] == "BLOCKER" for item in findings):
        return "BLOCKER"
    if any(item["status"] == "ERROR" for item in findings):
        return "ERROR"
    if any(item["status"] == "WARNING" for item in findings):
        return "WARNING"
    if any(item["status"] == "UNKNOWN" for item in findings):
        return "UNKNOWN"
    return "PASS"


def _scanned_repositories(estate_roots: list[Path]) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    for root in estate_roots:
        if not root.exists() or not root.is_dir():
            continue
        queue: list[tuple[Path, int]] = [(root, 0)]
        seen: set[Path] = set()
        while queue:
            current, depth = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            if current != root:
                if (current / ".git").exists() or _first_existing_path(
                    [
                        current / "project.neos.json",
                        current / "project.neos.yaml",
                        current / "project.neos.yml",
                        current / "project.json",
                        current / "project.yaml",
                        current / "project.yml",
                        current / "manifest.json",
                    ]
                ) is not None:
                    candidates.append(current)
                else:
                    name = _normalize_text(current.name)
                    if any(marker in name for marker in _REPOSITORY_MARKERS):
                        candidates.append(current)
            if depth >= 2:
                continue
            try:
                children = [item for item in current.iterdir() if item.is_dir()]
            except OSError:
                continue
            for child in children:
                queue.append((child, depth + 1))
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    repositories: list[dict[str, Any]] = []
    for path in sorted(unique):
        profile = repo_profile(path)
        manifest = profile.get("manifest", {})
        text = " ".join(
            str(part)
            for part in (
                profile.get("name"),
                profile.get("project_id"),
                profile.get("project_family"),
                profile.get("project_type"),
                " ".join(manifest.get("tags", [])) if isinstance(manifest, dict) else "",
                " ".join(manifest.get("capabilities", [])) if isinstance(manifest, dict) else "",
            )
        ).lower()
        if not any(marker in text for marker in _REPOSITORY_MARKERS) and not manifest:
            continue
        if not (path / ".git").exists() and not manifest:
            continue
        repositories.append(
            {
                "repo_path": str(path.resolve()),
                "remote_url": profile.get("remote_url"),
                "branch": profile.get("branch"),
                "commit": profile.get("commit"),
                "dirty": profile.get("dirty"),
                "name": profile.get("name"),
                "project_id": profile.get("project_id") or path.name,
                "project_family": profile.get("project_family"),
                "project_type": profile.get("project_type"),
                "manifest": manifest,
                "profile": profile,
            }
        )
    return repositories


def _observed_repo_lookup(observed_projects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for project in observed_projects:
        for key in {
            _normalize_text(project["project_id"]),
            _normalize_text(project["name"]),
            _normalize_text(Path(project["repo_path"]).name),
            _normalize_text(project.get("remote_url")),
        }:
            if key and key not in lookup:
                lookup[key] = project
    return lookup


def _find_unregistered_repositories(
    *,
    declared_systems: list[dict[str, Any]],
    observed_projects: list[dict[str, Any]],
    estate_roots: list[Path],
    platform_core: dict[str, Any],
    source_commit: str | None,
) -> list[dict[str, Any]]:
    if not estate_roots:
        return []
    declared_keys = {
        _normalize_text(system["system_id"])
        for system in declared_systems
    } | {
        _normalize_text(system["name"])
        for system in declared_systems
    } | {
        _normalize_text(system["repository"]["path"])
        for system in declared_systems
        if system["repository"]["path"]
    }
    declared_keys.update(_normalize_text(system["repository"].get("canonical_repo")) for system in declared_systems)
    declared_keys.discard("")
    observed_lookup = _observed_repo_lookup(observed_projects)
    findings: list[dict[str, Any]] = []
    for repo in _scanned_repositories(estate_roots):
        key_candidates = {
            _normalize_text(repo["project_id"]),
            _normalize_text(repo["name"]),
            _normalize_text(Path(repo["repo_path"]).name),
            _normalize_text(repo.get("remote_url")),
        }
        if any(key in declared_keys for key in key_candidates if key):
            continue
        if any(key in observed_lookup for key in key_candidates if key):
            continue
        profile_text = " ".join(
            str(part)
            for part in (
                repo.get("name"),
                repo.get("project_id"),
                repo.get("project_family"),
                " ".join(repo.get("manifest", {}).get("tags", [])) if isinstance(repo.get("manifest"), dict) else "",
            )
        ).lower()
        if not any(marker in profile_text for marker in _REPOSITORY_MARKERS):
            continue
        findings.append(
            _finding(
                rule_id="NEOS-GOV-012",
                status="WARNING",
                severity="WARNING",
                system_id=repo["project_id"],
                canonical_owner=repo.get("project_family") or repo.get("name") or repo["project_id"],
                declared_state={
                    "system_id": repo["project_id"],
                    "name": repo.get("name"),
                    "repository": {
                        "path": None,
                        "remote": None,
                        "branch": None,
                    },
                    "classification": "UNREGISTERED",
                },
                observed_state={
                    "state": "OBSERVED",
                    "repo_path": repo["repo_path"],
                    "remote_url": repo.get("remote_url"),
                    "branch": repo.get("branch"),
                    "commit": repo.get("commit"),
                    "dirty": repo.get("dirty"),
                    "manifest": repo.get("manifest"),
                    "profile": repo.get("profile"),
                },
                explanation="Observed New Earth-style repository is not registered in Platform Core governance.",
                recommended_owner="Platform Core",
                remediation_category="registration",
                evidence={
                    "estate_roots": [str(path) for path in estate_roots],
                    "repo_profile": repo,
                },
                affected={"repositories": [repo["repo_path"]]},
                confidence=0.84,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )
    return findings


def _find_duplicate_capability_ownership(
    observed_projects: list[dict[str, Any]],
    platform_core: dict[str, Any],
    *,
    source_commit: str | None,
) -> list[dict[str, Any]]:
    capabilities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in observed_projects:
        if not project.get("is_first_party"):
            continue
        for capability in project.get("capabilities", []):
            capabilities[capability].append(project)
    findings: list[dict[str, Any]] = []
    focus = {"repository_intelligence", "engineering_drift", "architecture_truth", "ai_reasoning", "backup_engine", "experiment_validation", "knowledge_librarian", "voice_intelligence"}
    for capability, projects in sorted(capabilities.items()):
        if capability not in focus or len(projects) < 2:
            continue
        project_ids = sorted(project["project_id"] for project in projects)
        findings.append(
            _finding(
                rule_id="NEOS-GOV-009",
                status="WARNING",
                severity="WARNING",
                system_id=capability,
                canonical_owner="Platform Core",
                declared_state={"capability": capability, "canonical_owner": "single owner expected"},
                observed_state={"project_ids": project_ids, "project_count": len(project_ids)},
                explanation="Platform Core declares a single canonical owner, but NEOS observes the capability in multiple first-party systems.",
                recommended_owner="Platform Core",
                remediation_category="ownership",
                evidence={"projects": project_ids},
                affected={"project_ids": project_ids},
                confidence=0.88,
                platform_core=platform_core,
                source_commit=source_commit,
            )
        )
    return findings


def _governance_summary(findings: list[dict[str, Any]], platform_core: dict[str, Any]) -> dict[str, Any]:
    status_counts = Counter(item["status"] for item in findings)
    severity_counts = Counter(item["severity"] for item in findings)
    unknowns = [item for item in findings if item["status"] == "UNKNOWN"]
    blocking = [item for item in findings if item["severity"] == "BLOCKER" or item["status"] == "ERROR"]
    if platform_core.get("status") != "AVAILABLE":
        readiness = "UNKNOWN"
    elif any(item["severity"] == "BLOCKER" for item in findings) or any(item["status"] == "ERROR" for item in findings):
        readiness = "NOT_READY"
    elif any(item["status"] == "WARNING" for item in findings):
        readiness = "READY_WITH_WARNINGS"
    elif any(item["status"] == "UNKNOWN" for item in findings):
        readiness = "UNKNOWN"
    else:
        readiness = "READY"
    if readiness not in GOVERNANCE_RESULT_STATES:
        readiness = "UNKNOWN"
    return {
        "readiness": readiness,
        "status_counts": dict(status_counts),
        "severity_counts": dict(severity_counts),
        "blocking_findings": [item["id"] for item in blocking],
        "unknown_count": len(unknowns),
        "finding_count": len(findings),
    }


def _governance_snapshot_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "platform_core_governance_version": report["platform_core"].get("governance_version"),
        "platform_core_governance_hash": report["platform_core"].get("registry_hash"),
        "platform_core_merge_commit": report["platform_core"].get("platform_core_merge_commit"),
        "neos_version": __version__,
        "neos_commit": report["source_commit"],
        "observed_at": report.get("observed_at"),
        "readiness": report["summary"]["readiness"],
        "status_counts": report["summary"]["status_counts"],
        "severity_counts": report["summary"]["severity_counts"],
        "findings": [item["id"] for item in report["findings"]],
        "unresolved_unknowns": [item["id"] for item in report["findings"] if item["status"] == "UNKNOWN"],
        "evidence_references": {
            "platform_core_governance_path": report["platform_core"].get("governance_path"),
            "platform_core_schema_path": report["platform_core"].get("schema_path"),
            "observed_project_count": report["observed"]["project_count"],
        },
    }


def governance_report(
    db_path: Path,
    *,
    platform_core_root: str | Path | None = None,
    estate_roots: Iterable[str | Path] | str | Path | None = None,
) -> dict[str, Any]:
    source_commit = _current_neos_commit()
    platform_core_root_path = resolve_platform_core_root(platform_core_root)
    platform_core, governance_doc = _load_platform_core_document(platform_core_root_path)
    observed_projects = _observed_projects(db_path)
    observed_index = _index_observed_projects(observed_projects)
    declared_systems = platform_core.get("declared", {}).get("systems", [])
    systems: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for declared in declared_systems:
        matches = _match_declared_system(declared, observed_index)
        system_report, system_findings = _evaluate_system(
            declared,
            observed_matches=matches,
            platform_core=platform_core,
            db_path=db_path,
            source_commit=source_commit,
        )
        systems.append(system_report)
        findings.extend(system_findings)
    roots = resolve_estate_roots(estate_roots, platform_core=platform_core)
    findings.extend(
        _find_unregistered_repositories(
            declared_systems=declared_systems,
            observed_projects=observed_projects,
            estate_roots=roots,
            platform_core=platform_core,
            source_commit=source_commit,
        )
    )
    findings.extend(_find_duplicate_capability_ownership(observed_projects, platform_core, source_commit=source_commit))
    findings = sorted(
        findings,
        key=lambda item: (
            item["rule_id"],
            item.get("system_id") or "",
            item.get("id") or "",
        ),
    )
    summary = _governance_summary(findings, platform_core)
    report: dict[str, Any] = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "governance_version": platform_core.get("governance_version"),
        "platform_core": platform_core,
        "observed": {
            "project_count": len(observed_projects),
            "projects": observed_projects,
            "estate_roots": [str(path) for path in roots],
        },
        "declared": {
            "system_count": len(declared_systems),
            "systems": declared_systems,
            "repositories": platform_core.get("declared", {}).get("repositories", []),
            "dependencies": platform_core.get("declared", {}).get("dependencies", []),
            "interfaces": platform_core.get("declared", {}).get("interfaces", []),
            "services": platform_core.get("declared", {}).get("services", []),
            "estate_roots": platform_core.get("declared", {}).get("estate_roots", []),
        },
        "systems": systems,
        "findings": findings,
        "summary": summary,
        "observed_at": utc_now(),
        "source_commit": source_commit,
        "governance_doc": governance_doc,
    }
    snapshot: dict[str, Any] = _governance_snapshot_payload(report)
    snapshot["source_fingerprint"] = _stable_hash(
        {
            "platform_core": report["platform_core"].get("registry_hash"),
            "observed_projects": [
                {
                    "project_id": item["project_id"],
                    "repo_path": item["repo_path"],
                    "commit": item["commit"],
                    "classification": item["classification"],
                    "capabilities": item["capabilities"],
                    "dependencies": item["observed_dependencies"],
                }
                for item in observed_projects
            ],
            "findings": [item["id"] for item in findings],
            "readiness": summary["readiness"],
        }
    )
    snapshot["id"] = "gov-" + _stable_hash(
        {
            "schema_version": snapshot["schema_version"],
            "platform_core_governance_version": snapshot["platform_core_governance_version"],
            "platform_core_governance_hash": snapshot["platform_core_governance_hash"],
            "platform_core_merge_commit": snapshot["platform_core_merge_commit"],
            "neos_version": snapshot["neos_version"],
            "source_fingerprint": snapshot["source_fingerprint"],
            "readiness": snapshot["readiness"],
            "status_counts": snapshot["status_counts"],
            "severity_counts": snapshot["severity_counts"],
            "findings": snapshot["findings"],
            "unresolved_unknowns": snapshot["unresolved_unknowns"],
            "evidence_references": snapshot["evidence_references"],
        }
    )[:24]
    report["snapshot"] = snapshot
    for item in report["findings"]:
        item["snapshot_id"] = snapshot["id"]
    for system in report["systems"]:
        system["snapshot_id"] = snapshot["id"]
    return report


def governance_status(
    db_path: Path,
    *,
    platform_core_root: str | Path | None = None,
    estate_roots: Iterable[str | Path] | str | Path | None = None,
) -> dict[str, Any]:
    report = governance_report(db_path, platform_core_root=platform_core_root, estate_roots=estate_roots)
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "status": report["summary"]["readiness"],
        "summary": report["summary"],
        "platform_core": report["platform_core"],
        "observed": report["observed"],
        "declared": report["declared"],
        "snapshot": report["snapshot"],
    }


def governance_findings(
    db_path: Path,
    *,
    platform_core_root: str | Path | None = None,
    estate_roots: Iterable[str | Path] | str | Path | None = None,
) -> dict[str, Any]:
    report = governance_report(db_path, platform_core_root=platform_core_root, estate_roots=estate_roots)
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "status": report["summary"]["readiness"],
        "count": len(report["findings"]),
        "findings": report["findings"],
        "summary": report["summary"],
        "platform_core": report["platform_core"],
        "snapshot": report["snapshot"],
    }


def governance_project(
    db_path: Path,
    project_id: str,
    *,
    platform_core_root: str | Path | None = None,
    estate_roots: Iterable[str | Path] | str | Path | None = None,
) -> dict[str, Any]:
    report = governance_report(db_path, platform_core_root=platform_core_root, estate_roots=estate_roots)
    for system in report["systems"]:
        if system["project_id"] == project_id or system["system_id"] == project_id:
            return {
                "schema_version": GOVERNANCE_SCHEMA_VERSION,
                "status": system["status"],
                "project_id": project_id,
                "system": system,
                "findings": [item for item in report["findings"] if item.get("system_id") in {project_id, system["system_id"]}],
                "platform_core": report["platform_core"],
                "snapshot": report["snapshot"],
            }
    observed_project = next((item for item in report["observed"]["projects"] if item["project_id"] == project_id), None)
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "status": "UNKNOWN",
        "project_id": project_id,
        "system": None,
        "observed": observed_project,
        "findings": [item for item in report["findings"] if item.get("system_id") == project_id],
        "platform_core": report["platform_core"],
        "snapshot": report["snapshot"],
    }


def governance_snapshot(
    db_path: Path,
    *,
    platform_core_root: str | Path | None = None,
    estate_roots: Iterable[str | Path] | str | Path | None = None,
) -> dict[str, Any]:
    return governance_report(db_path, platform_core_root=platform_core_root, estate_roots=estate_roots)["snapshot"]
