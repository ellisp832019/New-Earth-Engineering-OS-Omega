from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 7

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

CREATE TABLE IF NOT EXISTS memory_records (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    genome_id TEXT REFERENCES project_genomes(id) ON DELETE SET NULL,
    memory_schema_version INTEGER NOT NULL,
    memory_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path TEXT,
    source_commit TEXT,
    source_branch TEXT,
    timestamp TEXT NOT NULL,
    effective_date TEXT,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    superseded_by TEXT,
    related_entities_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_records_project_type ON memory_records(project_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_records_project_time ON memory_records(project_id, COALESCE(effective_date, timestamp), created_at);

CREATE TABLE IF NOT EXISTS memory_relationships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL REFERENCES memory_records(id) ON DELETE CASCADE,
    target_record_id TEXT NOT NULL REFERENCES memory_records(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_project_source ON memory_relationships(project_id, source_record_id);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_project_target ON memory_relationships(project_id, target_record_id);

CREATE TABLE IF NOT EXISTS memory_snapshots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    genome_id TEXT NOT NULL REFERENCES project_genomes(id) ON DELETE CASCADE,
    source_commit TEXT,
    source_branch TEXT,
    memory_schema_version INTEGER NOT NULL,
    source_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    memory_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_snapshots_unique ON memory_snapshots(project_id, memory_schema_version, source_fingerprint);
CREATE INDEX IF NOT EXISTS idx_memory_snapshots_created ON memory_snapshots(project_id, created_at);

CREATE TABLE IF NOT EXISTS flight_snapshots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    scan_id TEXT NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    genome_id TEXT REFERENCES project_genomes(id) ON DELETE SET NULL,
    memory_id TEXT REFERENCES memory_snapshots(id) ON DELETE SET NULL,
    source_commit TEXT,
    source_branch TEXT,
    source_ref TEXT,
    flight_schema_version INTEGER NOT NULL,
    source_fingerprint TEXT NOT NULL,
    repository_state_hash TEXT NOT NULL,
    semantic_state_hash TEXT NOT NULL,
    genome_state_hash TEXT NOT NULL,
    memory_state_hash TEXT NOT NULL,
    feature_state_hash TEXT NOT NULL,
    test_state_hash TEXT NOT NULL,
    api_state_hash TEXT NOT NULL,
    configuration_state_hash TEXT NOT NULL,
    risk_state_hash TEXT NOT NULL,
    unknown_state_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    state_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_flight_snapshots_unique ON flight_snapshots(project_id, flight_schema_version, source_fingerprint);
CREATE INDEX IF NOT EXISTS idx_flight_snapshots_created ON flight_snapshots(project_id, created_at);

CREATE TABLE IF NOT EXISTS flight_checkpoints (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    checkpoint_type TEXT NOT NULL,
    label TEXT NOT NULL,
    source_ref TEXT,
    source_commit TEXT,
    source_branch TEXT,
    scan_id TEXT REFERENCES scans(scan_id) ON DELETE SET NULL,
    genome_id TEXT REFERENCES project_genomes(id) ON DELETE SET NULL,
    memory_id TEXT REFERENCES memory_snapshots(id) ON DELETE SET NULL,
    snapshot_id TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_checkpoints_project_time ON flight_checkpoints(project_id, timestamp);

CREATE TABLE IF NOT EXISTS flight_events (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    target_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    affected_entities_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_events_project_time ON flight_events(project_id, timestamp);

CREATE TABLE IF NOT EXISTS flight_transitions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    target_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    confidence REAL NOT NULL,
    summary_json TEXT NOT NULL,
    transition_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_transitions_project_time ON flight_transitions(project_id, timestamp);

CREATE TABLE IF NOT EXISTS flight_regressions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    indicator_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    target_snapshot TEXT NOT NULL REFERENCES flight_snapshots(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    affected_entities_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_regressions_project_time ON flight_regressions(project_id, timestamp);

CREATE TABLE IF NOT EXISTS flight_incidents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    type TEXT NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL,
    affected_entities_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT,
    related_decisions_json TEXT NOT NULL,
    related_commits_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_incidents_project_time ON flight_incidents(project_id, timestamp);

CREATE TABLE IF NOT EXISTS ai_settings (
    settings_id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    timeout_seconds INTEGER NOT NULL,
    context_budget INTEGER NOT NULL,
    max_output_tokens INTEGER NOT NULL,
    streaming INTEGER NOT NULL,
    temperature REAL NOT NULL,
    enabled INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_project_updated ON ai_conversations(project_id, updated_at);

CREATE TABLE IF NOT EXISTS ai_conversation_turns (
    turn_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES ai_conversations(conversation_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    question TEXT NOT NULL,
    response_json TEXT NOT NULL,
    context_json TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL,
    intent TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    usage_json TEXT NOT NULL,
    safety_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_conversation_turns_conversation_time ON ai_conversation_turns(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS ai_requests (
    request_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    conversation_id TEXT REFERENCES ai_conversations(conversation_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    intent TEXT NOT NULL,
    mode TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL,
    context_json TEXT NOT NULL,
    response_json TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    usage_json TEXT NOT NULL,
    safety_json TEXT NOT NULL,
    tool_audit_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_requests_conversation_time ON ai_requests(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS ai_request_citations (
    citation_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES ai_requests(request_id) ON DELETE CASCADE,
    conversation_id TEXT REFERENCES ai_conversations(conversation_id) ON DELETE SET NULL,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    path TEXT NOT NULL,
    relationship TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    confidence REAL NOT NULL,
    excerpt TEXT NOT NULL,
    title TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_request_citations_request_confidence ON ai_request_citations(request_id, confidence);
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
    if _current_schema_version(conn) < 5 or conn.execute("SELECT 1 FROM migrations WHERE version=5").fetchone() is None:
        _record_migration(
            conn,
            5,
            "Add engineering memory snapshots for deterministic project history and rationale models.",
            applied_at,
        )
    if _current_schema_version(conn) < 6 or conn.execute("SELECT 1 FROM migrations WHERE version=6").fetchone() is None:
        _record_migration(
            conn,
            6,
            "Add engineering flight recorder snapshots, checkpoints, events, transitions, incidents, and regression intelligence.",
            applied_at,
        )
    if _current_schema_version(conn) < 7 or conn.execute("SELECT 1 FROM migrations WHERE version=7").fetchone() is None:
        _record_migration(
            conn,
            7,
            "Add AI settings, conversations, requests, citations, and audit persistence for the NEOS AI Engineering Partner.",
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
