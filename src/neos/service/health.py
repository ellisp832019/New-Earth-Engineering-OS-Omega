from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

from ..db import connect, schema_info
from ..flight import latest_project_flight
from ..genome import latest_project_genome
from ..memory import latest_project_memory
from .models import ServiceConfig


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _project_rows(conn) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM projects ORDER BY name, project_id").fetchall()
    return [dict(row) for row in rows]


def project_list(db_path: Path) -> list[dict[str, Any]]:
    conn = connect(db_path)
    rows = _project_rows(conn)
    projects: list[dict[str, Any]] = []
    for row in rows:
        scan = _latest_scan_row(conn, row["project_id"])
        try:
            genome = latest_project_genome(db_path, row["project_id"])
        except (sqlite3.Error, ValueError, OSError):
            genome = {}
        try:
            memory = latest_project_memory(db_path, row["project_id"])
        except (sqlite3.Error, ValueError, OSError):
            memory = {}
        try:
            flight = latest_project_flight(db_path, row["project_id"])
        except (sqlite3.Error, ValueError, OSError):
            flight = {}
        projects.append(
            {
                "project_id": row["project_id"],
                "name": row["name"],
                "repo_path": row["repo_path"],
                "branch": scan["git_branch"] if scan else None,
                "commit": scan["git_commit"] if scan else None,
                "scan_id": scan["scan_id"] if scan else None,
                "scan_freshness": "fresh" if scan else "unknown",
                "last_analysis_time": scan["created_at"] if scan else None,
                "health": genome.get("project_health", {}),
                "genome_status": "available" if genome else "missing",
                "memory_status": "available" if memory else "missing",
                "flight_status": "available" if flight else "missing",
                "summary": {
                    "last_scan": dict(scan) if scan else None,
                    "genome": genome.get("maturity", {}),
                    "memory": memory.get("summary", {}) if memory else {},
                    "flight": flight.get("metadata", {}) if flight else {},
                },
            }
        )
    conn.close()
    return projects


def service_health(db_path: Path, config: ServiceConfig) -> dict[str, Any]:
    conn = connect(db_path)
    info = schema_info(conn)
    project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    last_scan = conn.execute("SELECT created_at, project_id, scan_id FROM scans ORDER BY created_at DESC, scan_id DESC LIMIT 1").fetchone()
    conn.close()
    return {
        "status": "healthy",
        "service_name": config.service_name,
        "service_version": config.service_version,
        "api_version": config.api_version,
        "schema_version": info["database_schema"],
        "host": config.host,
        "port": config.port,
        "instance_id": config.instance_id,
        "owner_pid": config.owner_pid,
        "started_at": config.started_at,
        "db_path": str(db_path.resolve()),
        "database_size_bytes": db_path.stat().st_size if db_path.exists() else 0,
        "schema": info,
        "registered_projects": project_count,
        "last_scan": dict(last_scan) if last_scan else None,
        "python": sys.version.split()[0],
    }
