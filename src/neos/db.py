from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 4

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);
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

CREATE TABLE IF NOT EXISTS symbols (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    source_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    content_hash TEXT NOT NULL,
    parser_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    parent_symbol_id TEXT REFERENCES symbols(id),
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_symbols_project_kind ON symbols(project_id, kind);
CREATE INDEX IF NOT EXISTS idx_symbols_project_path ON symbols(project_id, source_path);
CREATE INDEX IF NOT EXISTS idx_symbols_scan ON symbols(scan_id);

CREATE TABLE IF NOT EXISTS symbol_locations (
    id TEXT PRIMARY KEY,
    symbol_id TEXT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    content_hash TEXT NOT NULL,
    parser_source TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_symbol_locations_project_symbol ON symbol_locations(project_id, symbol_id);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_source TEXT NOT NULL,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    parser_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_relationships_project_type ON relationships(project_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(project_id, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(project_id, target_entity_id);

CREATE TABLE IF NOT EXISTS dependencies (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_source TEXT NOT NULL,
    parser_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dependencies_project_source ON dependencies(project_id, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_project_target ON dependencies(project_id, target_entity_id);

CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    introduced_version TEXT,
    removed_version TEXT,
    confidence REAL NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_features_project_status ON features(project_id, status);

CREATE TABLE IF NOT EXISTS feature_evidence (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    content_hash TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feature_evidence_feature ON feature_evidence(feature_id);

CREATE TABLE IF NOT EXISTS feature_relationships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    feature_id TEXT NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    related_feature_id TEXT NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_source TEXT NOT NULL,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    parser_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engineering_decisions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    date TEXT,
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    alternatives TEXT NOT NULL,
    consequences TEXT NOT NULL,
    source_path TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_engineering_decisions_project_status ON engineering_decisions(project_id, status);

CREATE TABLE IF NOT EXISTS decision_evidence (
    id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES engineering_decisions(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    content_hash TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_endpoints (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    method TEXT,
    route TEXT NOT NULL,
    handler TEXT,
    source_path TEXT NOT NULL,
    line INTEGER,
    content_hash TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_project_route ON api_endpoints(project_id, route);

CREATE TABLE IF NOT EXISTS configuration_keys (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    section TEXT,
    source_path TEXT NOT NULL,
    value_type TEXT NOT NULL,
    default_value TEXT,
    content_hash TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_configuration_keys_project_key ON configuration_keys(project_id, key);

CREATE TABLE IF NOT EXISTS impact_findings (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL,
    impact_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    path_json TEXT NOT NULL,
    explanation TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_impact_findings_project_entity ON impact_findings(project_id, entity_id);

CREATE TABLE IF NOT EXISTS project_genomes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    source_commit TEXT,
    source_branch TEXT,
    genome_schema_version INTEGER NOT NULL,
    source_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    genome_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_genomes_unique ON project_genomes(project_id, genome_schema_version, source_fingerprint);
CREATE INDEX IF NOT EXISTS idx_project_genomes_created ON project_genomes(project_id, created_at);
"""


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _record_migration(conn: sqlite3.Connection, version: int, description: str, applied_at: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO migrations(version, applied_at, description)
        VALUES(?,?,?)
        """,
        (version, applied_at, description),
    )


def _current_schema_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if not row:
        return 0
    try:
        return int(str(row["value"]))
    except ValueError:
        return 0


def _migration_status(conn: sqlite3.Connection) -> str:
    current = _current_schema_version(conn)
    return "current" if current >= SCHEMA_VERSION else "pending"


def _migrate(conn: sqlite3.Connection) -> None:
    applied_at = datetime.now(UTC).isoformat()
    _ensure_column(conn, "scans", "git_branch", "TEXT")
    _ensure_column(conn, "scans", "repo_head", "TEXT")
    _ensure_column(conn, "scans", "snapshot_json", "TEXT NOT NULL DEFAULT '{}' ")

    # Ensure schema version 3 migrations are recorded exactly once.
    if _current_schema_version(conn) < 3 or conn.execute("SELECT 1 FROM migrations WHERE version=3").fetchone() is None:
        _record_migration(
            conn,
            3,
            "Add semantic intelligence tables for symbols, features, decisions, API routes, configuration keys, and impact findings.",
            applied_at,
        )
    if _current_schema_version(conn) < 4 or conn.execute("SELECT 1 FROM migrations WHERE version=4").fetchone() is None:
        _record_migration(
            conn,
            4,
            "Add project genome snapshots for deterministic project-wide engineering models.",
            applied_at,
        )
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    return conn


def schema_info(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "database_schema": _current_schema_version(conn),
        "migration_status": _migration_status(conn),
        "migrations": [dict(row) for row in conn.execute("SELECT version, applied_at, description FROM migrations ORDER BY version")],
    }
