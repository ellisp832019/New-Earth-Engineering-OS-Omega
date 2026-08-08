from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .core import scan_project
from .db import connect
from .ecosystem import analyse_portfolio, project_registry_v2, search_ecosystem
from .flight import latest_project_flight
from .genome import latest_project_genome
from .memory import latest_project_memory
from .requirements_intelligence import (
    architecture_without_requirement,
    build_requirement_intelligence,
    requirement_gaps,
    requirement_inventory,
    unimplemented_requirements,
    untested_requirements,
    verification_readiness,
)

SESSION_KEY = "workspace"
WORK_ITEM_STATES = {"open", "acknowledged", "deferred", "dismissed", "done"}
WORK_ITEM_CLOSED_STATES = {"dismissed", "done"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _utcnow() -> str:
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


def _stable_id(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _project_ids(project_ids: list[str] | None) -> list[str] | None:
    if not project_ids:
        return None
    values = [item.strip() for item in project_ids if item and item.strip()]
    return values or None


def _project_map(db_path: Path) -> dict[str, dict[str, Any]]:
    registry = project_registry_v2(db_path)
    return {row["project_id"]: row for row in registry["projects"]}


def _project_exists(conn: sqlite3.Connection, project_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone()
    return row is not None


def _project_row(conn: sqlite3.Connection, project_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT project_id, name, repo_path, lifecycle, manifest_json FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown project: {project_id}")
    return dict(row)


def _session_state_row(conn: sqlite3.Connection, session_key: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT session_key, value_json, updated_at FROM app_sessions WHERE session_key=?",
        (session_key,),
    ).fetchone()
    return dict(row) if row else None


def get_app_session(db_path: Path, session_key: str = SESSION_KEY) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        row = _session_state_row(conn, session_key)
        if row is None:
            return {
                "session_key": session_key,
                "state": {},
                "updated_at": None,
            }
        return {
            "session_key": session_key,
            "state": _json_loads(row["value_json"], {}),
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def set_app_session(db_path: Path, state: dict[str, Any], session_key: str = SESSION_KEY) -> dict[str, Any]:
    conn = connect(db_path)
    updated_at = _utcnow()
    conn.execute(
        """
        INSERT INTO app_sessions(session_key, value_json, updated_at)
        VALUES(?, ?, ?)
        ON CONFLICT(session_key) DO UPDATE SET
            value_json=excluded.value_json,
            updated_at=excluded.updated_at
        """,
        (session_key, _json_dumps(state), updated_at),
    )
    conn.commit()
    conn.close()
    return {"session_key": session_key, "state": state, "updated_at": updated_at}


def _store_work_item(conn: sqlite3.Connection, item: dict[str, Any]) -> None:
    existing = conn.execute("SELECT status, metadata_json FROM work_items WHERE id=?", (item["id"],)).fetchone()
    status = item.get("status", "open")
    if existing is not None and existing["status"] in WORK_ITEM_CLOSED_STATES:
        status = existing["status"]
    conn.execute(
        """
        INSERT INTO work_items(
            id, project_id, scope, category, priority, title, why, evidence_json,
            recommended_action, status, source, source_fingerprint, created_at, updated_at, metadata_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            project_id=excluded.project_id,
            scope=excluded.scope,
            category=excluded.category,
            priority=excluded.priority,
            title=excluded.title,
            why=excluded.why,
            evidence_json=excluded.evidence_json,
            recommended_action=excluded.recommended_action,
            status=?,
            source=excluded.source,
            source_fingerprint=excluded.source_fingerprint,
            updated_at=excluded.updated_at,
            metadata_json=excluded.metadata_json
        """,
        (
            item["id"],
            item["project_id"],
            item["scope"],
            item["category"],
            item["priority"],
            item["title"],
            item["why"],
            item["evidence_json"],
            item["recommended_action"],
            status,
            item["source"],
            item["source_fingerprint"],
            item["created_at"],
            item["updated_at"],
            item["metadata_json"],
            status,
        ),
    )


def _queue_item(
    *,
    project_id: str,
    scope: str,
    category: str,
    priority: str,
    title: str,
    why: str,
    evidence: dict[str, Any],
    recommended_action: str,
    source: str,
) -> dict[str, Any]:
    source_fingerprint = _stable_id(project_id, scope, category, priority, title, why, _json_dumps(evidence), source)
    now = _utcnow()
    return {
        "id": source_fingerprint,
        "project_id": project_id,
        "scope": scope,
        "category": category,
        "priority": priority,
        "title": title,
        "why": why,
        "evidence_json": _json_dumps(evidence),
        "recommended_action": recommended_action,
        "status": "open",
        "source": source,
        "source_fingerprint": source_fingerprint,
        "created_at": now,
        "updated_at": now,
        "metadata_json": _json_dumps({"kind": "deterministic_command_centre", "source": source}),
    }


def _add_default_queue_items(project_id: str, project: dict[str, Any], genome: dict[str, Any] | None, memory: dict[str, Any] | None, flight: dict[str, Any] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not project.get("last_scan_id"):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="scan",
                priority="high",
                title="Scan the repository",
                why="The project has no recorded scan yet, so downstream intelligence is incomplete.",
                evidence={"last_scan_id": None, "project": project},
                recommended_action="Run a fresh project scan before reviewing downstream intelligence.",
                source="scan-state",
            ),
        )
    if genome is None:
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="genome",
                priority="high",
                title="Build the project genome",
                why="There is no genome snapshot to summarise project structure, risks, or attention.",
                evidence={"genome": None},
                recommended_action="Build the project genome after the latest scan.",
                source="genome-state",
            ),
        )
    if memory is None:
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="memory",
                priority="medium",
                title="Build engineering memory",
                why="The project has no memory snapshot to preserve rationale and prior decisions.",
                evidence={"memory": None},
                recommended_action="Build the project memory snapshot after the genome refresh.",
                source="memory-state",
            ),
        )
    if flight is None:
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="flight",
                priority="medium",
                title="Build the flight recorder",
                why="The project has no flight snapshot to capture release and regression context.",
                evidence={"flight": None},
                recommended_action="Build the flight recorder after the memory snapshot refresh.",
                source="flight-state",
            ),
        )
    return items


