from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    lifecycle TEXT,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scans (
    scan_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    repo_path TEXT NOT NULL,
    git_commit TEXT,
    git_branch TEXT,
    repo_head TEXT,
    created_at TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    source_path TEXT,
    content_hash TEXT,
    metadata_json TEXT NOT NULL,
    last_scan_id TEXT REFERENCES scans(scan_id)
);
CREATE INDEX IF NOT EXISTS idx_nodes_project_kind ON nodes(project_id, kind);
CREATE INDEX IF NOT EXISTS idx_nodes_source_path ON nodes(project_id, source_path);
CREATE TABLE IF NOT EXISTS edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    relation TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scan_observations (
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    PRIMARY KEY (scan_id, source_path, kind, label)
);
CREATE INDEX IF NOT EXISTS idx_scan_observations_project_scan ON scan_observations(project_id, scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_observations_source_path ON scan_observations(project_id, source_path);
"""

def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _migrate(conn: sqlite3.Connection) -> None:
    scan_columns = _columns(conn, "scans")
    if "git_branch" not in scan_columns:
        conn.execute("ALTER TABLE scans ADD COLUMN git_branch TEXT")
    if "repo_head" not in scan_columns:
        conn.execute("ALTER TABLE scans ADD COLUMN repo_head TEXT")
    if "snapshot_json" not in scan_columns:
        conn.execute("ALTER TABLE scans ADD COLUMN snapshot_json TEXT NOT NULL DEFAULT '{}' ")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
    conn.commit()
    return conn
