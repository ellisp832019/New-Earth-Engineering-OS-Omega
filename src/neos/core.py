from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .flight import flight_temporal_context
from .hardware import build_hardware_intelligence
from .manifest import load_manifest
from .memory import latest_project_memory, memory_timeline, memory_why
from .models import Finding
from .plugins.runtime import PluginRegistry
from .scanner import scan_repo
from .semantic import extract_semantics, persist_semantics


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stable_node_id(project_id: str, source_path: str, kind: str = "artefact", origin: str = "scanner") -> str:
    raw = f"{project_id}:{origin}:{kind}:{source_path}".encode()
    return "node-" + hashlib.sha256(raw).hexdigest()[:24]


def git_commit(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def git_branch(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def git_dirty(repo: Path) -> bool | None:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(output.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def git_state(repo: Path) -> dict[str, Any]:
    return {
        "repo_path": str(repo.resolve()),
        "branch": git_branch(repo),
        "commit": git_commit(repo),
        "dirty": git_dirty(repo),
    }


def _project_row(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown project: {project_id}")
    return row


def _project_repo_path(conn, project_id: str) -> Path:
    row = _project_row(conn, project_id)
    return Path(row["repo_path"])


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
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
            "metadata": json.loads(row["metadata_json"]),
        }
        for row in rows
    ]


def _fingerprint_entries(entries: list[dict[str, Any]]) -> str:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _upsert_node(conn, project_id: str, finding: Finding, scan_id: str, origin: str) -> str:
    node_id = stable_node_id(project_id, finding.source_path, finding.kind, origin)
    conn.execute(
        """
        INSERT INTO nodes(node_id,project_id,kind,label,source_path,content_hash,metadata_json,last_scan_id)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(node_id) DO UPDATE SET
            kind=excluded.kind,
            label=excluded.label,
            source_path=excluded.source_path,
            content_hash=excluded.content_hash,
            metadata_json=excluded.metadata_json,
            last_scan_id=excluded.last_scan_id
        """,
        (
            node_id,
            project_id,
            finding.kind,
            finding.label,
            finding.source_path,
            finding.content_hash,
            json.dumps({**finding.metadata, "origin": origin}, sort_keys=True),
            scan_id,
        ),
    )
    return node_id


def _upsert_edge(conn, project_id: str, source_id: str, target_id: str, relation: str, metadata: dict[str, Any]) -> None:
    edge_id = "edge-" + hashlib.sha256(f"{source_id}:{target_id}:{relation}".encode()).hexdigest()[:24]
    conn.execute(
        """
        INSERT OR REPLACE INTO edges(edge_id,project_id,source_id,target_id,relation,metadata_json)
        VALUES(?,?,?,?,?,?)
        """,
        (edge_id, project_id, source_id, target_id, relation, json.dumps(metadata, sort_keys=True)),
    )


def init_project(db_path: Path, manifest_path: Path) -> str:
    data = load_manifest(manifest_path)
    now = utc_now()
    conn = connect(db_path)
    conn.execute(
        """
        INSERT INTO projects(project_id,name,manifest_path,repo_path,lifecycle,manifest_json,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(project_id) DO UPDATE SET
            name=excluded.name,
            manifest_path=excluded.manifest_path,
            repo_path=excluded.repo_path,
            lifecycle=excluded.lifecycle,
            manifest_json=excluded.manifest_json,
            updated_at=excluded.updated_at
        """,
        (
            data["project_id"],
            data["name"],
            str(manifest_path.resolve()),
            data["repository"]["path"],
            data.get("lifecycle"),
            json.dumps(data, sort_keys=True),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return data["project_id"]


def scan_project(db_path: Path, project_id: str, repo_path: Path) -> dict[str, Any]:
    repo_path = repo_path.resolve()
    findings = scan_repo(repo_path)
    registry = PluginRegistry()
    analyses = registry.analyze(repo_path, {"project_id": project_id})
    plugin_findings = [finding for analysis in analyses for finding in analysis.findings]
    combined_findings = findings + plugin_findings
    scan_id = "scan-" + uuid.uuid4().hex[:16]
    commit = git_commit(repo_path)
    branch = git_branch(repo_path)
    fingerprint = _fingerprint_entries(
        [
            {
                "source_path": finding.source_path,
                "kind": finding.kind,
                "label": finding.label,
                "content_hash": finding.content_hash,
            }
            for finding in findings
        ]
    )

    conn = connect(db_path)
    _project_row(conn, project_id)
    conn.execute(
        """
        INSERT INTO scans(scan_id,project_id,repo_path,git_commit,git_branch,repo_head,created_at,file_count,snapshot_json)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            scan_id,
            project_id,
            str(repo_path),
            commit,
            branch,
            commit,
            utc_now(),
            len(findings),
            json.dumps(
                {
                    "fingerprint": fingerprint,
                    "raw_findings": len(findings),
                    "plugin_findings": len(plugin_findings),
                    "detected_plugins": registry.detect(repo_path),
                },
                sort_keys=True,
            ),
        ),
    )
    semantic_package = extract_semantics(repo_path, project_id, scan_id, combined_findings)
    persist_semantics(conn, semantic_package)

    project_node = "project-" + project_id
    conn.execute(
        """
        INSERT OR IGNORE INTO nodes(node_id,project_id,kind,label,source_path,content_hash,metadata_json,last_scan_id)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (project_node, project_id, "project", project_id, None, None, "{}", scan_id),
    )

    for finding in findings:
        node_id = _upsert_node(conn, project_id, finding, scan_id, "scanner")
        _upsert_edge(conn, project_id, project_node, node_id, "PROJECT_CONTAINS_ARTEFACT", {})
        conn.execute(
            """
            INSERT OR REPLACE INTO scan_observations(
                scan_id, project_id, source_path, kind, label, content_hash, metadata_json
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                scan_id,
                project_id,
                finding.source_path,
                finding.kind,
                finding.label,
                finding.content_hash,
                json.dumps({**finding.metadata, "origin": "scanner"}, sort_keys=True),
            ),
        )

    for finding in plugin_findings:
        node_id = _upsert_node(conn, project_id, finding, scan_id, "plugin")
        _upsert_edge(conn, project_id, project_node, node_id, "PROJECT_CONTAINS_ARTEFACT", {"origin": "plugin"})

    conn.commit()
    conn.close()
    return {
        "scan_id": scan_id,
        "project_id": project_id,
        "file_count": len(findings),
        "plugin_findings": len(plugin_findings),
        "git_commit": commit,
        "git_branch": branch,
        "fingerprint": fingerprint,
        "semantic_counts": {key: len(value) for key, value in semantic_package.items() if isinstance(value, list)},
    }


def _diff_records(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    left_map = {row["source_path"]: row for row in left}
    right_map = {row["source_path"]: row for row in right}
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []

    for path in sorted(set(left_map) | set(right_map)):
        old = left_map.get(path)
        new = right_map.get(path)
        if old is None and new is not None:
            added.append(new)
        elif new is None and old is not None:
            removed.append(old)
        elif old and new:
            if old["content_hash"] == new["content_hash"] and old["kind"] == new["kind"]:
                unchanged.append(new)
            else:
                modified.append({"before": old, "after": new})
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
    }


def scan_diff(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    _project_row(conn, project_id)
    scans = conn.execute(
        "SELECT scan_id, created_at, git_commit, git_branch, file_count FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC",
        (project_id,),
    ).fetchall()
    if not scans:
        raise ValueError(f"No scans available for project: {project_id}")
    latest = scans[0]
    previous = scans[1] if len(scans) > 1 else None
    latest_rows = _scan_rows(conn, latest["scan_id"])
    previous_rows = _scan_rows(conn, previous["scan_id"]) if previous else []
    conn.close()
    return {
        "project_id": project_id,
        "latest_scan_id": latest["scan_id"],
        "previous_scan_id": previous["scan_id"] if previous else None,
        "latest_created_at": latest["created_at"],
        "previous_created_at": previous["created_at"] if previous else None,
        "diff": _diff_records(previous_rows, latest_rows) if previous else {"added": latest_rows, "removed": [], "modified": [], "unchanged": []},
    }


def _inventory_rows(conn, project_id: str, kinds: set[str]) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT node_id, kind, label, source_path, content_hash, metadata_json
        FROM nodes
        WHERE project_id=?
        ORDER BY COALESCE(source_path, label), kind, label
        """,
        (project_id,),
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        if row["kind"] not in kinds:
            continue
        items.append(
            {
                "node_id": row["node_id"],
                "kind": row["kind"],
                "label": row["label"],
                "source_path": row["source_path"],
                "content_hash": row["content_hash"],
                "metadata": json.loads(row["metadata_json"]),
            }
        )
    return items


def hardware_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    return build_hardware_intelligence(db_path, project_id)


def project_summary(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    counts = {
        row["kind"]: row["n"]
        for row in conn.execute(
            "SELECT kind,COUNT(*) AS n FROM nodes WHERE project_id=? GROUP BY kind",
            (project_id,),
        )
    }
    semantic_counts = {
        "symbols": conn.execute("SELECT COUNT(*) FROM symbols WHERE project_id=?", (project_id,)).fetchone()[0],
        "features": conn.execute("SELECT COUNT(*) FROM features WHERE project_id=?", (project_id,)).fetchone()[0],
        "decisions": conn.execute("SELECT COUNT(*) FROM engineering_decisions WHERE project_id=?", (project_id,)).fetchone()[0],
        "api_endpoints": conn.execute("SELECT COUNT(*) FROM api_endpoints WHERE project_id=?", (project_id,)).fetchone()[0],
        "configuration_keys": conn.execute("SELECT COUNT(*) FROM configuration_keys WHERE project_id=?", (project_id,)).fetchone()[0],
        "relationships": conn.execute("SELECT COUNT(*) FROM relationships WHERE project_id=?", (project_id,)).fetchone()[0],
        "dependencies": conn.execute("SELECT COUNT(*) FROM dependencies WHERE project_id=?", (project_id,)).fetchone()[0],
    }
    last = _latest_scan_row(conn, project_id)
    conn.close()
    return {
        "project_id": project_id,
        "name": project["name"],
        "repo_path": project["repo_path"],
        "lifecycle": project["lifecycle"],
        "counts": counts,
        "semantic_counts": semantic_counts,
        "last_scan": dict(last) if last else None,
    }


def technology_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    manifest = json.loads(project["manifest_json"])
    latest = _latest_scan_row(conn, project_id)
    plugins = []
    if latest and latest["snapshot_json"]:
        plugins = json.loads(latest["snapshot_json"]).get("detected_plugins", [])
    technologies = sorted(
        {
            *(manifest.get("technologies", []) or []),
            *plugins,
        }
    )
    conn.close()
    return {"project_id": project_id, "technologies": technologies}


def documentation_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    items = _inventory_rows(conn, project_id, {"documentation", "release_documentation"})
    conn.close()
    return {"project_id": project_id, "items": items, "count": len(items)}


def test_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    items = _inventory_rows(conn, project_id, {"test"})
    conn.close()
    return {"project_id": project_id, "items": items, "count": len(items)}


def build_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    items = _inventory_rows(conn, project_id, {"build_definition", "ci_workflow", "application_configuration"})
    conn.close()
    return {"project_id": project_id, "items": items, "count": len(items)}


def git_state_report(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    last = _latest_scan_row(conn, project_id)
    conn.close()
    repo_path = Path(project["repo_path"])
    current = git_state(repo_path)
    return {
        "project_id": project_id,
        "repo_path": current["repo_path"],
        "current": current,
        "last_scan": dict(last) if last else None,
    }


def stale_scan_status(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    last = _latest_scan_row(conn, project_id)
    conn.close()
    if not last:
        return {"project_id": project_id, "status": "stale", "reason": "no_scans"}
    current = git_state(Path(project["repo_path"]))
    if current["commit"] and last["git_commit"] and current["commit"] != last["git_commit"]:
        return {
            "project_id": project_id,
            "status": "stale",
            "reason": "git_head_changed",
            "current_commit": current["commit"],
            "last_scan_commit": last["git_commit"],
        }
    if current["dirty"]:
        return {"project_id": project_id, "status": "stale", "reason": "working_tree_dirty"}
    return {"project_id": project_id, "status": "fresh", "reason": "scan_matches_head"}


def _select_evidence_rows(conn, project_id: str, keywords: set[str], limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT node_id, kind, label, source_path, content_hash, metadata_json
        FROM nodes
        WHERE project_id=?
        ORDER BY COALESCE(source_path, label), kind, label
        """,
        (project_id,),
    ).fetchall()
    selected: list[dict[str, Any]] = []
    for row in rows:
        path_text = (row["source_path"] or "").lower()
        label_text = (row["label"] or "").lower()
        if keywords and not any(keyword in path_text or keyword in label_text for keyword in keywords):
            continue
        selected.append(
            {
                "node_id": row["node_id"],
                "kind": row["kind"],
                "label": row["label"],
                "source_path": row["source_path"],
                "content_hash": row["content_hash"],
                "metadata": json.loads(row["metadata_json"]),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def context_bundle(db_path: Path, project_id: str, question: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    latest = _latest_scan_row(conn, project_id)
    latest_rows = _scan_rows(conn, latest["scan_id"]) if latest else []
    question_lc = question.lower()
    keywords = set()
    if "test" in question_lc:
        keywords.update({"test", "tests", "spec"})
    if "doc" in question_lc:
        keywords.update({"doc", "docs", "readme"})
    if "build" in question_lc or "ci" in question_lc:
        keywords.update({"build", "workflow", "platformio", "pubspec", "docker"})
    if "git" in question_lc or "branch" in question_lc:
        keywords.update({"git", "branch"})
    if not keywords:
        keywords.update({"readme", "docs", "test", "build"})
    evidence = _select_evidence_rows(conn, project_id, keywords)
    if not evidence:
        evidence = _select_evidence_rows(conn, project_id, set(), limit=8)
    selected_facts = []
    for item in evidence:
        selected_facts.append(
            {
                "id": item["node_id"],
                "kind": item["kind"],
                "summary": f"{item['kind']}: {item['label']}",
                "evidence_path": item["source_path"],
                "provenance": item["metadata"].get("origin", "scanner"),
                "confidence": 0.8,
            }
        )
    inferences = []
    if selected_facts:
        inferences.append(
            {
                "summary": f"{len(selected_facts)} evidence items matched the question keywords.",
                "confidence": 0.7,
                "provenance": "deterministic-query",
            }
        )
    if latest and latest_rows:
        inferences.append(
            {
                "summary": f"The latest scan observed {len(latest_rows)} raw artefacts.",
                "confidence": 0.95,
                "provenance": "scan-snapshot",
            }
        )
    limitations = [
        "Repository text is treated as untrusted input.",
        "Context is bounded to selected evidence paths.",
    ]
    unknowns = []
    if not latest:
        unknowns.append("No scan exists for this project.")
    injection_warnings = []
    for row in latest_rows[:50]:
        source_path = row["source_path"]
        file_path = Path(project["repo_path"]) / source_path
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore") if file_path.exists() else ""
        except OSError:
            text = ""
        if text and any(marker in text.lower() for marker in ("ignore previous instructions", "system prompt", "prompt injection")):
            injection_warnings.append({"source_path": source_path, "warning": "instruction-like repository text detected"})
    bundle = {
        "project_id": project_id,
        "scan_id": latest["scan_id"] if latest else None,
        "scan_freshness": {
            "created_at": latest["created_at"] if latest else None,
            "file_count": latest["file_count"] if latest else 0,
            "fingerprint": json.loads(latest["snapshot_json"]).get("fingerprint") if latest else None,
        },
        "generated_at": utc_now(),
        "question": question,
        "evidence_paths": [item["source_path"] for item in evidence],
        "selected_facts": selected_facts,
        "facts": selected_facts,
        "inferences": inferences,
        "provenance": {
            "project_name": project["name"],
            "repo_path": project["repo_path"],
            "latest_scan": dict(latest) if latest else None,
            "source_count": len(latest_rows),
        },
        "unknowns": unknowns,
        "limitations": limitations,
        "warnings": injection_warnings,
    }
    memory: dict[str, Any] = latest_project_memory(db_path, project_id)
    if memory:
        bundle["historical_record"] = memory_timeline(memory)
        bundle["memory_provenance"] = memory.get("provenance", {})
        bundle["decisions"] = memory.get("records", {}).get("decision", [])
        bundle["assumptions"] = memory.get("records", {}).get("assumption", [])
        bundle["lessons"] = memory.get("records", {}).get("lesson", [])
        bundle["memory_unknowns"] = memory.get("gaps", [])
    bundle["temporal_intelligence"] = flight_temporal_context(db_path, project_id, question)
    conn.close()
    return bundle


def _row_dict(row) -> dict[str, Any]:
    return dict(row) if row else {}


def _entity_lookup(conn, entity_id: str) -> dict[str, Any] | None:
    for table in (
        "symbols",
        "features",
        "engineering_decisions",
        "api_endpoints",
        "configuration_keys",
        "impact_findings",
    ):
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (entity_id,)).fetchone()
        if row:
            data = dict(row)
            data["entity_table"] = table
            data["entity_type"] = table.removesuffix("s")
            return data
    return None


def _entity_evidence(conn, entity_id: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    symbol = conn.execute("SELECT * FROM symbols WHERE id=?", (entity_id,)).fetchone()
    if symbol:
        location = conn.execute("SELECT * FROM symbol_locations WHERE symbol_id=? ORDER BY start_line LIMIT 1", (entity_id,)).fetchone()
        evidence.append({"type": "symbol_location", "row": _row_dict(location)})
    for table, parent_column in (
        ("feature_evidence", "feature_id"),
        ("decision_evidence", "decision_id"),
    ):
        rows = conn.execute(f"SELECT * FROM {table} WHERE {parent_column}=? ORDER BY source_path, start_line", (entity_id,)).fetchall()
        evidence.extend({"type": table, "row": dict(row)} for row in rows)
    return evidence


def _adjacency_rows(conn, entity_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in conn.execute(
        """
        SELECT id, source_entity_id, target_entity_id, relationship_type, confidence, evidence_source, scan_id, parser_source, created_at, metadata_json
        FROM relationships
        WHERE source_entity_id=? OR target_entity_id=?
        ORDER BY relationship_type, id
        """,
        (entity_id, entity_id),
    ):
        rows.append(dict(row))
    for row in conn.execute(
        """
        SELECT id, source_entity_id, target_entity_id, dependency_type AS relationship_type, confidence, evidence_source, scan_id, parser_source, created_at, metadata_json
        FROM dependencies
        WHERE source_entity_id=? OR target_entity_id=?
        ORDER BY dependency_type, id
        """,
        (entity_id, entity_id),
    ):
        rows.append(dict(row))
    for row in conn.execute(
        """
        SELECT id AS id, feature_id AS source_entity_id, entity_id AS target_entity_id, 'supported_by' AS relationship_type,
               confidence, provenance AS evidence_source, scan_id, 'feature_evidence' AS parser_source, '' AS created_at, metadata_json
        FROM feature_evidence
        WHERE feature_id=? OR entity_id=?
        ORDER BY id
        """,
        (entity_id, entity_id),
    ):
        rows.append(dict(row))
    for row in conn.execute(
        """
        SELECT id AS id, decision_id AS source_entity_id, entity_id AS target_entity_id, 'supported_by' AS relationship_type,
               confidence, provenance AS evidence_source, scan_id, 'decision_evidence' AS parser_source, '' AS created_at, metadata_json
        FROM decision_evidence
        WHERE decision_id=? OR entity_id=?
        ORDER BY id
        """,
        (entity_id, entity_id),
    ):
        rows.append(dict(row))
    return rows


def _project_entities(conn, table: str, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE project_id=? ORDER BY id",
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def symbol_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _project_entities(conn, "symbols", project_id)
    conn.close()
    return {"project_id": project_id, "count": len(rows), "items": rows}


def symbol_show(db_path: Path, symbol_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    symbol = conn.execute("SELECT * FROM symbols WHERE id=?", (symbol_id,)).fetchone()
    location = conn.execute("SELECT * FROM symbol_locations WHERE symbol_id=? ORDER BY start_line LIMIT 1", (symbol_id,)).fetchone()
    conn.close()
    if not symbol:
        raise ValueError(f"Unknown symbol: {symbol_id}")
    return {"symbol": dict(symbol), "location": _row_dict(location)}


def feature_inventory(db_path: Path, project_id: str, candidates_only: bool = False) -> dict[str, Any]:
    conn = connect(db_path)
    if candidates_only:
        rows = conn.execute(
            "SELECT * FROM features WHERE project_id=? AND source='heuristic' ORDER BY confidence DESC, name",
            (project_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM features WHERE project_id=? ORDER BY source, confidence DESC, name",
            (project_id,),
        ).fetchall()
    conn.close()
    return {"project_id": project_id, "count": len(rows), "items": [dict(row) for row in rows]}


def feature_show(db_path: Path, feature_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    feature = conn.execute("SELECT * FROM features WHERE id=?", (feature_id,)).fetchone()
    evidence = conn.execute("SELECT * FROM feature_evidence WHERE feature_id=? ORDER BY source_path, start_line", (feature_id,)).fetchall()
    conn.close()
    if not feature:
        raise ValueError(f"Unknown feature: {feature_id}")
    return {"feature": dict(feature), "evidence": [dict(row) for row in evidence]}


def confirm_feature(db_path: Path, feature_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    feature = conn.execute("SELECT * FROM features WHERE id=?", (feature_id,)).fetchone()
    if not feature:
        conn.close()
        raise ValueError(f"Unknown feature: {feature_id}")
    now = utc_now()
    conn.execute(
        "UPDATE features SET source='operator', status='validated', updated_at=? WHERE id=?",
        (now, feature_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM features WHERE id=?", (feature_id,)).fetchone()
    conn.close()
    return {"feature": dict(updated)}


def decision_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _project_entities(conn, "engineering_decisions", project_id)
    conn.close()
    return {"project_id": project_id, "count": len(rows), "items": rows}


def decision_show(db_path: Path, decision_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    decision = conn.execute("SELECT * FROM engineering_decisions WHERE id=?", (decision_id,)).fetchone()
    evidence = conn.execute("SELECT * FROM decision_evidence WHERE decision_id=? ORDER BY source_path, start_line", (decision_id,)).fetchall()
    conn.close()
    if not decision:
        raise ValueError(f"Unknown decision: {decision_id}")
    return {"decision": dict(decision), "evidence": [dict(row) for row in evidence]}


def api_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _project_entities(conn, "api_endpoints", project_id)
    conn.close()
    return {"project_id": project_id, "count": len(rows), "items": rows}


def configuration_inventory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _project_entities(conn, "configuration_keys", project_id)
    conn.close()
    return {"project_id": project_id, "count": len(rows), "items": rows}


def dependencies_for_entity(db_path: Path, entity_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _adjacency_rows(conn, entity_id)
    conn.close()
    deps = [row for row in rows if row["relationship_type"] in {"imports", "depends_on"}]
    return {"entity_id": entity_id, "count": len(deps), "items": deps}


def trace_entity(db_path: Path, entity_id: str, depth: int = 3, relationship: str | None = None, direction: str = "both") -> dict[str, Any]:
    conn = connect(db_path)
    visited = {entity_id}
    frontier: list[tuple[str, int, list[str]]] = [(entity_id, 0, [])]
    edges: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    while frontier:
        current_id, current_depth, path = frontier.pop(0)
        if current_depth >= depth:
            continue
        for row in _adjacency_rows(conn, current_id):
            rel_type = row["relationship_type"]
            if relationship and rel_type != relationship:
                continue
            if direction == "out" and row["source_entity_id"] != current_id:
                continue
            if direction == "in" and row["target_entity_id"] != current_id:
                continue
            next_id = row["target_entity_id"] if row["source_entity_id"] == current_id else row["source_entity_id"]
            edge = dict(row)
            edge["depth"] = current_depth + 1
            edge["path"] = path + [rel_type]
            edges.append(edge)
            if next_id not in visited:
                visited.add(next_id)
                entity = _entity_lookup(conn, next_id)
                if entity:
                    nodes.append({"id": next_id, "entity": entity, "depth": current_depth + 1})
                frontier.append((next_id, current_depth + 1, path + [rel_type]))
    conn.close()
    return {"entity_id": entity_id, "depth": depth, "nodes": nodes, "edges": edges}


def impact_entity(db_path: Path, entity_id: str, depth: int = 2) -> dict[str, Any]:
    trace = trace_entity(db_path, entity_id, depth=depth, direction="both")
    direct = [edge for edge in trace["edges"] if edge["depth"] == 1]
    indirect = [edge for edge in trace["edges"] if edge["depth"] > 1]
    affected_features = []
    affected_tests = []
    affected_docs = []
    affected_api = []
    affected_config = []
    affected_decisions = []
    for node in trace["nodes"]:
        entity = node["entity"]
        kind = entity.get("kind") or entity.get("entity_type")
        item = {"id": node["id"], "kind": kind, "name": entity.get("name") or entity.get("title") or entity.get("route"), "path": entity.get("source_path"), "depth": node["depth"]}
        if kind == "feature":
            affected_features.append(item)
        elif kind in {"test_function", "test_class", "test"}:
            affected_tests.append(item)
        elif kind in {"module", "class", "function", "method", "async_function", "cli_entry_point"}:
            affected_docs.append(item)
        elif kind == "api_endpoint":
            affected_api.append(item)
        elif kind == "configuration_key":
            affected_config.append(item)
        elif kind == "decision":
            affected_decisions.append(item)
    conn = connect(db_path)
    entity = _entity_lookup(conn, entity_id)
    conn.close()
    return {
        "entity": entity,
        "direct_impacts": direct,
        "indirect_impacts": indirect,
        "affected_features": affected_features,
        "affected_tests": affected_tests,
        "affected_documentation": affected_docs,
        "affected_api": affected_api,
        "affected_configuration": affected_config,
        "affected_decisions": affected_decisions,
        "unknown_areas": [],
    }


def why_entity(db_path: Path, entity_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    entity = _entity_lookup(conn, entity_id)
    evidence = _entity_evidence(conn, entity_id)
    related_decisions = conn.execute(
        """
        SELECT d.*
        FROM engineering_decisions d
        JOIN decision_evidence e ON e.decision_id = d.id
        WHERE e.entity_id = ? OR d.id = ?
        ORDER BY d.date, d.title
        """,
        (entity_id, entity_id),
    ).fetchall()
    conn.close()
    rationale = "Rationale not recorded in current NEOS evidence."
    if entity and entity.get("kind") == "decision":
        rationale = entity.get("rationale") or rationale
    result: dict[str, Any] = {
        "entity": entity,
        "evidence": evidence,
        "decisions": [dict(row) for row in related_decisions],
        "rationale": rationale,
    }
    memory = latest_project_memory(db_path, str(entity["project_id"])) if entity and entity.get("project_id") else {}
    if memory:
        memory_result = memory_why(memory, entity_id)
        result.update(
            {
                "recorded_rationale": memory_result["recorded_rationale"],
                "supporting_evidence": memory_result["supporting_evidence"],
                "related_decisions": memory_result["related_decisions"],
                "historical_changes": memory_result["historical_changes"],
                "unknown_rationale": memory_result["unknown_rationale"],
                "memory_trace": memory_result["trace"],
            }
        )
    else:
        result.update(
            {
                "recorded_rationale": [rationale] if rationale else [],
                "supporting_evidence": evidence,
                "related_decisions": [dict(row) for row in related_decisions],
                "historical_changes": [],
                "unknown_rationale": [] if rationale else ["Rationale not recorded in current engineering memory."],
            }
        )
    return result