def _add_requirement_items(project_id: str, requirements: dict[str, Any], gaps: dict[str, Any], verification: dict[str, Any], architecture_gaps: dict[str, Any], unimplemented: dict[str, Any], untested: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if gaps.get("count", 0):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="requirements",
                priority="high" if gaps["count"] >= 3 else "medium",
                title=f"Close {gaps['count']} requirement gap(s)",
                why="Some requirements do not yet have full feature, architecture, validation, or release traceability.",
                evidence={"requirements": requirements, "gaps": gaps},
                recommended_action="Review the gaps and attach evidence or implementation links.",
                source="requirements-gap-analysis",
            ),
        )
    if verification.get("count", 0) < requirements.get("count", 0):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="verification",
                priority="medium",
                title="Raise verification coverage",
                why="Not every requirement is currently verified end-to-end.",
                evidence={"requirements": requirements, "verification": verification},
                recommended_action="Add or link tests, validation, or release evidence for the uncovered requirements.",
                source="verification-readiness",
            ),
        )
    if architecture_gaps.get("count", 0):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="architecture",
                priority="medium",
                title="Resolve architecture without requirement",
                why="Some architecture entries are not traced back to a requirement.",
                evidence={"architecture_gaps": architecture_gaps},
                recommended_action="Trace each architecture item to its originating requirement or mark it intentional.",
                source="architecture-traceability",
            ),
        )
    if unimplemented.get("count", 0):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="implementation",
                priority="medium",
                title="Implement outstanding requirements",
                why="The requirement inventory still has items without implementation evidence.",
                evidence={"unimplemented": unimplemented},
                recommended_action="Link the missing requirements to implementation or break them into executable work.",
                source="implementation-traceability",
            ),
        )
    if untested.get("count", 0):
        items.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="tests",
                priority="medium",
                title="Add missing test evidence",
                why="There are requirements without recorded test coverage.",
                evidence={"untested": untested},
                recommended_action="Add tests or record evidence for the unverified requirements.",
                source="test-traceability",
            ),
        )
    return items


def _project_attention_items(project_id: str, genome: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not genome:
        return []
    attention = genome.get("attention", {})
    items = attention.get("items", []) if isinstance(attention, dict) else []
    if not isinstance(items, list):
        return []
    results: list[dict[str, Any]] = []
    for index, item in enumerate(items[:3]):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("label") or item.get("name") or f"Attention item {index + 1}").strip()
        if not title:
            continue
        results.append(
            _queue_item(
                project_id=project_id,
                scope="project",
                category="attention",
                priority=str(item.get("priority") or "medium"),
                title=title,
                why=str(item.get("reason") or item.get("summary") or "The genome marked this item for attention."),
                evidence={"attention_item": item},
                recommended_action=str(item.get("next_action") or "Review the attention item in the project genome."),
                source="genome-attention",
            )
        )
    return results


