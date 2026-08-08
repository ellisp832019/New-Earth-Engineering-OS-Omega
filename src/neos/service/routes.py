from __future__ import annotations

from pathlib import Path
from typing import Any

from ..ai.service import handle_ai_get, handle_ai_post
from ..core import (
    api_inventory,
    build_inventory,
    configuration_inventory,
    decision_inventory,
    documentation_inventory,
    feature_inventory,
    git_state_report,
    impact_entity,
    init_project,
    project_summary,
    scan_project,
    symbol_inventory,
    test_inventory,
    trace_entity,
    why_entity,
)
from ..db import connect
from ..decision_intelligence import (
    accept_decision,
    compare_options,
    decision_history,
    defer_decision,
    evaluate_decision_question,
    get_next_actions,
    get_release_readiness,
    reject_decision,
    review_reuse_candidate,
    run_scenario_analysis,
)
from ..ecosystem import (
    analyse_portfolio,
    ecosystem_diff,
    ecosystem_timeline,
    ecosystem_trace,
    latest_portfolio_snapshot,
    search_ecosystem,
)
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


def _query_values(query: dict[str, list[str]], key: str) -> list[str]:
    return [item for item in query.get(key, []) if item]


def _body_project_ids(body: dict[str, Any], query: dict[str, list[str]]) -> list[str] | None:
    raw = body.get("project_ids")
    if raw is None:
        raw = query.get("project_ids", [])
    if isinstance(raw, list):
        values = [str(item).strip() for item in raw if str(item).strip()]
        return values or None
    return None


def _project_repo_path(db_path: Path, project_id: str) -> Path:
    conn = connect(db_path)
    row = conn.execute("SELECT repo_path FROM projects WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    if row is None:
        raise ValueError(f"Unknown project: {project_id}")
    return Path(row["repo_path"])


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
    if segments[0] == "ai":
        return handle_ai_get(path, query, db_path, config)
    if segments[:3] == ["decisions", "intelligence", "inbox"]:
        project_ids = _query_values(query, "project_id")
        history = decision_history(db_path, project_ids=project_ids or None)
        pending = [item for item in history["items"] if item.get("question", {}).get("status") in {"draft", "review_pending"}]
        return 200, {"count": len(pending), "items": pending, "history_count": history["count"]}
    if segments[:3] == ["decisions", "intelligence", "next-actions"]:
        project_ids = _query_values(query, "project_id")
        return 200, get_next_actions(db_path, project_ids=project_ids or None)
    if segments[:3] == ["decisions", "intelligence", "release-readiness"]:
        project_id = query.get("project_id", [""])[0].strip()
        if not project_id:
            return 400, {"error": "missing_project_id"}
        return 200, get_release_readiness(db_path, project_id)
    if segments[:3] == ["decisions", "intelligence", "reuse"]:
        project_ids = _query_values(query, "project_id")
        return 200, review_reuse_candidate(db_path, project_ids=project_ids or None)
    if segments[:3] == ["decisions", "intelligence", "test-priorities"]:
        project_ids = _query_values(query, "project_id")
        result = evaluate_decision_question(
            db_path,
            "Test priority review",
            "Which tests should be prioritised next?",
            "test_priority",
            project_ids=project_ids or None,
            scope="portfolio" if project_ids else "project",
            source="service-route",
        )
        return 200, result
    if segments[:3] == ["decisions", "intelligence", "debt-priorities"]:
        project_ids = _query_values(query, "project_id")
        result = evaluate_decision_question(
            db_path,
            "Technical debt review",
            "Which technical debt items should be prioritised next?",
            "technical_debt",
            project_ids=project_ids or None,
            scope="portfolio" if project_ids else "project",
            source="service-route",
        )
        return 200, result
    if segments[:3] == ["decisions", "intelligence", "history"]:
        project_ids = _query_values(query, "project_id")
        return 200, decision_history(db_path, project_ids=project_ids or None)
    if segments[0] == "ecosystem":
        if segments == ["ecosystem"]:
            analysis = analyse_portfolio(db_path)
            return 200, analysis
        if segments == ["ecosystem", "projects"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"projects": analysis["projects"], "count": len(analysis["projects"])}
        if segments == ["ecosystem", "capabilities"]:
            analysis = analyse_portfolio(db_path)
            return 200, analysis["capability_matrix"]
        if segments == ["ecosystem", "technologies"]:
            analysis = analyse_portfolio(db_path)
            return 200, analysis["technology_portfolio"]
        if segments == ["ecosystem", "reuse"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["reuse_candidates"]), "items": analysis["reuse_candidates"]}
        if segments == ["ecosystem", "duplication"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["duplicate_findings"]), "items": analysis["duplicate_findings"]}
        if segments == ["ecosystem", "dependencies"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["cross_project_dependencies"]), "items": analysis["cross_project_dependencies"]}
        if segments == ["ecosystem", "risks"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["portfolio_risks"]), "items": analysis["portfolio_risks"]}
        if segments == ["ecosystem", "unknowns"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["unknown_surface"]), "items": analysis["unknown_surface"]}
        if segments == ["ecosystem", "attention"]:
            analysis = analyse_portfolio(db_path)
            return 200, {"count": len(analysis["attention"]), "items": analysis["attention"]}
        if segments == ["ecosystem", "timeline"]:
            return 200, ecosystem_timeline(db_path)
        if segments == ["ecosystem", "search"]:
            query_text = query.get("q", [""])[0].strip()
            limit = int(query.get("limit", ["20"])[0] or 20)
            offset = int(query.get("offset", ["0"])[0] or 0)
            project_ids = [item for item in query.get("project_id", []) if item]
            return 200, search_ecosystem(db_path, query_text, limit=limit, offset=offset, project_ids=project_ids or None)
        if len(segments) == 3 and segments[1] == "trace":
            return 200, ecosystem_trace(db_path, segments[2])
        if len(segments) == 4 and segments[1] == "diff":
            return 200, ecosystem_diff(db_path, segments[2], segments[3])
        if segments == ["ecosystem", "snapshot"]:
            snapshot = latest_portfolio_snapshot(db_path)
            if snapshot is None:
                return 404, {"error": "not_found"}
            return 200, snapshot
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


