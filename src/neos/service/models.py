from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ServiceConfig:
    db_path: Path
    host: str = "127.0.0.1"
    port: int = 8765
    api_version: str = "v1"
    service_name: str = "NEOS Local Service"
    service_version: str = "1.1.0"
    instance_id: str = ""
    owner_pid: int | None = None
    shutdown_token: str = ""
    started_at: str = ""


@dataclass(frozen=True)
class ServiceProject:
    project_id: str
    name: str
    repo_path: str
    branch: str | None
    commit: str | None
    scan_id: str | None
    scan_freshness: str
    last_analysis_time: str | None
    health: dict[str, Any]
    genome_status: str
    memory_status: str
    flight_status: str
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceState:
    service: dict[str, Any]
    projects: list[ServiceProject]

