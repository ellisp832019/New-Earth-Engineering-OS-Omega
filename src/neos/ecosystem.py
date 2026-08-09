from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .flight import latest_project_flight
from .genome import latest_project_genome
from .memory import latest_project_memory

ECOSYSTEM_SCHEMA_VERSION = 1

CAPABILITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "authentication": ("auth", "login", "token", "oauth", "signin"),
    "configuration": ("config", "configuration", "settings", "preferences"),
    "desktop_interface": ("flutter", "desktop", "windows", "gui", "ui"),
    "diagnostics": ("diagnostic", "health", "doctor", "troubleshoot", "debug"),
    "documentation": ("doc", "docs", "readme", "markdown"),
    "hardware_abstraction": ("hardware", "sensor", "embedded", "firmware", "gpio", "esp32"),
    "ai_reasoning": ("ai", "llm", "assistant", "provider", "conversation"),
    "local_api": ("api", "http", "endpoint", "service"),
    "logging": ("log", "logging", "logger"),
    "release_management": ("release", "package", "deploy", "build"),
    "repository_intelligence": ("scan", "genome", "memory", "flight", "semantic", "repository intelligence"),
    "sensor_acquisition": ("sensor", "sensing", "measurement", "probe"),
    "telemetry": ("telemetry", "metric", "metrics", "analytics"),
    "testing": ("test", "tests", "spec", "pytest", "flutter test"),
}


@dataclass(frozen=True)
class EngineeringEcosystem:
    id: str
    name: str
    created_at: str
    updated_at: str
    project_ids: list[str]
    snapshot_id: str
    schema_version: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class PortfolioSnapshot:
    id: str
    name: str
    created_at: str
    project_ids: list[str]
    ecosystem_id: str
    source_fingerprint: str
    snapshot: dict[str, Any]
    metadata: dict[str, Any]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _project_row(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown project: {project_id}")
    return row


def _safe_count(conn, query: str, params: tuple[Any, ...]) -> int:
    try:
        row = conn.execute(query, params).fetchone()
    except sqlite3.Error:
        return 0
    if not row:
        return 0
    value = row[0] if not isinstance(row, dict) else next(iter(row.values()))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _search_text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, dict):
            parts.extend(_search_text(*value.values()).split())
        elif isinstance(value, list):
            parts.extend(_search_text(*value).split())
        else:
            text = str(value).strip()
            if text:
                parts.append(text.lower())
    return " ".join(parts)


def _search_score(query: str, *values: Any) -> int:
    text = _search_text(*values)
    if not text:
        return 0
    score = 0
    for token in query.lower().split():
        if token in text:
            score += 5
        for fragment in text.split():
            if token == fragment:
                score += 2
    return score


def _normalise_technology(entry: Any) -> dict[str, Any]:
    if isinstance(entry, dict):
        name = str(entry.get("name") or entry.get("technology") or entry.get("id") or entry.get("value") or "").strip()
        version = str(entry.get("version") or entry.get("specifier") or entry.get("range") or "").strip()
        category = str(entry.get("category") or "unknown").strip()
        evidence = _safe_list(entry.get("evidence"))
    else:
        text = str(entry).strip()
        name = text
        version = ""
        category = "unknown"
        evidence = []
        if "==" in text:
            name, version = [part.strip() for part in text.split("==", 1)]
        elif ":" in text and "/" not in text:
            name, version = [part.strip() for part in text.split(":", 1)]
    return {
        "name": name or "unknown",
        "version": version,
        "category": category,
        "evidence": evidence,
        "raw": entry,
    }


def _project_manifest(row: Any) -> dict[str, Any]:
    return _json_loads(row["manifest_json"], {})


def _domains_from_genome(genome: dict[str, Any]) -> list[dict[str, Any]]:
    domains = genome.get("domains", []) if isinstance(genome, dict) else []
    if isinstance(domains, dict):
        items = domains.get("items", [])
        return items if isinstance(items, list) else []
    return domains if isinstance(domains, list) else []


def _manifest_tags(manifest: dict[str, Any]) -> list[str]:
    tags = manifest.get("tags") or manifest.get("labels") or manifest.get("categories") or []
    if isinstance(tags, str):
        tags = [tags]
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def _project_status(row: Any, manifest: dict[str, Any]) -> str:
    for key in ("status", "project_status", "lifecycle_status"):
        value = manifest.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    lifecycle = str(row["lifecycle"] or "").strip().lower()
    if lifecycle in {"active", "experimental", "maintenance", "archived"}:
        return lifecycle
    if lifecycle:
        return lifecycle
    if manifest.get("archived") is True:
        return "archived"
    return "unknown"