def handle_post(
    path: str,
    query: dict[str, list[str]],
    body: dict[str, Any],
    db_path: Path,
    config: ServiceConfig,
    server: Any,
) -> tuple[int, dict[str, Any]]:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if segments and segments[0] == "ai":
        return handle_ai_post(path, query, body, db_path, config)
    if segments[:3] == ["decisions", "intelligence", "evaluate"]:
        decision_type = str(body.get("decision_type") or "engineering_next_action").strip() or "engineering_next_action"
        title = str(body.get("title") or "Decision evaluation").strip() or "Decision evaluation"
        description = str(body.get("description") or "").strip()
        options = body.get("options")
        constraints = body.get("constraints")
        related_entities = body.get("related_entities")
        project_ids = _body_project_ids(body, query)
        if options is not None and not isinstance(options, list):
            return 400, {"error": "invalid_options"}
        if constraints is not None and not isinstance(constraints, list):
            return 400, {"error": "invalid_constraints"}
        if related_entities is not None and not isinstance(related_entities, list):
            return 400, {"error": "invalid_related_entities"}
        result = evaluate_decision_question(
            db_path,
            title,
            description,
            decision_type,
            project_id=str(body.get("project_id") or query.get("project_id", [""])[0] or "").strip() or None,
            project_ids=project_ids,
            scope=str(body.get("scope") or ("portfolio" if project_ids else "project")),
            source=str(body.get("source") or "operator"),
            options=options,
            constraints=[str(item) for item in constraints] if isinstance(constraints, list) else None,
            related_entities=[str(item) for item in related_entities] if isinstance(related_entities, list) else None,
        )
        return 200, result
    if segments[:3] == ["decisions", "intelligence", "compare"]:
        question = str(body.get("question") or "Option comparison").strip()
        decision_type = str(body.get("decision_type") or "architecture").strip() or "architecture"
        options = body.get("options")
        if not isinstance(options, list) or not options:
            return 400, {"error": "invalid_options"}
        project_ids = _body_project_ids(body, query)
        return 200, compare_options(
            db_path,
            question,
            decision_type,
            options,
            project_ids=project_ids,
        )
    if segments[:3] == ["decisions", "intelligence", "scenario"]:
        scenario = body.get("scenario")
        if not isinstance(scenario, dict):
            scenario = body
        project_ids = _body_project_ids(body, query)
        return 200, run_scenario_analysis(db_path, scenario, project_ids=project_ids)
    if len(segments) == 4 and segments[:3] == ["decisions", "intelligence", "accept"]:
        return 200, accept_decision(
            db_path,
            segments[3],
            operator=str(body.get("operator") or "operator"),
            selected_option=str(body.get("selected_option") or ""),
            notes=str(body.get("notes") or ""),
        )
    if len(segments) == 4 and segments[:3] == ["decisions", "intelligence", "reject"]:
        return 200, reject_decision(
            db_path,
            segments[3],
            operator=str(body.get("operator") or "operator"),
            selected_option=str(body.get("selected_option") or ""),
            notes=str(body.get("notes") or ""),
        )
    if len(segments) == 4 and segments[:3] == ["decisions", "intelligence", "defer"]:
        return 200, defer_decision(
            db_path,
            segments[3],
            operator=str(body.get("operator") or "operator"),
            selected_option=str(body.get("selected_option") or ""),
            notes=str(body.get("notes") or ""),
        )
    if segments[:2] == ["ecosystem", "build"]:
        raw_project_ids = body.get("project_ids")
        if raw_project_ids is not None and not isinstance(raw_project_ids, list):
            return 400, {"error": "invalid_project_ids"}
        project_ids = [str(item) for item in raw_project_ids] if isinstance(raw_project_ids, list) else None
        raw_name = body.get("name")
        name = raw_name if isinstance(raw_name, str) else "default"
        analysis = analyse_portfolio(db_path, project_ids=project_ids, name=name)
        return 200, analysis
    if segments == ["shutdown"]:
        if body.get("shutdown_token") != config.shutdown_token:
            return 403, {"error": "forbidden"}
        server.shutdown()
        return 200, {"status": "shutting_down", "instance_id": config.instance_id}
    if segments == ["projects", "register"]:
        manifest_path = body.get("manifest_path")
        if not isinstance(manifest_path, str) or not manifest_path.strip():
            return 400, {"error": "missing_manifest_path"}
        project_id = init_project(db_path, Path(manifest_path))
        return 200, {"status": "registered", "project_id": project_id}
    if len(segments) == 3 and segments[0] == "projects" and segments[2] == "scan":
        project_id = segments[1]
        repo_path = body.get("repo_path")
        if isinstance(repo_path, str) and repo_path.strip():
            scan_repo_path = Path(repo_path)
        else:
            scan_repo_path = _project_repo_path(db_path, project_id)
        result = scan_project(db_path, project_id, scan_repo_path)
        return 200, {"status": "scanned", "project_id": project_id, "scan": result}
    return 404, {"error": "not_found"}
