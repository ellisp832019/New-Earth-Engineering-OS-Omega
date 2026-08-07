from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core import (
    api_inventory,
    build_inventory,
    configuration_inventory,
    decision_inventory,
    documentation_inventory,
    feature_inventory,
    git_state_report,
    impact_entity,
    project_summary,
    symbol_inventory,
    test_inventory,
    trace_entity,
    why_entity,
)
from ..db import connect
from ..flight import (
    flight_diff,
    flight_incidents,
    flight_regressions,
    flight_snapshots,
    flight_timeline,
    latest_project_flight,
)
from ..genome import (
    genome_attention,
    genome_domains,
    genome_health,
    genome_risks,
    genome_summary,
    genome_unknowns,
    latest_project_genome,
)
from ..memory import (
    latest_project_memory,
    memory_assumptions,
    memory_contradictions,
    memory_decisions,
    memory_experiments,
    memory_gaps,
    memory_lessons,
    memory_milestones,
    memory_timeline,
)
from .health import project_list, service_health
from .models import ServiceConfig


def _project_exists(db_path: Path, project_id: str) -> bool:
    conn = connect(db_path)
    row = conn.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    return row is not None


def _dependencies_for_project(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT id, source_entity_id, target_entity_id, dependency_type, confidence, evidence_source, parser_source, metadata_json
        FROM dependencies
        WHERE project_id=?
        ORDER BY dependency_type, source_entity_id, target_entity_id, id
        """,
        (project_id,),
    ).fetchall()
    conn.close()
    items = [
        {
            "id": row["id"],
            "source_entity_id": row["source_entity_id"],
            "target_entity_id": row["target_entity_id"],
            "dependency_type": row["dependency_type"],
            "confidence": row["confidence"],
            "evidence_source": row["evidence_source"],
            "parser_source": row["parser_source"],
            "metadata": {"raw": row["metadata_json"]},
        }
        for row in rows
    ]
    return {"project_id": project_id, "count": len(items), "items": items}


def _empty_items(project_id: str) -> dict[str, Any]:
    return {"project_id": project_id, "count": 0, "items": []}


def _project_payload(db_path: Path, project_id: str) -> dict[str, Any]:
    if not _project_exists(db_path, project_id):
        raise ValueError(f"Unknown project: {project_id}")
    genome = latest_project_genome(db_path, project_id)
    memory = latest_project_memory(db_path, project_id)
    flight = latest_project_flight(db_path, project_id)
    return {
        "project": project_summary(db_path, project_id),
        "summary": project_summary(db_path, project_id),
        "genome": genome,
        "health": genome_health(genome) if genome else {},
        "domains": genome_domains(genome) if genome else _empty_items(project_id),
        "features": feature_inventory(db_path, project_id),
        "risks": genome_risks(genome) if genome else _empty_items(project_id),
        "unknowns": genome_unknowns(genome) if genome else _empty_items(project_id),
        "attention": genome_attention(genome) if genome else _empty_items(project_id),
        "symbols": symbol_inventory(db_path, project_id),
        "apis": api_inventory(db_path, project_id),
        "tests": test_inventory(db_path, project_id),
        "documentation": documentation_inventory(db_path, project_id),
        "memory": memory,
        "memory_timeline": memory_timeline(memory) if memory else _empty_items(project_id),
        "decisions": decision_inventory(db_path, project_id),
        "configuration": configuration_inventory(db_path, project_id),
        "dependencies": _dependencies_for_project(db_path, project_id),
        "flight": flight,
        "flight_timeline": flight_timeline(db_path, project_id),
        "flight_snapshots": flight_snapshots(db_path, project_id),
        "flight_incidents": flight_incidents(db_path, project_id),
        "flight_regressions": flight_regressions(db_path, project_id),
        "memory_decisions": memory_decisions(memory) if memory else _empty_items(project_id),
        "memory_assumptions": memory_assumptions(memory) if memory else _empty_items(project_id),
        "memory_experiments": memory_experiments(memory) if memory else _empty_items(project_id),
        "memory_lessons": memory_lessons(memory) if memory else _empty_items(project_id),
        "memory_milestones": memory_milestones(memory) if memory else _empty_items(project_id),
        "memory_gaps": memory_gaps(memory) if memory else _empty_items(project_id),
        "memory_contradictions": memory_contradictions(memory) if memory else _empty_items(project_id),
        "git_state": git_state_report(db_path, project_id),
        "why": why_entity(db_path, project_id),
        "impact": impact_entity(db_path, project_id),
    }


def handle_get(path: str, query: dict[str, list[str]], db_path: Path, config: ServiceConfig) -> tuple[int, dict[str, Any]]:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if not segments:
        return 404, {"error": "not_found"}
    if segments == ["health"]:
        return 200, service_health(db_path, config)
    if segments == ["projects"]:
        return 200, {"projects": project_list(db_path)}
    if segments[0] != "projects" or len(segments) < 2:
        return 404, {"error": "not_found"}

    project_id = segments[1]
    try:
        if len(segments) == 2:
            return 200, _project_payload(db_path, project_id)

        tail = segments[2:]
        if tail == ["summary"]:
            return 200, project_summary(db_path, project_id)
        if tail == ["genome"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, {"project_id": project_id, "genome": genome, "summary": genome_summary(genome) if genome else {}}
        if tail == ["health"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, {"project_id": project_id, "health": genome_health(genome) if genome else {}, "genome": genome}
        if tail == ["domains"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, genome_domains(genome) if genome else _empty_items(project_id)
        if tail == ["features"]:
            return 200, feature_inventory(db_path, project_id)
        if tail == ["risks"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, genome_risks(genome) if genome else _empty_items(project_id)
        if tail == ["unknowns"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, genome_unknowns(genome) if genome else _empty_items(project_id)
        if tail == ["attention"]:
            genome = latest_project_genome(db_path, project_id)
            return 200, genome_attention(genome) if genome else _empty_items(project_id)
        if tail == ["symbols"]:
            return 200, symbol_inventory(db_path, project_id)
        if tail == ["apis"]:
            return 200, api_inventory(db_path, project_id)
        if tail == ["tests"]:
            return 200, test_inventory(db_path, project_id)
        if tail == ["documentation"]:
            return 200, documentation_inventory(db_path, project_id)
        if tail == ["memory"]:
            memory = latest_project_memory(db_path, project_id)
            return 200, {"project_id": project_id, "memory": memory, "summary": memory.get("summary", {}) if memory else {}}
        if tail == ["memory", "timeline"]:
            memory = latest_project_memory(db_path, project_id)
            return 200, memory_timeline(memory) if memory else _empty_items(project_id)
        if tail == ["flight"]:
            return 200, {"project_id": project_id, "flight": latest_project_flight(db_path, project_id)}
        if tail == ["flight", "timeline"]:
            return 200, flight_timeline(db_path, project_id)
        if tail == ["flight", "snapshots"]:
            return 200, flight_snapshots(db_path, project_id)
        if tail == ["flight", "incidents"]:
            return 200, flight_incidents(db_path, project_id)
        if tail == ["flight", "regressions"]:
            return 200, flight_regressions(db_path, project_id)
        if tail == ["flight", "diff"]:
            source_ref = query.get("from", ["latest"])[0]
            target_ref = query.get("to", ["latest"])[0]
            return 200, flight_diff(db_path, project_id, source_ref, target_ref)
        if tail == ["decisions"]:
            return 200, decision_inventory(db_path, project_id)
        if tail == ["configuration"]:
            return 200, configuration_inventory(db_path, project_id)
        if tail == ["dependencies"]:
            return 200, _dependencies_for_project(db_path, project_id)
        if tail == ["build"]:
            return 200, build_inventory(db_path, project_id)
        if tail == ["git"]:
            return 200, git_state_report(db_path, project_id)
        if tail == ["why"]:
            entity_id = query.get("entity", [project_id])[0]
            return 200, why_entity(db_path, entity_id)
        if tail == ["trace"]:
            entity_id = query.get("entity", [project_id])[0]
            return 200, trace_entity(db_path, entity_id)
        if tail == ["impact"]:
            entity_id = query.get("entity", [project_id])[0]
            return 200, impact_entity(db_path, entity_id)
    except ValueError:
        return 404, {"error": "not_found"}

    return 404, {"error": "not_found"}
