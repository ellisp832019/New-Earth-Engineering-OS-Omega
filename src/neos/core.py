from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .manifest import load_manifest
from .models import Finding
from .plugins.runtime import PluginRegistry
from .scanner import scan_repo


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
    last = _latest_scan_row(conn, project_id)
    conn.close()
    return {
        "project_id": project_id,
        "name": project["name"],
        "repo_path": project["repo_path"],
        "lifecycle": project["lifecycle"],
        "counts": counts,
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
    selected_facts = [
        {
            "fact": f"{item['kind']}: {item['label']}",
            "evidence_path": item["source_path"],
            "provenance": item["metadata"].get("origin", "scanner"),
        }
        for item in evidence
    ]
    limitations = [
        "Repository text is treated as untrusted input.",
        "Context is bounded to selected evidence paths.",
    ]
    unknowns = []
    if not latest:
        unknowns.append("No scan exists for this project.")
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
        "provenance": {
            "project_name": project["name"],
            "repo_path": project["repo_path"],
            "latest_scan": dict(latest) if latest else None,
            "source_count": len(latest_rows),
        },
        "unknowns": unknowns,
        "limitations": limitations,
    }
    conn.close()
    return bundle