def _project_family(manifest: dict[str, Any]) -> str:
    for key in ("family", "project_family", "portfolio_family"):
        value = manifest.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    portfolio = manifest.get("portfolio")
    if isinstance(portfolio, dict):
        value = portfolio.get("family")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _project_dependencies(manifest: dict[str, Any]) -> list[str]:
    candidates: list[Any] = []
    for key in ("project_dependencies", "depends_on_projects", "dependencies"):
        value = manifest.get(key)
        if value:
            candidates.extend(_safe_list(value))
    portfolio = manifest.get("portfolio")
    if isinstance(portfolio, dict):
        for key in ("dependencies", "depends_on_projects"):
            value = portfolio.get(key)
            if value:
                candidates.extend(_safe_list(value))
    description = str(manifest.get("description") or "")
    for token in description.replace(",", " ").split():
        token_lc = token.lower().strip()
        for prefix in ("depends-on:", "depends_on:", "depends-on=", "depends_on="):
            if token_lc.startswith(prefix):
                candidates.append(token.split(":", 1)[-1].split("=", 1)[-1])
        if token_lc.startswith("depends:"):
            candidates.append(token.split(":", 1)[-1])
    dependency_ids: list[str] = []
    for item in candidates:
        if isinstance(item, str):
            dependency_ids.append(item.strip())
        elif isinstance(item, dict):
            for key in ("project_id", "target_project_id", "id", "name"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    dependency_ids.append(value.strip())
                    break
    return sorted({dep for dep in dependency_ids if dep})


def _evidence_text(entry: dict[str, Any]) -> str:
    parts = [entry.get("name", ""), entry.get("status", ""), entry.get("family", "")]
    parts.extend(entry.get("tags", []))
    parts.extend(
        [
            str(entry.get("project_id", "")),
            str(entry.get("name", "")),
            str(entry.get("repository_type", "")),
            str(entry.get("lifecycle", "")),
        ]
    )
    for tech in entry.get("technologies", []):
        parts.append(str(tech.get("name", "")))
        parts.append(str(tech.get("version", "")))
        parts.append(str(tech.get("category", "")))
    for feature in entry.get("features", []):
        parts.append(str(feature.get("name", "")))
        parts.append(str(feature.get("description", "")))
    for decision in entry.get("decisions", []):
        parts.append(str(decision.get("title", "")))
        parts.append(str(decision.get("decision", "")))
        parts.append(str(decision.get("rationale", "")))
    return " ".join(part.lower() for part in parts if part)


def _capability_keywords() -> dict[str, tuple[str, ...]]:
    return CAPABILITY_KEYWORDS


def _project_capabilities(entry: dict[str, Any]) -> list[dict[str, Any]]:
    text = _evidence_text(entry)
    capabilities: list[dict[str, Any]] = []
    evidence_paths = sorted({*(entry.get("documentation_paths", [])), *(entry.get("test_paths", [])), *(entry.get("feature_paths", []))})
    for capability, keywords in _capability_keywords().items():
        hits = [keyword for keyword in keywords if keyword in text]
        if capability == "configuration" and entry.get("configuration_count", 0) > 0:
            hits.append("configuration-keys")
        if capability == "local_api" and entry.get("api_count", 0) > 0:
            hits.append("api-endpoints")
        if capability == "repository_intelligence" and (entry.get("scan_id") or entry.get("genome_id") or entry.get("memory_id")):
            hits.append("analysis-snapshots")
        if capability == "testing" and entry.get("test_count", 0) > 0:
            hits.append("test-evidence")
        if not hits:
            continue
        confidence = min(0.98, 0.55 + 0.08 * len(hits))
        maturity_score = entry.get("test_count", 0) + entry.get("docs_count", 0) + entry.get("feature_count", 0)
        if maturity_score >= 10:
            maturity = "mature"
        elif maturity_score >= 5:
            maturity = "established"
        else:
            maturity = "emerging"
        capabilities.append(
            {
                "capability": capability,
                "project_id": entry["project_id"],
                "project_name": entry["name"],
                "maturity": maturity,
                "confidence": round(confidence, 3),
                "evidence_paths": evidence_paths[:10],
                "evidence": {
                    "feature_count": entry.get("feature_count", 0),
                    "test_count": entry.get("test_count", 0),
                    "docs_count": entry.get("docs_count", 0),
                    "api_count": entry.get("api_count", 0),
                    "configuration_count": entry.get("configuration_count", 0),
                },
                "signal_count": len(hits),
            }
        )
    return capabilities


def _load_project_entry(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = _project_row(conn, project_id)
    manifest = _project_manifest(row)
    scan = _latest_scan_row(conn, project_id)
    scan_snapshot = _json_loads(scan["snapshot_json"], {}) if scan else {}
    technologies = [_normalise_technology(item) for item in _safe_list(manifest.get("technologies") or [])]
    detected_plugins = [_normalise_technology(item) for item in _safe_list(scan_snapshot.get("detected_plugins") or [])]
    tech_map: dict[tuple[str, str], dict[str, Any]] = {}
    for item in [*technologies, *detected_plugins]:
        key = (item["name"].lower(), item["version"].lower())
        tech_map.setdefault(key, item)
    technologies = sorted(tech_map.values(), key=lambda item: (item["name"].lower(), item["version"].lower()))
    feature_rows = conn.execute(
        "SELECT id, name, description, status, source, confidence, metadata_json FROM features WHERE project_id=? ORDER BY name, id",
        (project_id,),
    ).fetchall()
    decision_rows = conn.execute(
        "SELECT id, title, status, decision, rationale, source_path, confidence FROM engineering_decisions WHERE project_id=? ORDER BY COALESCE(date, created_at), title, id",
        (project_id,),
    ).fetchall()
    api_count = _safe_count(conn, "SELECT COUNT(*) FROM api_endpoints WHERE project_id=?", (project_id,))
    config_count = _safe_count(conn, "SELECT COUNT(*) FROM configuration_keys WHERE project_id=?", (project_id,))
    test_count = _safe_count(conn, "SELECT COUNT(*) FROM nodes WHERE project_id=? AND kind='test'", (project_id,))
    docs_count = _safe_count(conn, "SELECT COUNT(*) FROM nodes WHERE project_id=? AND kind IN ('documentation','release_documentation')", (project_id,))
    genome = {}
    memory = {}
    flight = {}
    try:
        genome = latest_project_genome(db_path, project_id)
    except (sqlite3.Error, ValueError, OSError):
        genome = {}
    try:
        memory = latest_project_memory(db_path, project_id)
    except (sqlite3.Error, ValueError, OSError):
        memory = {}
    try:
        flight = latest_project_flight(db_path, project_id)
    except (sqlite3.Error, ValueError, OSError):
        flight = {}
    conn.close()

    scan_id = scan["scan_id"] if scan else None
    latest_genome_id = genome.get("id") if isinstance(genome, dict) else None
    latest_memory_id = memory.get("id") if isinstance(memory, dict) else None
    latest_flight_id = flight.get("id") if isinstance(flight, dict) else None
    current_branch = scan["git_branch"] if scan else None
    current_commit = scan["git_commit"] if scan else None
    tags = _manifest_tags(manifest)
    status = _project_status(row, manifest)
    family = _project_family(manifest)
    repo_type = str((manifest.get("repository") or {}).get("type") or manifest.get("repository_type") or "git")
    project_entry = {
        "project_id": project_id,
        "display_name": row["name"],
        "name": row["name"],
        "repository_path": row["repo_path"],
        "repository_type": repo_type,
        "current_branch": current_branch,
        "current_commit": current_commit,
        "last_scan": _row_dict(scan),
        "last_scan_id": scan_id,
        "last_genome_id": latest_genome_id,
        "last_memory_id": latest_memory_id,
        "last_flight_id": latest_flight_id,
        "health": genome.get("project_health", {}) if isinstance(genome, dict) else {},
        "technologies": technologies,
        "technology_names": [item["name"] for item in technologies],
        "domains": _domains_from_genome(genome),
        "lifecycle": row["lifecycle"],
        "status": status,
        "tags": tags,
        "family": family,
        "manifest": manifest,
        "scan_id": scan_id,
        "genome_id": latest_genome_id,
        "memory_id": latest_memory_id,
        "flight_id": latest_flight_id,
        "feature_count": len(feature_rows),
        "test_count": test_count,
        "docs_count": docs_count,
        "api_count": api_count,
        "configuration_count": config_count,
        "features": [dict(row) for row in feature_rows],
        "decisions": [dict(row) for row in decision_rows],
        "documentation_paths": [],
        "test_paths": [],
        "feature_paths": [row["source_path"] for row in feature_rows if "source_path" in row],
        "dependency_project_ids": _project_dependencies(manifest),
    }
    return project_entry


def project_registry_v2(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute("SELECT project_id FROM projects ORDER BY name, project_id").fetchall()
    conn.close()
    projects = [_load_project_entry(db_path, row["project_id"]) for row in rows]
    return {
        "schema_version": 2,
        "project_count": len(projects),
        "projects": projects,
    }


def _snapshot_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def build_portfolio_snapshot(db_path: Path, project_ids: list[str] | None = None, *, name: str = "default") -> dict[str, Any]:
    registry = project_registry_v2(db_path)
    projects = registry["projects"]
    if project_ids:
        selected = [project for project in projects if project["project_id"] in set(project_ids)]
    else:
        selected = projects
    selected = sorted(selected, key=lambda item: item["project_id"])
    selected_project_ids = [project["project_id"] for project in selected]
    source_payload = {
        "name": name,
        "project_ids": selected_project_ids,
        "projects": [
            {
                "project_id": project["project_id"],
                "last_scan_id": project["last_scan_id"],
                "last_genome_id": project["last_genome_id"],
                "last_memory_id": project["last_memory_id"],
                "last_flight_id": project["last_flight_id"],
                "technologies": [(tech["name"], tech["version"]) for tech in project["technologies"]],
                "status": project["status"],
                "tags": project["tags"],
                "family": project["family"],
            }
            for project in selected
        ],
    }
    fingerprint = _snapshot_fingerprint(source_payload)
    snapshot_id = f"portfolio-snapshot-{fingerprint[:24]}"
    ecosystem_id = f"ecosystem-{fingerprint[:16]}"
    now = utc_now()
    snapshot_json = {
        "schema_version": ECOSYSTEM_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "ecosystem_id": ecosystem_id,
        "name": name,
        "project_ids": selected_project_ids,
        "projects": selected,
        "source_fingerprint": fingerprint,
        "created_at": now,
    }
    conn = connect(db_path)
    conn.execute(
        """
        INSERT INTO ecosystems(id,name,created_at,updated_at,project_ids,snapshot_id,schema_version,metadata_json)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            updated_at=excluded.updated_at,
            project_ids=excluded.project_ids,
            snapshot_id=excluded.snapshot_id,
            schema_version=excluded.schema_version,
            metadata_json=excluded.metadata_json
        """,
        (
            ecosystem_id,
            name,
            now,
            now,
            _json_dumps(snapshot_json["project_ids"]),
            snapshot_id,
            ECOSYSTEM_SCHEMA_VERSION,
            _json_dumps({"source_fingerprint": fingerprint}),
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO portfolio_snapshots(
            id, name, ecosystem_id, project_ids, source_fingerprint, created_at, snapshot_json, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            snapshot_id,
            name,
            ecosystem_id,
            _json_dumps(snapshot_json["project_ids"]),
            fingerprint,
            now,
            _json_dumps(snapshot_json),
            _json_dumps({"project_count": len(selected), "schema_version": ECOSYSTEM_SCHEMA_VERSION}),
        ),
    )
    conn.commit()
    conn.close()
    return {
        "ecosystem": EngineeringEcosystem(
            id=ecosystem_id,
            name=name,
            created_at=now,
            updated_at=now,
            project_ids=selected_project_ids,
            snapshot_id=snapshot_id,
            schema_version=ECOSYSTEM_SCHEMA_VERSION,
            metadata={"source_fingerprint": fingerprint},
        ).__dict__,
        "portfolio_snapshot": PortfolioSnapshot(
            id=snapshot_id,
            name=name,
            created_at=now,
            project_ids=selected_project_ids,
            ecosystem_id=ecosystem_id,
            source_fingerprint=fingerprint,
            snapshot=snapshot_json,
            metadata={"project_count": len(selected)},
        ).__dict__,
    }


def latest_portfolio_snapshot(db_path: Path) -> dict[str, Any] | None:
    conn = connect(db_path)
    row = conn.execute("SELECT * FROM portfolio_snapshots ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return None
    payload = _json_loads(row["snapshot_json"], {})
    return {
        "id": row["id"],
        "name": row["name"],
        "ecosystem_id": row["ecosystem_id"],
        "project_ids": _json_loads(row["project_ids"], []),
        "source_fingerprint": row["source_fingerprint"],
        "created_at": row["created_at"],
        "snapshot": payload,
        "metadata": _json_loads(row["metadata_json"], {}),
    }


def _capabilities_by_name(project_capabilities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for capability in project_capabilities:
        grouped.setdefault(capability["capability"], []).append(capability)
    return grouped


def _technology_index(projects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for project in projects:
        for tech in project.get("technologies", []):
            key = tech["name"].lower()
            record = index.setdefault(
                key,
                {
                    "technology": tech["name"],
                    "versions": {},
                    "projects": [],
                    "category": tech.get("category", "unknown"),
                },
            )
            version_key = tech.get("version") or "unknown"
            record["projects"].append(project["project_id"])
            record["versions"].setdefault(version_key, [])
            record["versions"][version_key].append(project["project_id"])
    for record in index.values():
        record["projects"] = sorted(set(record["projects"]))
        record["project_count"] = len(record["projects"])
        record["shared"] = record["project_count"] > 1
        record["versions"] = {version: sorted(set(project_ids)) for version, project_ids in record["versions"].items()}
    return dict(sorted(index.items(), key=lambda item: item[0]))


def _shared_capabilities(project_capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = _capabilities_by_name(project_capabilities)
    items: list[dict[str, Any]] = []
    for capability, implementations in sorted(grouped.items(), key=lambda item: item[0]):
        if len(implementations) < 2:
            continue
        items.append(
            {
                "capability": capability,
                "project_ids": sorted({item["project_id"] for item in implementations}),
                "implementations": implementations,
                "count": len(implementations),
                "confirmed": len(implementations) >= 2,
            }
        )
    return items


def _project_quality_score(project: dict[str, Any]) -> float:
    return float(
        project.get("test_count", 0) * 2
        + project.get("docs_count", 0)
        + project.get("feature_count", 0)
        + project.get("api_count", 0)
        + project.get("configuration_count", 0)
    )


def _reuse_candidates(projects: list[dict[str, Any]], shared_capabilities: list[dict[str, Any]], technology_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    project_lookup = {project["project_id"]: project for project in projects}
    candidates: list[dict[str, Any]] = []
    for shared in shared_capabilities:
        implementations = shared["implementations"]
        source = max(implementations, key=lambda item: (_project_quality_score(project_lookup[item["project_id"]]), item["confidence"], item["project_id"]))
        targets = sorted(pid for pid in shared["project_ids"] if pid != source["project_id"])
        source_techs = {tech["name"].lower() for tech in project_lookup[source["project_id"]]["technologies"]}
        shared_techs = sorted(
            tech["technology"]
            for tech in technology_index.values()
            if source["project_id"] in tech["projects"] and any(target in tech["projects"] for target in targets)
        )
        candidates.append(
            {
                "candidate_id": f"reuse-{shared['capability']}-{source['project_id']}",
                "source_project": source["project_id"],
                "source_entitys": [],
                "capability": shared["capability"],
                "potential_target_projects": targets,
                "reason": f"{shared['capability']} is implemented in {len(shared['project_ids'])} projects with evidence-backed overlap.",
                "coupling_evidence": {
                    "shared_technologies": shared_techs,
                    "shared_capability": shared["capability"],
                    "source_project_quality": _project_quality_score(project_lookup[source["project_id"]]),
                    "source_technologies": sorted(source_techs),
                },
                "dependencies": project_lookup[source["project_id"]].get("dependency_project_ids", []),
                "test_evidence": project_lookup[source["project_id"]].get("test_count", 0),
                "documentation": project_lookup[source["project_id"]].get("docs_count", 0),
                "stability": "stable" if project_lookup[source["project_id"]].get("test_count", 0) > 0 else "emerging",
                "confidence": round(min(0.98, 0.55 + len(targets) * 0.08 + _project_quality_score(project_lookup[source["project_id"]]) / 100), 3),
                "risks": ["project-specific coupling requires review"],
                "required_adaptation": "review boundaries, project-specific configuration, and integration assumptions before reuse.",
            }
        )
    return candidates


def _duplicate_findings(projects: list[dict[str, Any]], shared_capabilities: list[dict[str, Any]], technology_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    project_lookup = {project["project_id"]: project for project in projects}
    findings: list[dict[str, Any]] = []
    for shared in shared_capabilities:
        project_ids = shared["project_ids"]
        shared_techs = [tech for tech in technology_index.values() if set(project_ids).issubset(set(tech["projects"])) or len(set(project_ids) & set(tech["projects"])) >= 2]
        source_projects = [project_lookup[project_id] for project_id in project_ids]
        if len(project_ids) < 2:
            continue
        dependency_present = any(dep in project_ids for project in source_projects for dep in project.get("dependency_project_ids", []))
        if dependency_present:
            conflict_type = "possible_overlap"
            confidence = 0.55
        elif shared_techs:
            conflict_type = "parallel_implementation"
            confidence = 0.7
        else:
            conflict_type = "likely_reusable_pattern"
            confidence = 0.6
        if len(shared["implementations"]) >= 2:
            findings.append(
                {
                    "id": f"duplicate-{shared['capability']}-{'-'.join(project_ids[:2])}",
                    "project_ids": project_ids,
                    "capability": shared["capability"],
                    "finding_type": conflict_type,
                    "reason": f"{shared['capability']} appears in multiple projects and should be reviewed for overlap versus intentional parallel implementation.",
                    "confidence": confidence,
                    "evidence": {
                        "shared_technologies": [tech["technology"] for tech in shared_techs],
                        "implementations": shared["implementations"],
                    },
                    "recommended_review": "compare architecture boundaries, test coverage, and project-specific coupling before consolidation.",
                }
            )
    return findings


def _dependency_relationships(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    project_lookup = {project["project_id"]: project for project in projects}
    for project in projects:
        for target in project.get("dependency_project_ids", []):
            if target not in project_lookup:
                continue
            relationships.append(
                {
                    "id": f"dependency-{project['project_id']}-{target}",
                    "source_project_id": project["project_id"],
                    "target_project_id": target,
                    "relationship_type": "cross_project_dependency",
                    "confidence": 0.9,
                    "evidence": {
                        "source": "manifest",
                        "project_id": project["project_id"],
                        "manifest_family": project.get("family", "unknown"),
                    },
                    "detector": "manifest_dependency",
                    "created_at": utc_now(),
                }
            )
    return relationships


def _decision_conflicts(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for index, left in enumerate(projects):
        left_decisions = left.get("decisions", [])
        left_text = " ".join(str(decision.get("decision", "")) for decision in left_decisions).lower()
        for right in projects[index + 1 :]:
            right_decisions = right.get("decisions", [])
            right_text = " ".join(str(decision.get("decision", "")) for decision in right_decisions).lower()
            if not left_text or not right_text:
                continue
            conflict_type = "unknown"
            reason = "Decisions exist but no clear alignment or conflict signal was detected."
            confidence = 0.4
            left_local = any(keyword in left_text for keyword in ("local-first", "offline", "local first"))
            right_cloud = any(keyword in right_text for keyword in ("cloud", "online", "remote", "mandatory"))
            right_local = any(keyword in right_text for keyword in ("local-first", "offline", "local first"))
            left_cloud = any(keyword in left_text for keyword in ("cloud", "online", "remote", "mandatory"))
            if (left_local and right_cloud) or (right_local and left_cloud):
                conflict_type = "potential_conflict"
                reason = "One project favors local-first behavior while the other favors cloud/remote behavior."
                confidence = 0.78
            elif left_text == right_text:
                conflict_type = "aligned"
                reason = "The projects record the same or very similar decision intent."
                confidence = 0.86
            elif any(keyword in left_text for keyword in right_text.split()[:3]):
                conflict_type = "different_context"
                reason = "The projects share some decision vocabulary but appear to be describing different contexts."
                confidence = 0.55
            conflicts.append(
                {
                    "id": f"decision-conflict-{left['project_id']}-{right['project_id']}",
                    "project_a": left["project_id"],
                    "project_b": right["project_id"],
                    "decision_a": left_decisions[0]["title"] if left_decisions else "",
                    "decision_b": right_decisions[0]["title"] if right_decisions else "",
                    "conflict_type": conflict_type,
                    "reason": reason,
                    "confidence": confidence,
                    "integration_relevance": "high" if conflict_type == "potential_conflict" else "medium",
                    "evidence": {
                        "project_a_decisions": left_decisions[:5],
                        "project_b_decisions": right_decisions[:5],
                    },
                    "recommended_review": "confirm whether the different decision contexts are intentional before integration.",
                }
            )
    return conflicts


def _portfolio_risks(
    projects: list[dict[str, Any]],
    technology_index: dict[str, dict[str, Any]],
    shared_capabilities: list[dict[str, Any]],
    dependency_relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    project_count = max(1, len(projects))
    for tech_key, tech in technology_index.items():
        if tech["project_count"] >= 2 and tech["project_count"] / project_count >= 0.5:
            risks.append(
                {
                    "id": f"risk-tech-{tech_key}",
                    "title": f"Technology concentration: {tech['technology']}",
                    "category": "dependency concentration risk",
                    "severity": "medium" if tech["project_count"] < project_count else "high",
                    "confidence": 0.8,
                    "affected_projects": tech["projects"],
                    "reason": "A shared technology is used across many registered projects, increasing portfolio coupling.",
                    "recommended_investigation": "check version drift, release cadence, and cross-project impact if the technology changes.",
                }
            )
    for shared in shared_capabilities:
        if all(implementation["evidence"]["test_count"] == 0 for implementation in shared["implementations"]):
            risks.append(
                {
                    "id": f"risk-capability-{shared['capability']}",
                    "title": f"Shared capability without test evidence: {shared['capability']}",
                    "category": "coverage gap",
                    "severity": "medium",
                    "confidence": 0.76,
                    "affected_projects": shared["project_ids"],
                    "reason": "Several projects implement the capability but there is no test evidence across the portfolio.",
                    "recommended_investigation": "add or link validation evidence before treating the capability as stable.",
                }
            )
    if dependency_relationships:
        centrality: dict[str, int] = {}
        for relation in dependency_relationships:
            centrality[relation["target_project_id"]] = centrality.get(relation["target_project_id"], 0) + 1
        for target, count in centrality.items():
            if count >= 2:
                risks.append(
                    {
                        "id": f"risk-central-{target}",
                        "title": f"High dependency concentration around {target}",
                        "category": "cross-project dependency concentration",
                        "severity": "high" if count >= 3 else "medium",
                        "confidence": 0.82,
                        "affected_projects": [relation["source_project_id"] for relation in dependency_relationships if relation["target_project_id"] == target],
                        "reason": "Multiple projects depend on the same upstream project.",
                        "recommended_investigation": "review whether this project should become a supported shared component or be de-risked.",
                    }
                )
    return risks


def _unknown_surface(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unknowns: list[dict[str, Any]] = []
    for project in projects:
        missing: list[str] = []
        for key in ("scan_id", "genome_id", "memory_id", "flight_id"):
            if not project.get(key):
                missing.append(key)
        if not project.get("test_count", 0):
            missing.append("test evidence")
        if not project.get("docs_count", 0):
            missing.append("documentation evidence")
        if missing:
            unknowns.append(
                {
                    "id": f"unknown-{project['project_id']}",
                    "project_id": project["project_id"],
                    "title": f"Unknown surface in {project['project_id']}",
                    "unknown_items": missing,
                    "confidence": 0.7 if len(missing) < 3 else 0.85,
                    "reason": "The project has missing or weak evidence in one or more portfolio dimensions.",
                }
            )
    return unknowns


def _attention_items(shared_capabilities: list[dict[str, Any]], reuse_candidates: list[dict[str, Any]], risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for shared in shared_capabilities[:10]:
        items.append(
            {
                "id": f"attention-{shared['capability']}",
                "type": "shared_capability",
                "summary": f"{len(shared['project_ids'])} projects implement {shared['capability']}.",
                "confidence": 0.8,
                "recommended_action": "compare implementation maturity and decide whether reuse or standardization review is warranted.",
            }
        )
    for candidate in reuse_candidates[:10]:
        items.append(
            {
                "id": candidate["candidate_id"],
                "type": "reuse_candidate",
                "summary": candidate["reason"],
                "confidence": candidate["confidence"],
                "recommended_action": candidate["required_adaptation"],
            }
        )
    for risk in risks[:10]:
        items.append(
            {
                "id": risk["id"],
                "type": "risk",
                "summary": risk["reason"],
                "confidence": risk["confidence"],
                "recommended_action": risk["recommended_investigation"],
            }
        )
    return items


def _portfolio_health(
    projects: list[dict[str, Any]],
    technology_index: dict[str, dict[str, Any]],
    shared_capabilities: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    unknowns: list[dict[str, Any]],
    reuse_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    project_count = len(projects)
    active_count = sum(1 for project in projects if project.get("status") != "archived")
    maturity_coverage = round(sum(1 for project in projects if project.get("feature_count", 0) or project.get("test_count", 0)) / project_count, 3) if project_count else 0.0
    documentation_coverage = round(sum(1 for project in projects if project.get("docs_count", 0)) / project_count, 3) if project_count else 0.0
    testing_evidence = round(sum(1 for project in projects if project.get("test_count", 0)) / project_count, 3) if project_count else 0.0
    decision_coverage = round(sum(1 for project in projects if project.get("decisions")) / project_count, 3) if project_count else 0.0
    unknown_surface = round(len(unknowns) / project_count, 3) if project_count else 0.0
    dependency_concentration = round(max((tech["project_count"] for tech in technology_index.values()), default=0) / project_count, 3) if project_count else 0.0
    reuse_opportunities = round(len(reuse_candidates) / max(1, len(shared_capabilities)), 3) if shared_capabilities else float(len(reuse_candidates) > 0)
    score = 100.0
    score -= min(30.0, unknown_surface * 30.0)
    score -= min(20.0, (1.0 - maturity_coverage) * 20.0)
    score -= min(15.0, (1.0 - documentation_coverage) * 15.0)
    score -= min(10.0, (1.0 - testing_evidence) * 10.0)
    score -= min(10.0, len(risks) * 2.0)
    score += min(10.0, reuse_opportunities * 5.0)
    score = max(0.0, min(100.0, round(score, 2)))
    return {
        "score": score,
        "project_count": project_count,
        "active_project_count": active_count,
        "dimension_scores": {
            "project_freshness": 1.0 if project_count else 0.0,
            "maturity_coverage": maturity_coverage,
            "testing_evidence": testing_evidence,
            "documentation_coverage": documentation_coverage,
            "decision_coverage": decision_coverage,
            "risk_distribution": max(0.0, round(1.0 - min(1.0, len(risks) / max(1, project_count)), 3)),
            "unknown_surface": max(0.0, round(1.0 - min(1.0, unknown_surface), 3)),
            "dependency_concentration": max(0.0, round(1.0 - min(1.0, dependency_concentration), 3)),
            "reuse_opportunities": min(1.0, reuse_opportunities),
        },
        "explanation": "Aggregate portfolio health emphasizes evidence coverage, unknown surface, concentration, and reuse opportunities without averaging project scores blindly.",
    }


def _persist_analysis(
    db_path: Path,
    ecosystem: dict[str, Any],
    snapshot: dict[str, Any],
    projects: list[dict[str, Any]],
    technology_index: dict[str, dict[str, Any]],
    shared_capabilities: list[dict[str, Any]],
    reuse_candidates: list[dict[str, Any]],
    duplicate_findings: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    decision_conflicts: list[dict[str, Any]],
    portfolio_risks: list[dict[str, Any]],
    attention_items: list[dict[str, Any]],
) -> None:
    conn = connect(db_path)
    now = utc_now()
    snapshot_id = snapshot["id"]
    conn.execute(
        "UPDATE ecosystems SET updated_at=?, snapshot_id=?, project_ids=?, metadata_json=? WHERE id=?",
        (
            now,
            snapshot_id,
            _json_dumps(snapshot["project_ids"]),
            _json_dumps({"analysis_persisted_at": now, "project_count": len(projects)}),
            ecosystem["id"],
        ),
    )
    conn.execute("DELETE FROM shared_capabilities WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM project_relationships WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM reuse_candidates WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM duplicate_findings WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM decision_conflicts WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM portfolio_risks WHERE portfolio_snapshot_id=?", (snapshot_id,))
    conn.execute("DELETE FROM ecosystem_attention WHERE portfolio_snapshot_id=?", (snapshot_id,))
    for shared in shared_capabilities:
        for implementation in shared["implementations"]:
            impl_id = f"shared-capability-{snapshot_id}-{shared['capability']}-{implementation['project_id']}"
            conn.execute(
                """
                INSERT OR REPLACE INTO shared_capabilities(
                    id, portfolio_snapshot_id, capability, project_id, implementation_json, confidence, created_at, metadata_json
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    impl_id,
                    snapshot_id,
                    shared["capability"],
                    implementation["project_id"],
                    _json_dumps(implementation),
                    implementation["confidence"],
                    now,
                    _json_dumps({"source": "deterministic-portfolio-analysis"}),
                ),
            )
    for relation in dependencies:
        conn.execute(
            """
            INSERT OR REPLACE INTO project_relationships(
                id, portfolio_snapshot_id, source_project_id, target_project_id, relationship_type, confidence, evidence_json, detector, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                relation["id"],
                snapshot_id,
                relation["source_project_id"],
                relation["target_project_id"],
                relation["relationship_type"],
                relation["confidence"],
                _json_dumps(relation["evidence"]),
                relation["detector"],
                relation["created_at"],
                _json_dumps({"source": "manifest"}),
            ),
        )
    for candidate in reuse_candidates:
        conn.execute(
            """
            INSERT OR REPLACE INTO reuse_candidates(
                id, portfolio_snapshot_id, source_project_id, capability, potential_target_projects_json, reason, coupling_evidence_json,
                dependencies_json, test_evidence, documentation, stability, confidence, risks_json, required_adaptation, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                candidate["candidate_id"],
                snapshot_id,
                candidate["source_project"],
                candidate["capability"],
                _json_dumps(candidate["potential_target_projects"]),
                candidate["reason"],
                _json_dumps(candidate["coupling_evidence"]),
                _json_dumps(candidate["dependencies"]),
                candidate["test_evidence"],
                candidate["documentation"],
                candidate["stability"],
                candidate["confidence"],
                _json_dumps(candidate["risks"]),
                candidate["required_adaptation"],
                now,
                _json_dumps({"source": "deterministic-portfolio-analysis"}),
            ),
        )
    for finding in duplicate_findings:
        conn.execute(
            """
            INSERT OR REPLACE INTO duplicate_findings(
                id, portfolio_snapshot_id, project_ids_json, capability, finding_type, reason, confidence, evidence_json, recommended_review, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                finding["id"],
                snapshot_id,
                _json_dumps(finding["project_ids"]),
                finding["capability"],
                finding["finding_type"],
                finding["reason"],
                finding["confidence"],
                _json_dumps(finding["evidence"]),
                finding["recommended_review"],
                now,
                _json_dumps({"source": "deterministic-portfolio-analysis"}),
            ),
        )
    for conflict in decision_conflicts:
        conn.execute(
            """
            INSERT OR REPLACE INTO decision_conflicts(
                id, portfolio_snapshot_id, project_a, decision_a, project_b, decision_b, conflict_type, reason, confidence, integration_relevance, evidence_json, recommended_review, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                conflict["id"],
                snapshot_id,
                conflict["project_a"],
                conflict["decision_a"],
                conflict["project_b"],
                conflict["decision_b"],
                conflict["conflict_type"],
                conflict["reason"],
                conflict["confidence"],
                conflict["integration_relevance"],
                _json_dumps(conflict["evidence"]),
                conflict["recommended_review"],
                now,
                _json_dumps({"source": "decision-comparison"}),
            ),
        )
    for risk in portfolio_risks:
        conn.execute(
            """
            INSERT OR REPLACE INTO portfolio_risks(
                id, portfolio_snapshot_id, title, category, severity, confidence, affected_projects_json, reason, recommended_investigation, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                risk["id"],
                snapshot_id,
                risk["title"],
                risk["category"],
                risk["severity"],
                risk["confidence"],
                _json_dumps(risk["affected_projects"]),
                risk["reason"],
                risk["recommended_investigation"],
                now,
                _json_dumps({"source": "deterministic-portfolio-analysis"}),
            ),
        )
    for item in attention_items:
        conn.execute(
            """
            INSERT OR REPLACE INTO ecosystem_attention(
                id, portfolio_snapshot_id, item_type, summary, confidence, recommended_action, created_at, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                item["id"],
                snapshot_id,
                item["type"],
                item["summary"],
                item["confidence"],
                item["recommended_action"],
                now,
                _json_dumps({"source": "deterministic-portfolio-analysis"}),
            ),
        )
    conn.commit()
    conn.close()


def analyse_portfolio(db_path: Path, project_ids: list[str] | None = None, *, name: str = "default") -> dict[str, Any]:
    registry = project_registry_v2(db_path)
    projects = registry["projects"]
    if project_ids:
        projects = [project for project in projects if project["project_id"] in set(project_ids)]
    projects = sorted(projects, key=lambda item: item["project_id"])
    snapshot_bundle = build_portfolio_snapshot(db_path, [project["project_id"] for project in projects], name=name)
    snapshot = snapshot_bundle["portfolio_snapshot"]
    ecosystem = snapshot_bundle["ecosystem"]
    technology_index = _technology_index(projects)
    project_capabilities = [capability for project in projects for capability in _project_capabilities(project)]
    shared_capabilities = _shared_capabilities(project_capabilities)
    reuse_candidates = _reuse_candidates(projects, shared_capabilities, technology_index)
    duplicate_findings = _duplicate_findings(projects, shared_capabilities, technology_index)
    dependencies = _dependency_relationships(projects)
    decision_conflicts = _decision_conflicts(projects)
    portfolio_risks = _portfolio_risks(projects, technology_index, shared_capabilities, dependencies)
    unknowns = _unknown_surface(projects)
    attention_items = _attention_items(shared_capabilities, reuse_candidates, portfolio_risks)
    health = _portfolio_health(projects, technology_index, shared_capabilities, portfolio_risks, unknowns, reuse_candidates)
    analysis = {
        "ecosystem": ecosystem,
        "portfolio_snapshot": snapshot,
        "projects": projects,
        "technology_portfolio": {
            "unique_technologies": len(technology_index),
            "technologies": list(technology_index.values()),
            "shared_technologies": [tech for tech in technology_index.values() if tech["shared"]],
        },
        "capability_matrix": {
            "project_capabilities": project_capabilities,
            "shared_capabilities": shared_capabilities,
        },
        "reuse_candidates": reuse_candidates,
        "duplicate_findings": duplicate_findings,
        "cross_project_dependencies": dependencies,
        "decision_conflicts": decision_conflicts,
        "portfolio_risks": portfolio_risks,
        "unknown_surface": unknowns,
        "attention": attention_items,
        "health": health,
    }
    _persist_analysis(
        db_path,
        ecosystem,
        snapshot,
        projects,
        technology_index,
        shared_capabilities,
        reuse_candidates,
        duplicate_findings,
        dependencies,
        decision_conflicts,
        portfolio_risks,
        attention_items,
    )
    return analysis


def ecosystem_timeline(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute("SELECT id, name, ecosystem_id, project_ids, source_fingerprint, created_at FROM portfolio_snapshots ORDER BY created_at, id").fetchall()
    conn.close()
    items = [
        {
            "snapshot_id": row["id"],
            "ecosystem_id": row["ecosystem_id"],
            "name": row["name"],
            "project_ids": _json_loads(row["project_ids"], []),
            "source_fingerprint": row["source_fingerprint"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {"count": len(items), "items": items}


def ecosystem_diff(db_path: Path, from_snapshot_id: str, to_snapshot_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    from_row = conn.execute("SELECT * FROM portfolio_snapshots WHERE id=?", (from_snapshot_id,)).fetchone()
    to_row = conn.execute("SELECT * FROM portfolio_snapshots WHERE id=?", (to_snapshot_id,)).fetchone()
    conn.close()
    if not from_row or not to_row:
        raise ValueError("Unknown portfolio snapshot")
    from_snapshot = _json_loads(from_row["snapshot_json"], {})
    to_snapshot = _json_loads(to_row["snapshot_json"], {})
    from_projects = {project["project_id"]: project for project in from_snapshot.get("projects", [])}
    to_projects = {project["project_id"]: project for project in to_snapshot.get("projects", [])}
    added = sorted(pid for pid in to_projects if pid not in from_projects)
    removed = sorted(pid for pid in from_projects if pid not in to_projects)
    changed = sorted(
        pid
        for pid in from_projects.keys() & to_projects.keys()
        if _snapshot_fingerprint(from_projects[pid]) != _snapshot_fingerprint(to_projects[pid])
    )
    return {
        "from_snapshot_id": from_snapshot_id,
        "to_snapshot_id": to_snapshot_id,
        "added_projects": added,
        "removed_projects": removed,
        "changed_projects": changed,
    }


def ecosystem_trace(db_path: Path, entity_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    relationships = conn.execute(
        """
        SELECT * FROM project_relationships
        WHERE source_project_id=? OR target_project_id=? OR relationship_type LIKE ?
        ORDER BY created_at, id
        """,
        (entity_id, entity_id, f"%{entity_id}%"),
    ).fetchall()
    snapshot_rows = conn.execute(
        "SELECT id, name, created_at FROM portfolio_snapshots ORDER BY created_at DESC, id DESC"
    ).fetchall()
    conn.close()
    return {
        "entity_id": entity_id,
        "relationships": [dict(row) for row in relationships],
        "recent_snapshots": [dict(row) for row in snapshot_rows[:10]],
    }


def render_ecosystem_report(analysis: dict[str, Any]) -> str:
    lines: list[str] = []
    ecosystem = analysis["ecosystem"]
    snapshot = analysis["portfolio_snapshot"]
    lines.append("# NEOS Ecosystem Report")
    lines.append("")
    lines.append(f"- Ecosystem: {ecosystem['name']} ({ecosystem['id']})")
    lines.append(f"- Snapshot: {snapshot['id']}")
    lines.append(f"- Projects: {len(analysis['projects'])}")
    lines.append(f"- Portfolio health: {analysis['health']['score']}")
    lines.append("")
    lines.append("## Registered Projects")
    for project in analysis["projects"]:
        lines.append(f"- {project['project_id']}: {project['display_name']} [{project['status']}]")
    lines.append("")
    lines.append("## Technology Landscape")
    for tech in analysis["technology_portfolio"]["technologies"]:
        shared = "shared" if tech["shared"] else "unique"
        lines.append(f"- {tech['technology']} ({shared}, projects: {', '.join(tech['projects'])})")
    lines.append("")
    lines.append("## Capability Matrix")
    for shared in analysis["capability_matrix"]["shared_capabilities"]:
        lines.append(f"- {shared['capability']}: {', '.join(shared['project_ids'])}")
    lines.append("")
    lines.append("## Reuse Opportunities")
    for item in analysis["reuse_candidates"]:
        lines.append(f"- {item['capability']} from {item['source_project']} -> {', '.join(item['potential_target_projects'])}")
    lines.append("")
    lines.append("## Potential Overlap")
    for item in analysis["duplicate_findings"]:
        lines.append(f"- {item['capability']} [{item['finding_type']}] in {', '.join(item['project_ids'])}")
    lines.append("")
    lines.append("## Cross-Project Dependencies")
    for item in analysis["cross_project_dependencies"]:
        lines.append(f"- {item['source_project_id']} -> {item['target_project_id']}")
    lines.append("")
    lines.append("## Decision Alignment")
    for item in analysis["decision_conflicts"]:
        lines.append(f"- {item['project_a']} vs {item['project_b']}: {item['conflict_type']}")
    lines.append("")
    lines.append("## Portfolio Risks")
    for item in analysis["portfolio_risks"]:
        lines.append(f"- {item['title']} [{item['severity']}]")
    lines.append("")
    lines.append("## Unknown Surface")
    for item in analysis["unknown_surface"]:
        lines.append(f"- {item['project_id']}: {', '.join(item['unknown_items'])}")
    lines.append("")
    lines.append("## Engineering Attention")
    for item in analysis["attention"]:
        lines.append(f"- {item['summary']}")
    return "\n".join(lines).strip() + "\n"


def search_ecosystem(db_path: Path, query: str, *, limit: int = 20, offset: int = 0, project_ids: list[str] | None = None) -> dict[str, Any]:
    analysis = analyse_portfolio(db_path, project_ids=project_ids)
    needle = query.strip().lower()
    if not needle:
        return {"query": query, "count": 0, "items": []}

    items: list[dict[str, Any]] = []

    def add(item_type: str, item_id: str, title: str, summary: str, *, project_ids: list[str] | None = None, source: str = "", metadata: dict[str, Any] | None = None) -> None:
        score = _search_score(
            needle,
            item_type,
            item_id,
            title,
            summary,
            project_ids or [],
            metadata or {},
        )
        if score <= 0:
            return
        items.append(
            {
                "type": item_type,
                "id": item_id,
                "title": title,
                "summary": summary,
                "project_ids": project_ids or [],
                "source": source,
                "score": score,
                "metadata": metadata or {},
            }
        )

    for project in analysis["projects"]:
        add(
            "project",
            project["project_id"],
            project["display_name"],
            project.get("summary", project["display_name"]),
            project_ids=[project["project_id"]],
            source="project_registry",
            metadata=project,
        )
        for feature in project.get("features", [])[:12]:
            add(
                "feature",
                feature.get("id", feature.get("name", "")),
                feature.get("name", feature.get("label", "Feature")),
                feature.get("description", ""),
                project_ids=[project["project_id"]],
                source="feature_inventory",
                metadata=feature,
            )
        for decision in project.get("decisions", [])[:12]:
            add(
                "decision",
                decision.get("id", decision.get("title", "")),
                decision.get("title", "Decision"),
                decision.get("decision", decision.get("rationale", "")),
                project_ids=[project["project_id"]],
                source="decision_inventory",
                metadata=decision,
            )
        for tech in project.get("technologies", [])[:12]:
            add(
                "technology",
                f"{project['project_id']}::{tech['name']}",
                tech["name"],
                tech.get("version", ""),
                project_ids=[project["project_id"]],
                source="technology_inventory",
                metadata=tech,
            )

    for shared in analysis["capability_matrix"]["shared_capabilities"]:
        add(
            "capability",
            shared["capability"],
            shared["capability"],
            shared.get("reason", ""),
            project_ids=shared.get("project_ids", []),
            source="capability_matrix",
            metadata=shared,
        )

    for candidate in analysis["reuse_candidates"]:
        add(
            "reuse",
            candidate["candidate_id"],
            candidate["capability"],
            candidate.get("reason", ""),
            project_ids=[candidate["source_project"], *candidate.get("potential_target_projects", [])],
            source="reuse_candidates",
            metadata=candidate,
        )

    for finding in analysis["duplicate_findings"]:
        add(
            "duplication",
            finding["id"],
            finding["capability"],
            finding.get("reason", ""),
            project_ids=finding.get("project_ids", []),
            source="duplicate_findings",
            metadata=finding,
        )

    for relation in analysis["cross_project_dependencies"]:
        add(
            "dependency",
            relation["id"],
            f"{relation['source_project_id']} -> {relation['target_project_id']}",
            relation.get("reason", ""),
            project_ids=[relation["source_project_id"], relation["target_project_id"]],
            source="cross_project_dependencies",
            metadata=relation,
        )

    for risk in analysis["portfolio_risks"]:
        add(
            "risk",
            risk["id"],
            risk["title"],
            risk.get("reason", ""),
            project_ids=risk.get("affected_projects", []),
            source="portfolio_risks",
            metadata=risk,
        )

    for item in analysis["attention"]:
        add(
            "attention",
            item["id"],
            item["summary"],
            item.get("recommended_action", ""),
            project_ids=item.get("project_ids", []),
            source="attention",
            metadata=item,
        )

    for item in analysis["unknown_surface"]:
        add(
            "unknown",
            item["id"],
            item["project_id"],
            ", ".join(item.get("unknown_items", [])),
            project_ids=[item["project_id"]],
            source="unknown_surface",
            metadata=item,
        )

    for item in analysis["technology_portfolio"]["technologies"]:
        add(
            "portfolio_technology",
            item["technology"],
            item["technology"],
            item.get("category", ""),
            project_ids=item.get("projects", []),
            source="technology_portfolio",
            metadata=item,
        )

    items.sort(key=lambda item: (-item["score"], item["type"], item["id"]))
    sliced = items[max(0, offset) : max(0, offset) + max(1, limit)]
    return {
        "query": query,
        "offset": offset,
        "limit": limit,
        "count": len(items),
        "items": sliced,
        "analysis_health": analysis["health"],
    }