def build_work_queue(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        projects = _project_map(db_path)
        selected_ids = _project_ids(project_ids) or list(projects)
        queue: list[dict[str, Any]] = []
        for project_id in selected_ids:
            project = projects.get(project_id)
            if project is None:
                continue
            genome = latest_project_genome(db_path, project_id)
            memory = latest_project_memory(db_path, project_id)
            flight = latest_project_flight(db_path, project_id)
            requirements = requirement_inventory(db_path, [project_id])
            gaps = requirement_gaps(db_path, [project_id])
            verification = verification_readiness(db_path, [project_id])
            architecture_gaps = architecture_without_requirement(db_path, [project_id])
            unimplemented = unimplemented_requirements(db_path, [project_id])
            untested = untested_requirements(db_path, [project_id])

            project_items = []
            project_items.extend(_add_default_queue_items(project_id, project, genome, memory, flight))
            project_items.extend(_add_requirement_items(project_id, requirements, gaps, verification, architecture_gaps, unimplemented, untested))
            project_items.extend(_project_attention_items(project_id, genome))

            for item in project_items:
                _store_work_item(conn, item)
            queue.extend(project_items)
        conn.commit()
        queue.sort(key=lambda item: (item["project_id"], PRIORITY_ORDER.get(item["priority"], 99), item["title"]))
        return {
            "generated_at": _utcnow(),
            "project_ids": selected_ids,
            "count": len(queue),
            "items": queue,
            "summary": {
                "project_count": len(selected_ids),
                "open_count": sum(1 for item in queue if item["status"] == "open"),
                "high_priority_count": sum(1 for item in queue if item["priority"] == "high"),
            },
        }
    finally:
        conn.close()


def load_work_queue(db_path: Path, project_ids: list[str] | None = None, *, include_closed: bool = False) -> dict[str, Any]:
    queue = build_work_queue(db_path, project_ids)
    if include_closed:
        return queue
    items = [item for item in queue["items"] if item["status"] not in WORK_ITEM_CLOSED_STATES]
    return {
        **queue,
        "count": len(items),
        "items": items,
        "summary": {
            **queue["summary"],
            "open_count": sum(1 for item in items if item["status"] == "open"),
        },
    }


def load_work_item(db_path: Path, work_item_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT id, project_id, scope, category, priority, title, why, evidence_json, recommended_action,
                   status, source, source_fingerprint, created_at, updated_at, metadata_json
            FROM work_items
            WHERE id=?
            """,
            (work_item_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown work item: {work_item_id}")
        item = dict(row)
        item["evidence"] = _json_loads(item.pop("evidence_json"), {})
        item["metadata"] = _json_loads(item.pop("metadata_json"), {})
        return item
    finally:
        conn.close()


def update_work_item(db_path: Path, work_item_id: str, status: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    if status not in WORK_ITEM_STATES:
        raise ValueError(f"Unsupported work item state: {status}")
    conn = connect(db_path)
    try:
        row = conn.execute("SELECT * FROM work_items WHERE id=?", (work_item_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown work item: {work_item_id}")
        metadata = _json_loads(row["metadata_json"], {})
        metadata["last_action"] = {
            "operator": operator,
            "notes": notes,
            "status": status,
            "updated_at": _utcnow(),
        }
        conn.execute(
            """
            UPDATE work_items
            SET status=?, updated_at=?, metadata_json=?
            WHERE id=?
            """,
            (status, _utcnow(), _json_dumps(metadata), work_item_id),
        )
        conn.commit()
        return load_work_item(db_path, work_item_id)
    finally:
        conn.close()


def acknowledge_work_item(db_path: Path, work_item_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    return update_work_item(db_path, work_item_id, "acknowledged", operator=operator, notes=notes)


def defer_work_item(db_path: Path, work_item_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    return update_work_item(db_path, work_item_id, "deferred", operator=operator, notes=notes)


def dismiss_work_item(db_path: Path, work_item_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    return update_work_item(db_path, work_item_id, "dismissed", operator=operator, notes=notes)


def resolve_work_item(db_path: Path, work_item_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    return update_work_item(db_path, work_item_id, "done", operator=operator, notes=notes)


def command_centre_health(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        open_work_items = conn.execute(
            "SELECT COUNT(*) FROM work_items WHERE status NOT IN ('dismissed', 'done')",
        ).fetchone()[0]
        active_refresh_jobs = conn.execute(
            "SELECT COUNT(*) FROM refresh_jobs WHERE status IN ('queued', 'running')",
        ).fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM app_sessions").fetchone()[0]
        last_refresh = conn.execute(
            """
            SELECT job_id, project_id, status, current_stage, stage_index, stage_total, created_at, updated_at
            FROM refresh_jobs
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """,
        ).fetchone()
        return {
            "status": "healthy",
            "project_count": project_count,
            "open_work_items": open_work_items,
            "active_refresh_jobs": active_refresh_jobs,
            "session_count": session_count,
            "last_refresh_job": dict(last_refresh) if last_refresh else None,
        }
    finally:
        conn.close()


def _refresh_job_row(conn: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM refresh_jobs WHERE job_id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def refresh_project_intelligence(db_path: Path, project_id: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = options or {}
    conn = connect(db_path)
    try:
        if not _project_exists(conn, project_id):
            raise ValueError(f"Unknown project: {project_id}")
        job_id = str(opts.get("job_id") or _stable_id("refresh-job", project_id, _utcnow()))
        stages = [str(stage) for stage in opts.get("stages", ["scan", "genome", "memory", "flight", "requirements", "work_queue"])]
        now = _utcnow()
        conn.execute(
            """
            INSERT INTO refresh_jobs(
                job_id, project_id, status, current_stage, stage_index, stage_total, stages_json, options_json,
                result_json, error_text, created_at, updated_at, metadata_json
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                project_id=excluded.project_id,
                status=excluded.status,
                current_stage=excluded.current_stage,
                stage_index=excluded.stage_index,
                stage_total=excluded.stage_total,
                stages_json=excluded.stages_json,
                options_json=excluded.options_json,
                result_json=excluded.result_json,
                error_text=excluded.error_text,
                updated_at=excluded.updated_at,
                metadata_json=excluded.metadata_json
            """,
            (
                job_id,
                project_id,
                "running",
                stages[0] if stages else "queued",
                0,
                len(stages),
                _json_dumps(stages),
                _json_dumps(opts),
                _json_dumps({}),
                "",
                now,
                now,
                _json_dumps({"kind": "refresh_job"}),
            ),
        )
        conn.commit()

        result: dict[str, Any] = {"job_id": job_id, "project_id": project_id, "status": "running", "stages": stages, "started_at": now}
        repo_path = Path(_project_row(conn, project_id)["repo_path"])
        stage_outputs: dict[str, Any] = {}
        try:
            for index, stage in enumerate(stages, start=1):
                conn.execute(
                    "UPDATE refresh_jobs SET current_stage=?, stage_index=?, updated_at=? WHERE job_id=?",
                    (stage, index - 1, _utcnow(), job_id),
                )
                conn.commit()
                if stage == "scan" and opts.get("scan", True):
                    stage_outputs["scan"] = scan_project(db_path, project_id, repo_path)
                elif stage == "genome" and opts.get("genome", True):
                    from .genome import build_project_genome

                    stage_outputs["genome"] = build_project_genome(db_path, project_id)
                elif stage == "memory" and opts.get("memory", True):
                    from .memory import build_project_memory

                    stage_outputs["memory"] = build_project_memory(db_path, project_id)
                elif stage == "flight" and opts.get("flight", True):
                    from .flight import build_project_flight

                    stage_outputs["flight"] = build_project_flight(db_path, project_id)
                elif stage == "requirements" and opts.get("requirements", True):
                    stage_outputs["requirements"] = build_requirement_intelligence(db_path, [project_id])
                elif stage == "work_queue" and opts.get("work_queue", True):
                    stage_outputs["work_queue"] = build_work_queue(db_path, [project_id])
                conn.execute(
                    "UPDATE refresh_jobs SET stage_index=?, updated_at=? WHERE job_id=?",
                    (index, _utcnow(), job_id),
                )
                conn.commit()
            result.update(
                {
                    "status": "completed",
                    "completed_at": _utcnow(),
                    "outputs": stage_outputs,
                    "work_queue": load_work_queue(db_path, [project_id]),
                }
            )
            conn.execute(
                "UPDATE refresh_jobs SET status=?, current_stage=?, stage_index=?, result_json=?, error_text=?, updated_at=? WHERE job_id=?",
                (
                    "completed",
                    "completed",
                    len(stages),
                    _json_dumps(result),
                    "",
                    _utcnow(),
                    job_id,
                ),
            )
            conn.commit()
            return result
        except Exception as exc:  # pragma: no cover - defensive persistence path  # noqa: BLE001
            result.update({"status": "failed", "error": str(exc), "completed_at": _utcnow()})
            conn.execute(
                "UPDATE refresh_jobs SET status=?, current_stage=?, stage_index=?, result_json=?, error_text=?, updated_at=? WHERE job_id=?",
                (
                    "failed",
                    stages[min(len(stages) - 1, 0)] if stages else "failed",
                    0,
                    _json_dumps(result),
                    str(exc),
                    _utcnow(),
                    job_id,
                ),
            )
            conn.commit()
            return result
    finally:
        conn.close()


def load_refresh_job(db_path: Path, job_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        row = _refresh_job_row(conn, job_id)
        if row is None:
            raise ValueError(f"Unknown refresh job: {job_id}")
        row["stages"] = _json_loads(row["stages_json"], [])
        row["options"] = _json_loads(row["options_json"], {})
        row["result"] = _json_loads(row["result_json"], {})
        row["metadata"] = _json_loads(row["metadata_json"], {})
        return row
    finally:
        conn.close()


def _search_row(kind: str, project_id: str, title: str, snippet: str, source: str, score: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "id": _stable_id(kind, project_id, title, snippet, source),
        "kind": kind,
        "project_id": project_id,
        "title": title,
        "snippet": snippet,
        "source": source,
        "score": score,
    }
    if extra:
        payload["metadata"] = extra
    return payload


def _score_text(query: str, *values: Any) -> int:
    haystack = " ".join(str(value).lower() for value in values if value is not None)
    score = 0
    for token in query.lower().split():
        if token and token in haystack:
            score += 5
    return score


def _count_value(value: Any) -> int:
    if isinstance(value, dict) and "count" in value:
        try:
            return int(value["count"])
        except (TypeError, ValueError):
            return 0
    if isinstance(value, list):
        return len(value)
    return 0


def search_command_centre(db_path: Path, query: str, project_ids: list[str] | None = None, limit: int = 20) -> dict[str, Any]:
    query = query.strip()
    if not query:
        return {"query": query, "count": 0, "items": []}
    conn = connect(db_path)
    try:
        selected = _project_ids(project_ids)
        rows: list[dict[str, Any]] = []
        project_filter = ""
        params: list[Any] = []
        if selected:
            placeholders = ", ".join(["?"] * len(selected))
            project_filter = f" AND project_id IN ({placeholders})"
            params.extend(selected)

        project_rows = conn.execute(
            f"""
            SELECT project_id, name, repo_path, manifest_json
            FROM projects
            WHERE (LOWER(project_id) LIKE ? OR LOWER(name) LIKE ? OR LOWER(repo_path) LIKE ? OR LOWER(manifest_json) LIKE ?)
            {project_filter}
            ORDER BY project_id
            """,
            [f"%{query.lower()}%"] * 4 + params,
        ).fetchall()
        for row in project_rows:
            rows.append(
                _search_row(
                    "project",
                    row["project_id"],
                    row["name"],
                    row["repo_path"],
                    "projects",
                    _score_text(query, row["project_id"], row["name"], row["repo_path"], row["manifest_json"]),
                    {"manifest": _json_loads(row["manifest_json"], {})},
                ),
            )

        requirement_rows = conn.execute(
            f"""
            SELECT id, project_id, title, description, source_path, status
            FROM requirements
            WHERE (LOWER(id) LIKE ? OR LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(source_path) LIKE ?)
            {project_filter}
            ORDER BY updated_at DESC, title
            """,
            [f"%{query.lower()}%"] * 4 + params,
        ).fetchall()
        for row in requirement_rows:
            rows.append(
                _search_row(
                    "requirement",
                    row["project_id"],
                    row["title"],
                    row["description"] or row["source_path"],
                    "requirements",
                    _score_text(query, row["id"], row["title"], row["description"], row["source_path"], row["status"]),
                    {"requirement_id": row["id"], "status": row["status"]},
                ),
            )

        work_rows = conn.execute(
            f"""
            SELECT id, project_id, title, why, source, category, priority, status
            FROM work_items
            WHERE (LOWER(id) LIKE ? OR LOWER(title) LIKE ? OR LOWER(why) LIKE ? OR LOWER(source) LIKE ? OR LOWER(category) LIKE ?)
            {project_filter}
            ORDER BY updated_at DESC, priority DESC, title
            """,
            [f"%{query.lower()}%"] * 5 + params,
        ).fetchall()
        for row in work_rows:
            rows.append(
                _search_row(
                    "work_item",
                    row["project_id"],
                    row["title"],
                    row["why"],
                    "work_items",
                    _score_text(query, row["id"], row["title"], row["why"], row["source"], row["category"], row["priority"], row["status"]),
                    {"work_item_id": row["id"], "status": row["status"], "category": row["category"]},
                ),
            )

        decision_rows = conn.execute(
            f"""
            SELECT id, project_id, title, description, decision_type, status
            FROM decision_questions
            WHERE (LOWER(id) LIKE ? OR LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(decision_type) LIKE ?)
            {project_filter}
            ORDER BY updated_at DESC, title
            """,
            [f"%{query.lower()}%"] * 4 + params,
        ).fetchall()
        for row in decision_rows:
            rows.append(
                _search_row(
                    "decision",
                    row["project_id"],
                    row["title"],
                    row["description"],
                    "decision_questions",
                    _score_text(query, row["id"], row["title"], row["description"], row["decision_type"], row["status"]),
                    {"decision_id": row["id"], "status": row["status"], "decision_type": row["decision_type"]},
                ),
            )

        rows.sort(key=lambda item: (-int(item["score"]), item["kind"], item["title"]))
        if not rows:
            ecosystem = search_ecosystem(db_path, query, project_ids=selected, limit=limit, offset=0)
            fallback = ecosystem.get("items", []) if isinstance(ecosystem, dict) else []
            for item in fallback:
                if isinstance(item, dict):
                    rows.append(
                        _search_row(
                            str(item.get("kind") or "ecosystem"),
                            str(item.get("project_id") or ""),
                            str(item.get("title") or item.get("name") or query),
                            str(item.get("summary") or item.get("description") or ""),
                            "ecosystem",
                            int(item.get("score") or 1),
                            item,
                        ),
                    )
        rows = rows[:limit]
        return {"query": query, "count": len(rows), "items": rows}
    finally:
        conn.close()


def load_today_brief(db_path: Path, project_ids: list[str] | None = None, session_key: str = SESSION_KEY) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        session = get_app_session(db_path, session_key)
        selected_ids = _project_ids(project_ids)
        if selected_ids is None:
            selected_id = str(session.get("state", {}).get("selected_project_id") or "")
            if not selected_id:
                registry = project_registry_v2(db_path)
                selected_id = registry["projects"][0]["project_id"] if registry["projects"] else ""
            selected_ids = [selected_id] if selected_id else []
        queue = build_work_queue(db_path, selected_ids)
        registry = project_registry_v2(db_path)
        projects = registry["projects"]
        selected_project = next((row for row in projects if row["project_id"] in selected_ids), projects[0] if projects else None)
        today_projects: list[dict[str, Any]] = []
        for project in projects:
            work_count = sum(1 for item in queue["items"] if item["project_id"] == project["project_id"] and item["status"] not in WORK_ITEM_CLOSED_STATES)
            attention = project.get("attention", [])
            today_projects.append(
                {
                    "project_id": project["project_id"],
                    "name": project["display_name"],
                    "status": project["status"],
                    "health": project["health"],
                    "scan_freshness": "fresh" if project["last_scan_id"] else "unknown",
                    "attention_count": _count_value(attention),
                    "work_item_count": work_count,
                    "last_scan": project["last_scan"],
                    "last_memory_id": project["last_memory_id"],
                    "last_flight_id": project["last_flight_id"],
                },
            )
        highlights = queue["items"][:5]
        portfolio = analyse_portfolio(db_path, project_ids=selected_ids or None)
        return {
            "generated_at": _utcnow(),
            "session": session,
            "selected_project_id": selected_project["project_id"] if selected_project else None,
            "selected_project": selected_project,
            "projects": today_projects,
            "work_queue": queue,
            "highlights": highlights,
            "portfolio_health": portfolio["health"],
            "command_centre_health": command_centre_health(db_path),
        }
    finally:
        conn.close()
