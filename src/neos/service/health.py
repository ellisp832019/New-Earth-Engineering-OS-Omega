from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..ai.providers import provider_from_settings
from ..ai.store import load_ai_settings
from ..db import connect, schema_info
from ..ecosystem import analyse_portfolio, project_registry_v2
from .models import ServiceConfig


def project_list(db_path: Path) -> list[dict[str, Any]]:
    registry = project_registry_v2(db_path)
    projects: list[dict[str, Any]] = []
    for row in registry["projects"]:
        projects.append(
            {
                "project_id": row["project_id"],
                "name": row["display_name"],
                "repo_path": row["repository_path"],
                "branch": row["current_branch"],
                "commit": row["current_commit"],
                "scan_id": row["last_scan_id"],
                "scan_freshness": "fresh" if row["last_scan_id"] else "unknown",
                "last_analysis_time": row["last_scan"]["created_at"] if row["last_scan"] else None,
                "health": row["health"],
                "genome_status": "available" if row["last_genome_id"] else "missing",
                "memory_status": "available" if row["last_memory_id"] else "missing",
                "flight_status": "available" if row["last_flight_id"] else "missing",
                "repository_type": row["repository_type"],
                "lifecycle": row["lifecycle"],
                "status": row["status"],
                "tags": row["tags"],
                "family": row["family"],
                "technologies": row["technologies"],
                "summary": {
                    "last_scan": row["last_scan"],
                    "genome": row["health"],
                    "memory": {},
                    "flight": {},
                },
            }
        )
    return projects


def service_health(db_path: Path, config: ServiceConfig) -> dict[str, Any]:
    conn = connect(db_path)
    info = schema_info(conn)
    project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    registry = project_registry_v2(db_path)
    last_scan = conn.execute("SELECT created_at, project_id, scan_id FROM scans ORDER BY created_at DESC, scan_id DESC LIMIT 1").fetchone()
    conn.close()
    ai_settings = load_ai_settings(db_path)
    provider = provider_from_settings(ai_settings)
    provider_health = provider.health().to_dict() if provider is not None else {"configured": False, "healthy": False, "message": "AI provider not configured."}
    portfolio_health = analyse_portfolio(db_path)["health"] if project_count > 1 else {
        "score": 100.0 if project_count else 0.0,
        "project_count": project_count,
        "active_project_count": project_count,
        "dimension_scores": {},
        "explanation": "Portfolio health is calculated when multiple projects are registered.",
    }
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
        "project_registry": registry,
        "portfolio_health": portfolio_health,
        "last_scan": dict(last_scan) if last_scan else None,
        "ai": {
            "settings": ai_settings.to_dict(),
            "provider": provider.info(ai_settings).to_dict() if provider is not None else None,
            "provider_health": provider_health,
        },
        "python": sys.version.split()[0],
    }
