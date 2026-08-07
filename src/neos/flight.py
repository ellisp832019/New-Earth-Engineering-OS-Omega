from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .genome import build_project_genome, genome_summary
from .memory import latest_project_memory, memory_summary, memory_timeline

FLIGHT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FlightSnapshot:
    id: str
    project_id: str
    source_commit: str | None
    source_branch: str | None
    scan_id: str
    genome_snapshot_id: str | None
    memory_snapshot_id: str | None
    timestamp: str
    schema_version: int
    repository_state_hash: str
    semantic_state_hash: str
    genome_hash: str
    memory_hash: str
    feature_state_hash: str
    test_state_hash: str
    api_state_hash: str
    configuration_state_hash: str
    risk_state_hash: str
    unknown_state_hash: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FlightEvent:
    id: str
    project_id: str
    timestamp: str
    event_type: str
    source_snapshot: str
    target_snapshot: str
    affected_entities: list[str]
    evidence: list[str]
    confidence: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FlightTransition:
    id: str
    project_id: str
    source_snapshot: str
    target_snapshot: str
    timestamp: str
    before: dict[str, Any]
    after: dict[str, Any]
    changed: dict[str, Any]
    unchanged: dict[str, Any]
    possible_causes: list[dict[str, Any]]
    related_decisions: list[dict[str, Any]]
    related_commits: list[dict[str, Any]]
    related_experiments: list[dict[str, Any]]
    related_risks: list[dict[str, Any]]
    confidence: float
    unknowns: list[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FlightIncident:
    id: str
    project_id: str
    timestamp: str
    severity: str
    type: str
    summary: str
    source: str
    affected_entities: list[str]
    evidence: list[str]
    resolved_at: str | None
    resolution: str | None
    related_decisions: list[str]
    related_commits: list[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FlightCheckpoint:
    id: str
    project_id: str
    checkpoint_type: str
    label: str
    source_ref: str | None
    source_commit: str | None
    source_branch: str | None
    scan_id: str | None
    genome_id: str | None
    memory_id: str | None
    snapshot_id: str
    timestamp: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FlightRegressionIndicator:
    id: str
    project_id: str
    timestamp: str
    indicator_type: str
    severity: str
    confidence: float
    source_snapshot: str
    target_snapshot: str
    summary: str
    evidence: list[str]
    affected_entities: list[str]
    metadata: dict[str, Any]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return f"{prefix}-" + hashlib.sha256(payload).hexdigest()[:24]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _state_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _json_loads(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


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


def _latest_genome_row(conn, project_id: str, scan_id: str | None = None):
    if scan_id:
        row = conn.execute(
            "SELECT * FROM project_genomes WHERE project_id=? AND scan_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (project_id, scan_id),
        ).fetchone()
        if row:
            return row
    return conn.execute(
        "SELECT * FROM project_genomes WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _latest_memory_row(conn, project_id: str, scan_id: str | None = None, genome_id: str | None = None):
    clauses = ["project_id=?"]
    params: list[Any] = [project_id]
    if scan_id:
        clauses.append("scan_id=?")
        params.append(scan_id)
    if genome_id:
        clauses.append("genome_id=?")
        params.append(genome_id)
    query = f"SELECT * FROM memory_snapshots WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC LIMIT 1"
    row = conn.execute(query, tuple(params)).fetchone()
    if row:
        return row
    return conn.execute(
        "SELECT * FROM memory_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _scan_rows(conn, scan_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT source_path, kind, label, content_hash, metadata_json
        FROM scan_observations
        WHERE scan_id=?
        ORDER BY source_path, kind, label
        """,
        (scan_id,),
    ).fetchall()
    return [
        {
            "source_path": row["source_path"],
            "kind": row["kind"],
            "label": row["label"],
            "content_hash": row["content_hash"],
            "metadata": _json_loads(row["metadata_json"], {}),
        }
        for row in rows
    ]


def _project_repo_state(conn, project_id: str, scan_row) -> dict[str, Any]:
    scan_snapshot = _json_loads(scan_row["snapshot_json"], {}) if scan_row else {}
    return {
        "project_id": project_id,
        "scan_id": scan_row["scan_id"] if scan_row else None,
        "commit": scan_row["git_commit"] if scan_row else None,
        "branch": scan_row["git_branch"] if scan_row else None,
        "repo_head": scan_row["repo_head"] if scan_row else None,
        "file_count": scan_row["file_count"] if scan_row else 0,
        "scan_fingerprint": scan_snapshot.get("fingerprint"),
    }


def _semantic_state(conn, project_id: str, scan_id: str, genome: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    def _select(query: str, fields: list[str], params: tuple[Any, ...]) -> list[dict[str, Any]]:
        rows = conn.execute(query, params).fetchall()
        return [{field: row[field] for field in fields if field in row} for row in rows]

    files = _scan_rows(conn, scan_id)
    symbols = _select(
        """
        SELECT id, name, kind, status, source_path, content_hash, provenance
        FROM symbols
        WHERE project_id=? AND scan_id=?
        ORDER BY kind, name, id
        """,
        ["id", "name", "kind", "status", "source_path", "content_hash", "provenance"],
        (project_id, scan_id),
    )
    features = _select(
        """
        SELECT id, name, description, status, source, provenance, introduced_version, removed_version, confidence
        FROM features
        WHERE project_id=? AND scan_id=?
        ORDER BY name, id
        """,
        ["id", "name", "description", "status", "source", "provenance", "introduced_version", "removed_version", "confidence"],
        (project_id, scan_id),
    )
    tests = _select(
        """
        SELECT source_path AS id, label, source_path, content_hash, metadata_json
        FROM scan_observations
        WHERE project_id=? AND scan_id=? AND kind='test'
        ORDER BY source_path, label
        """,
        ["id", "label", "source_path", "content_hash", "metadata_json"],
        (project_id, scan_id),
    )
    apis = _select(
        """
        SELECT id, method, route, handler, source_path, confidence, provenance
        FROM api_endpoints
        WHERE project_id=? AND scan_id=?
        ORDER BY route, method, id
        """,
        ["id", "method", "route", "handler", "source_path", "confidence", "provenance"],
        (project_id, scan_id),
    )
    configuration = _select(
        """
        SELECT id, key, section, value_type, source_path, confidence, provenance
        FROM configuration_keys
        WHERE project_id=? AND scan_id=?
        ORDER BY key, section, id
        """,
        ["id", "key", "section", "value_type", "source_path", "confidence", "provenance"],
        (project_id, scan_id),
    )
    decisions = _select(
        """
        SELECT id, title, status, date, source_path, confidence, provenance
        FROM engineering_decisions
        WHERE project_id=? AND scan_id=?
        ORDER BY COALESCE(date, created_at), title, id
        """,
        ["id", "title", "status", "date", "source_path", "confidence", "provenance"],
        (project_id, scan_id),
    )
    dependencies = _select(
        """
        SELECT id, source_entity_id, target_entity_id, dependency_type, confidence, evidence_source
        FROM dependencies
        WHERE project_id=? AND scan_id=?
        ORDER BY dependency_type, source_entity_id, target_entity_id, id
        """,
        ["id", "source_entity_id", "target_entity_id", "dependency_type", "confidence", "evidence_source"],
        (project_id, scan_id),
    )
    return {
        "files": files,
        "symbols": symbols,
        "features": features,
        "tests": tests,
        "apis": apis,
        "configuration": configuration,
        "decisions": decisions,
        "dependencies": dependencies,
        "risks": genome.get("risks", []),
        "unknowns": genome.get("unknowns", []),
        "health": genome.get("project_health", {}),
        "maturity": genome.get("maturity", {}),
        "memory_summary": memory_summary(memory) if memory else {},
        "genome_summary": genome_summary(genome) if genome else {},
    }


def _semantic_hashes(state: dict[str, Any]) -> dict[str, str]:
    return {
        "feature_state_hash": _state_hash(state.get("features", [])),
        "test_state_hash": _state_hash(state.get("tests", [])),
        "api_state_hash": _state_hash(state.get("apis", [])),
        "configuration_state_hash": _state_hash(state.get("configuration", [])),
        "risk_state_hash": _state_hash(state.get("risks", [])),
        "unknown_state_hash": _state_hash(state.get("unknowns", [])),
    }


def _scan_commit_history(repo: Path, limit: int = 25) -> list[dict[str, Any]]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo), "log", f"-{limit}", "--date=iso-strict", "--format=%H%x1f%ad%x1f%s"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return []
    items: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        commit, date, subject = parts
        items.append(
            {
                "id": f"commit-{commit[:12]}",
                "kind": "commit",
                "timestamp": date,
                "summary": subject,
                "commit": commit,
            }
        )
    return items


def _snapshot_payload(
    conn,
    project_id: str,
    ref: str | None = None,
    *,
    scan_row=None,
    genome_row=None,
    memory_row=None,
) -> dict[str, Any]:
    project = _project_row(conn, project_id)
    if scan_row is None:
        scan_row = _latest_scan_row(conn, project_id)
    if not scan_row:
        raise ValueError(f"No scans available for project: {project_id}")
    if genome_row is None:
        genome_row = _latest_genome_row(conn, project_id, scan_row["scan_id"])
    if genome_row is None:
        raise ValueError(f"No genome snapshot available for project: {project_id}")
    genome = _json_loads(genome_row["genome_json"], {}) if genome_row else {}
    if memory_row is None:
        memory_row = _latest_memory_row(conn, project_id, scan_row["scan_id"], genome_row["id"] if genome_row else None)
    memory = _json_loads(memory_row["memory_json"], {}) if memory_row else {}
    repo = Path(project["repo_path"])
    repo_state = _project_repo_state(conn, project_id, scan_row)
    semantic = _semantic_state(conn, project_id, scan_row["scan_id"], genome, memory)
    hashes = {
        "repository_state_hash": _state_hash(repo_state),
        "semantic_state_hash": _state_hash(semantic),
        "genome_hash": _state_hash(genome),
        "memory_hash": _state_hash(memory),
        **_semantic_hashes(semantic),
    }
    source_commit = repo_state["commit"]
    source_branch = repo_state["branch"]
    source_ref = ref or source_commit or scan_row["scan_id"]
    related_commits = _scan_commit_history(repo)
    state = {
        "repository": repo_state,
        "semantic": semantic,
        "genome": genome_summary(genome) if genome else {},
        "memory": memory_summary(memory) if memory else {},
        "related_commits": related_commits,
        "health": genome.get("project_health", {}),
        "maturity": genome.get("maturity", {}),
    }
    summary = {
        "files": len(semantic.get("files", [])),
        "features": len(semantic.get("features", [])),
        "tests": len(semantic.get("tests", [])),
        "apis": len(semantic.get("apis", [])),
        "configuration": len(semantic.get("configuration", [])),
        "decisions": len(semantic.get("decisions", [])),
        "dependencies": len(semantic.get("dependencies", [])),
        "risks": len(semantic.get("risks", [])),
        "unknowns": len(semantic.get("unknowns", [])),
    }
    snapshot = FlightSnapshot(
        id=_stable_id(
            "flight_snapshot",
            project_id,
            source_ref,
            scan_row["scan_id"],
            genome_row["id"] if genome_row else None,
            memory_row["id"] if memory_row else None,
            hashes["repository_state_hash"],
            hashes["semantic_state_hash"],
            hashes["genome_hash"],
            hashes["memory_hash"],
            FLIGHT_SCHEMA_VERSION,
        ),
        project_id=project_id,
        source_commit=source_commit,
        source_branch=source_branch,
        scan_id=scan_row["scan_id"],
        genome_snapshot_id=genome_row["id"] if genome_row else None,
        memory_snapshot_id=memory_row["id"] if memory_row else None,
        timestamp=genome.get("generated_at") or scan_row["created_at"] or utc_now(),
        schema_version=FLIGHT_SCHEMA_VERSION,
        repository_state_hash=hashes["repository_state_hash"],
        semantic_state_hash=hashes["semantic_state_hash"],
        genome_hash=hashes["genome_hash"],
        memory_hash=hashes["memory_hash"],
        feature_state_hash=hashes["feature_state_hash"],
        test_state_hash=hashes["test_state_hash"],
        api_state_hash=hashes["api_state_hash"],
        configuration_state_hash=hashes["configuration_state_hash"],
        risk_state_hash=hashes["risk_state_hash"],
        unknown_state_hash=hashes["unknown_state_hash"],
        metadata={
            "source_ref": source_ref,
            "scan_fingerprint": repo_state.get("scan_fingerprint"),
            "genome_summary": genome_summary(genome) if genome else {},
            "memory_summary": memory_summary(memory) if memory else {},
        },
    )
    payload = {
        "snapshot": asdict(snapshot),
        "summary": summary,
        "state": state,
        "hashes": hashes,
    }
    payload["snapshot"]["metadata"] = snapshot.metadata
    payload["snapshot"]["state"] = state
    return payload


def _snapshot_row_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    snapshot = payload["snapshot"]
    return {
        "id": snapshot["id"],
        "project_id": snapshot["project_id"],
        "scan_id": snapshot["scan_id"],
        "genome_id": snapshot["genome_snapshot_id"],
        "memory_id": snapshot["memory_snapshot_id"],
        "source_commit": snapshot["source_commit"],
        "source_branch": snapshot["source_branch"],
        "source_ref": snapshot["metadata"].get("source_ref"),
        "flight_schema_version": snapshot["schema_version"],
        "source_fingerprint": _stable_id(
            "flight_fp",
            snapshot["project_id"],
            snapshot["scan_id"],
            snapshot["genome_snapshot_id"],
            snapshot["memory_snapshot_id"],
            snapshot["repository_state_hash"],
            snapshot["semantic_state_hash"],
            snapshot["genome_hash"],
            snapshot["memory_hash"],
            snapshot["feature_state_hash"],
            snapshot["test_state_hash"],
            snapshot["api_state_hash"],
            snapshot["configuration_state_hash"],
            snapshot["risk_state_hash"],
            snapshot["unknown_state_hash"],
            snapshot["schema_version"],
        ),
        "repository_state_hash": snapshot["repository_state_hash"],
        "semantic_state_hash": snapshot["semantic_state_hash"],
        "genome_state_hash": snapshot["genome_hash"],
        "memory_state_hash": snapshot["memory_hash"],
        "feature_state_hash": snapshot["feature_state_hash"],
        "test_state_hash": snapshot["test_state_hash"],
        "api_state_hash": snapshot["api_state_hash"],
        "configuration_state_hash": snapshot["configuration_state_hash"],
        "risk_state_hash": snapshot["risk_state_hash"],
        "unknown_state_hash": snapshot["unknown_state_hash"],
        "created_at": snapshot["timestamp"],
        "summary_json": _canonical_json(payload["summary"]),
        "state_json": _canonical_json(payload["state"]),
        "metadata_json": _canonical_json(snapshot["metadata"]),
    }


def _event_rows(before: dict[str, Any], after: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    before_snapshot = before.get("snapshot", before)
    after_snapshot = after.get("snapshot", after)
    before_semantic = before.get("state", {}).get("semantic", {})
    after_semantic = after.get("state", {}).get("semantic", {})
    before_genome = before.get("state", {}).get("genome", {})
    after_genome = after.get("state", {}).get("genome", {})

    def _diff(before_items: list[dict[str, Any]], after_items: list[dict[str, Any]], key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        before_map = {str(item.get(key)): item for item in before_items}
        after_map = {str(item.get(key)): item for item in after_items}
        added = [after_map[item] for item in sorted(set(after_map) - set(before_map))]
        removed = [before_map[item] for item in sorted(set(before_map) - set(after_map))]
        changed = [
            {"before": before_map[item], "after": after_map[item]}
            for item in sorted(set(before_map) & set(after_map))
            if _canonical_json(before_map[item]) != _canonical_json(after_map[item])
        ]
        return added, removed, changed

    feature_added, feature_removed, feature_changed = _diff(
        before_semantic.get("features", []), after_semantic.get("features", []), "id"
    )
    test_added, test_removed, _ = _diff(before_semantic.get("tests", []), after_semantic.get("tests", []), "id")
    api_added, api_removed, _ = _diff(before_semantic.get("apis", []), after_semantic.get("apis", []), "id")
    config_added, config_removed, config_changed = _diff(
        before_semantic.get("configuration", []), after_semantic.get("configuration", []), "id"
    )
    dep_added, dep_removed, _ = _diff(before_semantic.get("dependencies", []), after_semantic.get("dependencies", []), "id")
    decision_added, _decision_removed, decision_changed = _diff(before_semantic.get("decisions", []), after_semantic.get("decisions", []), "id")

    def _append(event_type: str, items: list[dict[str, Any]], evidence: list[str], confidence: float) -> None:
        if not items:
            return
        events.append(
            {
                "id": _stable_id("flight_event", project_id, before_snapshot["id"], after_snapshot["id"], event_type),
                "project_id": project_id,
                "timestamp": after_snapshot["created_at"],
                "event_type": event_type,
                "source_snapshot": before_snapshot["id"],
                "target_snapshot": after_snapshot["id"],
                "affected_entities": [str(item.get("id") or item.get("route") or item.get("key") or item.get("source_path")) for item in items],
                "evidence": evidence,
                "confidence": confidence,
                "metadata": {"count": len(items)},
            }
        )

    _append("feature_added", feature_added, [item.get("source", "") for item in feature_added if item.get("source")], 0.9)
    _append("feature_removed", feature_removed, [item.get("source", "") for item in feature_removed if item.get("source")], 0.9)
    if feature_changed:
        _append("feature_status_changed", [item["after"] for item in feature_changed], [item["after"].get("source", "") for item in feature_changed], 0.78)
    _append("test_added", test_added, [item.get("source_path", "") for item in test_added if item.get("source_path")], 0.88)
    _append("test_removed", test_removed, [item.get("source_path", "") for item in test_removed if item.get("source_path")], 0.88)
    _append("api_added", api_added, [item.get("source_path", "") for item in api_added if item.get("source_path")], 0.86)
    _append("api_removed", api_removed, [item.get("source_path", "") for item in api_removed if item.get("source_path")], 0.86)
    _append("config_changed", config_added + config_removed + [item["after"] for item in config_changed], [item.get("source_path", "") for item in config_added + config_removed], 0.8)
    _append("dependency_added", dep_added, [item.get("evidence_source", "") for item in dep_added if item.get("evidence_source")], 0.82)
    _append("dependency_removed", dep_removed, [item.get("evidence_source", "") for item in dep_removed if item.get("evidence_source")], 0.82)
    _append("decision_added", decision_added, [item.get("source_path", "") for item in decision_added if item.get("source_path")], 0.9)
    if decision_changed:
        _append("decision_superseded", [item["after"] for item in decision_changed], [item["after"].get("source_path", "") for item in decision_changed], 0.74)

    before_maturity = before_genome.get("score", before_genome.get("maturity", {}).get("score"))
    after_maturity = after_genome.get("score", after_genome.get("maturity", {}).get("score"))
    if before_maturity != after_maturity:
        events.append(
                {
                    "id": _stable_id("flight_event", project_id, before_snapshot["id"], after_snapshot["id"], "maturity_changed"),
                    "project_id": project_id,
                    "timestamp": after_snapshot["created_at"],
                    "event_type": "maturity_changed",
                    "source_snapshot": before_snapshot["id"],
                    "target_snapshot": after_snapshot["id"],
                    "affected_entities": ["maturity"],
                    "evidence": [after_snapshot["id"]],
                    "confidence": 0.95,
                    "metadata": {"before": before_maturity, "after": after_maturity},
                }
            )
    return events


def _regression_indicators(before: dict[str, Any], after: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
    indicators: list[dict[str, Any]] = []
    before_snapshot = before.get("snapshot", before)
    after_snapshot = after.get("snapshot", after)
    before_semantic = before.get("state", {}).get("semantic", {})
    after_semantic = after.get("state", {}).get("semantic", {})
    before_genome = before.get("state", {}).get("genome", {})
    after_genome = after.get("state", {}).get("genome", {})

    def _add(indicator_type: str, severity: str, summary: str, evidence: list[str], affected: list[str], confidence: float) -> None:
        indicators.append(
            {
                "id": _stable_id("flight_regression", project_id, before_snapshot["id"], after_snapshot["id"], indicator_type),
                "project_id": project_id,
                "timestamp": after_snapshot["created_at"],
                "indicator_type": indicator_type,
                "severity": severity,
                "confidence": confidence,
                "source_snapshot": before_snapshot["id"],
                "target_snapshot": after_snapshot["id"],
                "summary": summary,
                "evidence": evidence,
                "affected_entities": affected,
                "metadata": {},
            }
        )

    before_tests = len(before_semantic.get("tests", []))
    after_tests = len(after_semantic.get("tests", []))
    if after_tests < before_tests:
        _add("test_count_decreased", "medium", "Test count decreased between snapshots.", [before_snapshot["id"], after_snapshot["id"]], ["tests"], 0.92)
    if len(after_semantic.get("apis", [])) < len(before_semantic.get("apis", [])):
        _add("api_removed", "high", "API surface shrank between snapshots.", [before_snapshot["id"], after_snapshot["id"]], ["apis"], 0.9)
    before_unknowns = len(before_semantic.get("unknowns", []))
    after_unknowns = len(after_semantic.get("unknowns", []))
    if after_unknowns > before_unknowns:
        _add("unknowns_increased", "medium", "Known unknowns increased.", [before_snapshot["id"], after_snapshot["id"]], ["unknowns"], 0.8)
    before_risks = len(before_semantic.get("risks", []))
    after_risks = len(after_semantic.get("risks", []))
    if after_risks > before_risks:
        _add("risk_count_increased", "medium", "Risk count increased.", [before_snapshot["id"], after_snapshot["id"]], ["risks"], 0.78)
    before_maturity = before_genome.get("score", before_genome.get("maturity", {}).get("score", 0))
    after_maturity = after_genome.get("score", after_genome.get("maturity", {}).get("score", 0))
    if after_maturity < before_maturity:
        _add("maturity_decreased", "high", "Project maturity decreased.", [before_snapshot["id"], after_snapshot["id"]], ["maturity"], 0.95)
    return indicators


def _incident_rows(regressions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []
    for regression in regressions:
        severity = "high" if regression["severity"] == "high" or regression["indicator_type"] in {"api_removed", "maturity_decreased"} else "medium"
        incidents.append(
            {
                "id": _stable_id("flight_incident", regression["id"]),
                "project_id": regression["project_id"],
                "timestamp": regression["timestamp"],
                "severity": severity,
                "type": regression["indicator_type"],
                "summary": regression["summary"],
                "source": "regression-indicator",
                "affected_entities": regression["affected_entities"],
                "evidence": regression["evidence"],
                "resolved_at": None,
                "resolution": None,
                "related_decisions": [],
                "related_commits": [],
                "metadata": {"regression_id": regression["id"]},
            }
        )
    return incidents


def _store_if_missing(conn, table: str, row: dict[str, Any]) -> None:
    columns = [key for key in row if key in {item["name"] for item in conn.execute(f"PRAGMA table_info({table})")}]
    values = [row[column] for column in columns]
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join(columns)
    conn.execute(f"INSERT OR IGNORE INTO {table} ({column_list}) VALUES ({placeholders})", values)


def _load_snapshot_row(row) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "scan_id": row["scan_id"],
        "genome_id": row["genome_id"],
        "memory_id": row["memory_id"],
        "source_commit": row["source_commit"],
        "source_branch": row["source_branch"],
        "source_ref": row["source_ref"],
        "flight_schema_version": row["flight_schema_version"],
        "source_fingerprint": row["source_fingerprint"],
        "repository_state_hash": row["repository_state_hash"],
        "semantic_state_hash": row["semantic_state_hash"],
        "genome_state_hash": row["genome_state_hash"],
        "memory_state_hash": row["memory_state_hash"],
        "feature_state_hash": row["feature_state_hash"],
        "test_state_hash": row["test_state_hash"],
        "api_state_hash": row["api_state_hash"],
        "configuration_state_hash": row["configuration_state_hash"],
        "risk_state_hash": row["risk_state_hash"],
        "unknown_state_hash": row["unknown_state_hash"],
        "created_at": row["created_at"],
        "summary": _json_loads(row["summary_json"], {}),
        "state": _json_loads(row["state_json"], {}),
        "metadata": _json_loads(row["metadata_json"], {}),
    }


def _latest_flight_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM flight_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def build_project_flight(db_path: Path, project_id: str, ref: str | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    _project_row(conn, project_id)
    scan = _latest_scan_row(conn, project_id)
    if not scan:
        conn.close()
        raise ValueError(f"No scans available for project: {project_id}")
    genome_row = _latest_genome_row(conn, project_id, scan["scan_id"])
    if genome_row is None:
        conn.close()
        build_project_genome(db_path, project_id)
        conn = connect(db_path)
        scan = _latest_scan_row(conn, project_id)
        genome_row = _latest_genome_row(conn, project_id, scan["scan_id"])
    memory_row = _latest_memory_row(conn, project_id, scan["scan_id"], genome_row["id"] if genome_row else None)
    if memory_row is None:
        conn.close()
        from .memory import build_project_memory

        build_project_memory(db_path, project_id)
        conn = connect(db_path)
        scan = _latest_scan_row(conn, project_id)
        genome_row = _latest_genome_row(conn, project_id, scan["scan_id"])
        memory_row = _latest_memory_row(conn, project_id, scan["scan_id"], genome_row["id"] if genome_row else None)

    payload = _snapshot_payload(conn, project_id, ref, scan_row=scan, genome_row=genome_row, memory_row=memory_row)
    source_fingerprint = _stable_id(
        "flight_fp",
        payload["snapshot"]["project_id"],
        payload["snapshot"]["source_commit"],
        payload["snapshot"]["source_branch"],
        payload["snapshot"]["scan_id"],
        payload["snapshot"]["genome_snapshot_id"],
        payload["snapshot"]["memory_snapshot_id"],
        payload["snapshot"]["repository_state_hash"],
        payload["snapshot"]["semantic_state_hash"],
        payload["snapshot"]["genome_hash"],
        payload["snapshot"]["memory_hash"],
        payload["snapshot"]["feature_state_hash"],
        payload["snapshot"]["test_state_hash"],
        payload["snapshot"]["api_state_hash"],
        payload["snapshot"]["configuration_state_hash"],
        payload["snapshot"]["risk_state_hash"],
        payload["snapshot"]["unknown_state_hash"],
        payload["snapshot"]["schema_version"],
    )
    existing = conn.execute(
        """
        SELECT *
        FROM flight_snapshots
        WHERE project_id=? AND flight_schema_version=? AND source_fingerprint=?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (project_id, FLIGHT_SCHEMA_VERSION, source_fingerprint),
    ).fetchone()
    if existing:
        snapshot = _load_snapshot_row(existing)
        conn.close()
        return {"snapshot": snapshot, "stored": False, "snapshot_row": dict(existing)}

    snapshot_row = _snapshot_row_from_payload(payload)
    snapshot_row["source_fingerprint"] = source_fingerprint
    _store_if_missing(conn, "flight_snapshots", snapshot_row)
    conn.commit()

    stored_snapshot = conn.execute("SELECT * FROM flight_snapshots WHERE id=?", (payload["snapshot"]["id"],)).fetchone()
    snapshot = _load_snapshot_row(stored_snapshot)
    previous = conn.execute(
        """
        SELECT * FROM flight_snapshots
        WHERE project_id=? AND created_at < ? AND id != ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (project_id, snapshot["created_at"], snapshot["id"]),
    ).fetchone()
    if previous:
        before = _load_snapshot_row(previous)
        events = _event_rows(before, {"snapshot": snapshot, "state": snapshot["state"]}, project_id)
        transitions = {
            "id": _stable_id("flight_transition", project_id, before["id"], snapshot["id"]),
            "project_id": project_id,
            "source_snapshot": before["id"],
            "target_snapshot": snapshot["id"],
            "timestamp": snapshot["created_at"],
            "confidence": 0.88,
            "summary_json": _canonical_json({"before": before["summary"], "after": snapshot["summary"]}),
            "transition_json": _canonical_json(
                {
                    "before": before,
                    "after": snapshot,
                    "events": events,
                    "regressions": _regression_indicators(before, {"snapshot": snapshot, "state": snapshot["state"]}, project_id),
                }
            ),
            "created_at": utc_now(),
            "metadata_json": _canonical_json({"source": "deterministic-transition-engine"}),
        }
        _store_if_missing(conn, "flight_transitions", transitions)
        for event in events:
            event_row = {
                "id": event["id"],
                "project_id": event["project_id"],
                "timestamp": event["timestamp"],
                "event_type": event["event_type"],
                "source_snapshot": event["source_snapshot"],
                "target_snapshot": event["target_snapshot"],
                "affected_entities_json": _canonical_json(event["affected_entities"]),
                "evidence_json": _canonical_json(event["evidence"]),
                "confidence": event["confidence"],
                "created_at": utc_now(),
                "metadata_json": _canonical_json(event["metadata"]),
            }
            _store_if_missing(conn, "flight_events", event_row)
        regressions = _regression_indicators(before, {"snapshot": snapshot, "state": snapshot["state"]}, project_id)
        for regression in regressions:
            reg_row = {
                "id": regression["id"],
                "project_id": regression["project_id"],
                "timestamp": regression["timestamp"],
                "indicator_type": regression["indicator_type"],
                "severity": regression["severity"],
                "confidence": regression["confidence"],
                "source_snapshot": regression["source_snapshot"],
                "target_snapshot": regression["target_snapshot"],
                "summary": regression["summary"],
                "evidence_json": _canonical_json(regression["evidence"]),
                "affected_entities_json": _canonical_json(regression["affected_entities"]),
                "created_at": utc_now(),
                "metadata_json": _canonical_json(regression["metadata"]),
            }
            _store_if_missing(conn, "flight_regressions", reg_row)
        incidents = _incident_rows(regressions)
        for incident in incidents:
            incident_row = {
                "id": incident["id"],
                "project_id": incident["project_id"],
                "timestamp": incident["timestamp"],
                "severity": incident["severity"],
                "type": incident["type"],
                "summary": incident["summary"],
                "source": incident["source"],
                "affected_entities_json": _canonical_json(incident["affected_entities"]),
                "evidence_json": _canonical_json(incident["evidence"]),
                "resolved_at": incident["resolved_at"],
                "resolution": incident["resolution"],
                "related_decisions_json": _canonical_json(incident["related_decisions"]),
                "related_commits_json": _canonical_json(incident["related_commits"]),
                "created_at": utc_now(),
                "metadata_json": _canonical_json(incident["metadata"]),
            }
            _store_if_missing(conn, "flight_incidents", incident_row)
        conn.commit()
    conn.close()
    return {"snapshot": snapshot, "stored": True, "snapshot_row": snapshot_row, "metadata": snapshot["metadata"]}


def _state_from_ref(db_path: Path, project_id: str, ref: str | None) -> dict[str, Any]:
    conn = connect(db_path)
    if not ref or ref == "latest":
        row = _latest_flight_row(conn, project_id)
        if row:
            snapshot = _load_snapshot_row(row)
            conn.close()
            return {"snapshot": snapshot, "reconstructed": True, "unknowns": []}
        conn.close()
        return build_project_flight(db_path, project_id)

    snapshot_row = conn.execute("SELECT * FROM flight_snapshots WHERE id=?", (ref,)).fetchone()
    if snapshot_row:
        snapshot = _load_snapshot_row(snapshot_row)
        conn.close()
        return {"snapshot": snapshot, "reconstructed": True, "unknowns": []}

    scan_row = conn.execute(
        "SELECT * FROM scans WHERE project_id=? AND (git_commit=? OR repo_head=?) ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id, ref, ref),
    ).fetchone()
    if scan_row:
        genome_row = _latest_genome_row(conn, project_id, scan_row["scan_id"])
        memory_row = _latest_memory_row(conn, project_id, scan_row["scan_id"], genome_row["id"] if genome_row else None)
        if genome_row and memory_row:
            payload = _snapshot_payload(conn, project_id, ref, scan_row=scan_row, genome_row=genome_row, memory_row=memory_row)
            conn.close()
            return {"snapshot": payload["snapshot"], "reconstructed": True, "unknowns": []}
    latest = _latest_flight_row(conn, project_id)
    conn.close()
    if latest:
        snapshot = _load_snapshot_row(latest)
        snapshot["metadata"] = {**snapshot.get("metadata", {}), "reconstructed_from": ref, "reconstruction_incomplete": True}
        return {"snapshot": snapshot, "reconstructed": False, "unknowns": [f"No exact historical snapshot for {ref}."]}
    return {"snapshot": build_project_flight(db_path, project_id)["snapshot"], "reconstructed": False, "unknowns": [f"No flight snapshot available for {ref}."]}


def latest_project_flight(db_path: Path, project_id: str) -> dict[str, Any]:
    return _state_from_ref(db_path, project_id, "latest")["snapshot"]


def flight_show_snapshot(db_path: Path, snapshot_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = conn.execute("SELECT * FROM flight_snapshots WHERE id=?", (snapshot_id,)).fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Unknown flight snapshot: {snapshot_id}")
    snapshot = _load_snapshot_row(row)
    return {"snapshot": snapshot, "project_id": snapshot["project_id"]}


def flight_snapshots(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    items = [_load_snapshot_row(row) for row in rows]
    return {"project_id": project_id, "count": len(items), "items": items}


def flight_checkpoints(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_checkpoints WHERE project_id=? ORDER BY timestamp DESC, id DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    items = [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "checkpoint_type": row["checkpoint_type"],
            "label": row["label"],
            "source_ref": row["source_ref"],
            "source_commit": row["source_commit"],
            "source_branch": row["source_branch"],
            "scan_id": row["scan_id"],
            "genome_id": row["genome_id"],
            "memory_id": row["memory_id"],
            "snapshot_id": row["snapshot_id"],
            "timestamp": row["timestamp"],
            "created_at": row["created_at"],
            "metadata": _json_loads(row["metadata_json"], {}),
        }
        for row in rows
    ]
    return {"project_id": project_id, "count": len(items), "items": items}


def create_flight_checkpoint(
    db_path: Path,
    project_id: str,
    *,
    checkpoint_type: str = "manual",
    label: str | None = None,
    source_ref: str | None = None,
) -> dict[str, Any]:
    state = _state_from_ref(db_path, project_id, source_ref or "latest")
    snapshot = state["snapshot"]
    conn = connect(db_path)
    row = {
        "id": _stable_id("flight_checkpoint", project_id, checkpoint_type, label or checkpoint_type, snapshot["id"], source_ref or snapshot["source_commit"]),
        "project_id": project_id,
        "checkpoint_type": checkpoint_type,
        "label": label or checkpoint_type,
        "source_ref": source_ref or snapshot["metadata"].get("source_ref"),
        "source_commit": snapshot.get("source_commit"),
        "source_branch": snapshot.get("source_branch"),
        "scan_id": snapshot.get("scan_id"),
        "genome_id": snapshot.get("genome_id"),
        "memory_id": snapshot.get("memory_id"),
        "snapshot_id": snapshot["id"],
        "timestamp": snapshot.get("created_at") or utc_now(),
        "created_at": utc_now(),
        "metadata_json": _canonical_json({"source": "neos flight checkpoint create"}),
    }
    _store_if_missing(conn, "flight_checkpoints", row)
    conn.commit()
    conn.close()
    return {"project_id": project_id, "checkpoint": {**row, "metadata": _json_loads(row["metadata_json"], {})}, "snapshot": snapshot}


def flight_state(db_path: Path, project_id: str, at: str | None = None) -> dict[str, Any]:
    state = _state_from_ref(db_path, project_id, at or "latest")
    snapshot = state["snapshot"]
    return {
        "project_id": project_id,
        "at": at or "latest",
        "reconstructed": state["reconstructed"],
        "unknowns": state["unknowns"],
        "snapshot": snapshot,
        "state": snapshot.get("state", {}),
    }


def _compare_lists(before: list[dict[str, Any]], after: list[dict[str, Any]], key: str = "id") -> dict[str, list[dict[str, Any]]]:
    before_map = {str(item.get(key)): item for item in before}
    after_map = {str(item.get(key)): item for item in after}
    added = [after_map[item] for item in sorted(set(after_map) - set(before_map))]
    removed = [before_map[item] for item in sorted(set(before_map) - set(after_map))]
    modified = [
        {"before": before_map[item], "after": after_map[item]}
        for item in sorted(set(before_map) & set(after_map))
        if _canonical_json(before_map[item]) != _canonical_json(after_map[item])
    ]
    unchanged = [after_map[item] for item in sorted(set(before_map) & set(after_map)) if _canonical_json(before_map[item]) == _canonical_json(after_map[item])]
    return {"added": added, "removed": removed, "modified": modified, "unchanged": unchanged}


def flight_diff(db_path: Path, project_id: str, source_ref: str, target_ref: str) -> dict[str, Any]:
    before = flight_state(db_path, project_id, source_ref)
    after = flight_state(db_path, project_id, target_ref)
    before_state = before["state"]
    after_state = after["state"]
    diff = {
        "repository": _compare_lists([before_state.get("repository", {})], [after_state.get("repository", {})], "scan_id"),
        "files": _compare_lists(before_state.get("semantic", {}).get("files", []), after_state.get("semantic", {}).get("files", []), "source_path"),
        "symbols": _compare_lists(before_state.get("semantic", {}).get("symbols", []), after_state.get("semantic", {}).get("symbols", []), "id"),
        "dependencies": _compare_lists(before_state.get("semantic", {}).get("dependencies", []), after_state.get("semantic", {}).get("dependencies", []), "id"),
        "features": _compare_lists(before_state.get("semantic", {}).get("features", []), after_state.get("semantic", {}).get("features", []), "id"),
        "tests": _compare_lists(before_state.get("semantic", {}).get("tests", []), after_state.get("semantic", {}).get("tests", []), "id"),
        "apis": _compare_lists(before_state.get("semantic", {}).get("apis", []), after_state.get("semantic", {}).get("apis", []), "id"),
        "configuration": _compare_lists(before_state.get("semantic", {}).get("configuration", []), after_state.get("semantic", {}).get("configuration", []), "id"),
        "decisions": _compare_lists(before_state.get("semantic", {}).get("decisions", []), after_state.get("semantic", {}).get("decisions", []), "id"),
        "risks": _compare_lists(before_state.get("semantic", {}).get("risks", []), after_state.get("semantic", {}).get("risks", []), "id"),
        "unknowns": _compare_lists(before_state.get("semantic", {}).get("unknowns", []), after_state.get("semantic", {}).get("unknowns", []), "id"),
        "genome": {"before": before_state.get("genome", {}), "after": after_state.get("genome", {})},
        "maturity": {
            "before": before_state.get("maturity", {}),
            "after": after_state.get("maturity", {}),
        },
        "health": {
            "before": before_state.get("health", {}),
            "after": after_state.get("health", {}),
        },
    }
    transition = {
        "before": before,
        "after": after,
        "observed_change": diff,
        "possible_causes": [],
        "related_decisions": after_state.get("semantic", {}).get("decisions", [])[:10],
        "related_commits": after_state.get("related_commits", [])[:10],
        "related_experiments": [],
        "related_risks": after_state.get("semantic", {}).get("risks", []),
        "confidence": 0.9,
        "unknowns": after.get("unknowns", []),
    }
    return {
        "project_id": project_id,
        "source": source_ref,
        "target": target_ref,
        "before_snapshot": before["snapshot"]["id"],
        "after_snapshot": after["snapshot"]["id"],
        "changes": diff,
        "transition": transition,
    }


def flight_events(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_events WHERE project_id=? ORDER BY timestamp, id",
        (project_id,),
    ).fetchall()
    conn.close()
    items = [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "source_snapshot": row["source_snapshot"],
            "target_snapshot": row["target_snapshot"],
            "affected_entities": _json_loads(row["affected_entities_json"], []),
            "evidence": _json_loads(row["evidence_json"], []),
            "confidence": row["confidence"],
            "metadata": _json_loads(row["metadata_json"], {}),
        }
        for row in rows
    ]
    return {"project_id": project_id, "count": len(items), "items": items}


def flight_regressions(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_regressions WHERE project_id=? ORDER BY timestamp DESC, id DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    items = [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "timestamp": row["timestamp"],
            "indicator_type": row["indicator_type"],
            "severity": row["severity"],
            "confidence": row["confidence"],
            "source_snapshot": row["source_snapshot"],
            "target_snapshot": row["target_snapshot"],
            "summary": row["summary"],
            "evidence": _json_loads(row["evidence_json"], []),
            "affected_entities": _json_loads(row["affected_entities_json"], []),
            "metadata": _json_loads(row["metadata_json"], {}),
        }
        for row in rows
    ]
    return {"project_id": project_id, "count": len(items), "items": items}


def flight_incidents(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_incidents WHERE project_id=? ORDER BY timestamp DESC, id DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    items = [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "timestamp": row["timestamp"],
            "severity": row["severity"],
            "type": row["type"],
            "summary": row["summary"],
            "source": row["source"],
            "affected_entities": _json_loads(row["affected_entities_json"], []),
            "evidence": _json_loads(row["evidence_json"], []),
            "resolved_at": row["resolved_at"],
            "resolution": row["resolution"],
            "related_decisions": _json_loads(row["related_decisions_json"], []),
            "related_commits": _json_loads(row["related_commits_json"], []),
            "metadata": _json_loads(row["metadata_json"], {}),
        }
        for row in rows
    ]
    return {"project_id": project_id, "count": len(items), "items": items}


def flight_timeline(
    db_path: Path,
    project_id: str,
    *,
    event_type: str | None = None,
    feature: str | None = None,
    domain: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    snapshot_rows = conn.execute(
        "SELECT * FROM flight_snapshots WHERE project_id=? ORDER BY created_at, id",
        (project_id,),
    ).fetchall()
    event_rows = conn.execute(
        "SELECT * FROM flight_events WHERE project_id=? ORDER BY timestamp, id",
        (project_id,),
    ).fetchall()
    regression_rows = conn.execute(
        "SELECT * FROM flight_regressions WHERE project_id=? ORDER BY timestamp, id",
        (project_id,),
    ).fetchall()
    incident_rows = conn.execute(
        "SELECT * FROM flight_incidents WHERE project_id=? ORDER BY timestamp, id",
        (project_id,),
    ).fetchall()
    commit_rows = _scan_commit_history(Path(project["repo_path"]), limit=25)
    memory = latest_project_memory(db_path, project_id)
    memory_items = memory_timeline(memory).get("items", []) if memory else []
    conn.close()

    items: list[dict[str, Any]] = []
    for row in snapshot_rows:
        snapshot = _load_snapshot_row(row)
        items.append(
            {
                "id": snapshot["id"],
                "kind": "snapshot",
                "timestamp": snapshot["created_at"],
                "summary": f"Flight snapshot {snapshot['id']}",
                "entity": snapshot["project_id"],
                "metadata": {"scan_id": snapshot["scan_id"], "source_commit": snapshot["source_commit"]},
            }
        )
    for row in event_rows:
        items.append(
            {
                "id": row["id"],
                "kind": row["event_type"],
                "timestamp": row["timestamp"],
                "summary": row["event_type"],
                "entity": row["project_id"],
                "metadata": {"affected_entities": _json_loads(row["affected_entities_json"], [])},
            }
        )
    for row in regression_rows:
        items.append(
            {
                "id": row["id"],
                "kind": "regression",
                "timestamp": row["timestamp"],
                "summary": row["summary"],
                "entity": row["project_id"],
                "metadata": {"indicator_type": row["indicator_type"], "severity": row["severity"]},
            }
        )
    for row in incident_rows:
        items.append(
            {
                "id": row["id"],
                "kind": "incident",
                "timestamp": row["timestamp"],
                "summary": row["summary"],
                "entity": row["project_id"],
                "metadata": {"severity": row["severity"], "type": row["type"]},
            }
        )
    for item in commit_rows:
        items.append({**item, "entity": project_id})
    for item in memory_items:
        items.append(
            {
                "id": item["id"],
                "kind": item["memory_type"],
                "timestamp": item.get("effective_date") or item.get("timestamp"),
                "summary": item["title"],
                "entity": project_id,
                "metadata": {"status": item["status"], "source_path": item.get("source_path")},
            }
        )

    if event_type:
        items = [item for item in items if item["kind"] == event_type or item.get("metadata", {}).get("indicator_type") == event_type]
    if feature:
        items = [item for item in items if feature.lower() in _canonical_json(item).lower()]
    if domain:
        items = [item for item in items if domain.lower() in _canonical_json(item).lower()]
    if since:
        items = [item for item in items if (item.get("timestamp") or "") >= since]
    if until:
        items = [item for item in items if (item.get("timestamp") or "") <= until]
    items.sort(key=lambda item: (item.get("timestamp") or "", item.get("kind") or "", item.get("id") or ""))
    return {"project_id": project_id, "count": len(items), "items": items}


def flight_replay(db_path: Path, project_id: str, source_ref: str, target_ref: str) -> dict[str, Any]:
    before = flight_state(db_path, project_id, source_ref)
    after = flight_state(db_path, project_id, target_ref)
    timeline = flight_timeline(
        db_path,
        project_id,
        since=before["snapshot"]["created_at"],
        until=after["snapshot"]["created_at"],
    )
    items = [
        {"kind": "snapshot", "summary": f"Snapshot {before['snapshot']['id']}", "timestamp": before["snapshot"]["created_at"], "id": before["snapshot"]["id"]},
        *timeline["items"],
        {"kind": "snapshot", "summary": f"Snapshot {after['snapshot']['id']}", "timestamp": after["snapshot"]["created_at"], "id": after["snapshot"]["id"]},
    ]
    items.sort(key=lambda item: (item.get("timestamp") or "", item.get("kind") or "", item.get("id") or ""))
    return {"project_id": project_id, "source": source_ref, "target": target_ref, "count": len(items), "items": items}


def flight_temporal_context(db_path: Path, project_id: str, question: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM flight_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 2",
        (project_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return {"project_id": project_id, "question": question, "historical_facts": [], "observed_changes": [], "associated_events": [], "possible_causes": [], "unknown_causes": ["No flight snapshots available."]}
    latest = _load_snapshot_row(rows[0])
    previous = _load_snapshot_row(rows[1]) if len(rows) > 1 else None
    if not previous:
        return {
            "project_id": project_id,
            "question": question,
            "historical_facts": [latest["state"]],
            "observed_changes": [],
            "associated_events": [],
            "possible_causes": [],
            "unknown_causes": ["Only one flight snapshot is available."],
        }
    diff = flight_diff(db_path, project_id, previous["id"], latest["id"])
    timeline = flight_timeline(db_path, project_id, since=previous["created_at"], until=latest["created_at"])
    return {
        "project_id": project_id,
        "question": question,
        "historical_facts": [{"before": previous["state"], "after": latest["state"]}],
        "observed_changes": diff["changes"],
        "associated_events": timeline["items"][:25],
        "possible_causes": diff["transition"]["possible_causes"],
        "unknown_causes": diff["transition"]["unknowns"] or ["Causality remains partially unknown."],
    }
