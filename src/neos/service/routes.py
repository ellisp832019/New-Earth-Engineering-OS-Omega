from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..ai.service import handle_ai_get, handle_ai_post
from ..command_centre import (
    acknowledge_work_item,
    defer_work_item,
    dismiss_work_item,
    get_app_session,
    load_refresh_job,
    load_today_brief,
    load_work_item,
    load_work_queue,
    refresh_project_intelligence,
    resolve_work_item,
    search_command_centre,
    set_app_session,
)
from ..core import (
    api_inventory,
    build_inventory,
    configuration_inventory,
    decision_inventory,
    documentation_inventory,
    feature_inventory,
    firmware_impact,
    firmware_inventory,
    git_state_report,
    hardware_inventory,
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
from ..governance import (
    governance_findings,
    governance_project,
    governance_report,
    governance_snapshot,
    governance_status,
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
from ..registry import architecture_impact, architecture_registry, architecture_registry_inventory
from ..requirements_intelligence import (
    architecture_without_requirement,
    build_requirement_intelligence,
    confirm_requirement,
    defer_requirement,
    reject_requirement,
    requirement_gaps,
    requirement_history,
    requirement_inventory,
    requirement_show,
    requirement_trace,
    unimplemented_requirements,
    untested_requirements,
    verification_readiness,
)
from ..workspace import workspace_context, workspace_inventory, workspace_section
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


def _query_project_ids(query: dict[str, list[str]]) -> list[str] | None:
    values = _query_values(query, "project_id")
    return values or None


def _query_governance_estate_roots(query: dict[str, list[str]]) -> list[str] | None:
    roots = [item for item in query.get("estate_root", []) if item]
    return roots or None


def _query_platform_core_root(query: dict[str, list[str]]) -> str | None:
    value = query.get("platform_core_root", [""])[0].strip()
    return value or None


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
    registry = architecture_registry(db_path, project_id)
    workspace = workspace_context(db_path, project_id)
    return {
        "project": project_summary(db_path, project_id),
        "summary": project_summary(db_path, project_id),
        "registry": registry,
        "workspace": workspace,
        "identity": registry["identity"],
        "contracts": registry["contracts"],
        "drift": registry["drift"],
        "impact_analysis": registry["impact"],
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
        "hardware": hardware_inventory(db_path, project_id),
        "firmware": firmware_inventory(db_path, project_id),
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
        "requirements": requirement_inventory(db_path, [project_id]),
        "requirement_gaps": requirement_gaps(db_path, [project_id]),
        "requirement_verification": verification_readiness(db_path, [project_id]),
        "requirement_architecture_gaps": architecture_without_requirement(db_path, [project_id]),
        "requirement_unimplemented": unimplemented_requirements(db_path, [project_id]),
        "requirement_untested": untested_requirements(db_path, [project_id]),
        "requirement_history": requirement_history(db_path, [project_id]),
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
    if segments == ["today"]:
        return 200, load_today_brief(db_path, project_ids=_query_project_ids(query))
    if segments == ["work"]:
        include_closed = query.get("include_closed", ["false"])[0].lower() in {"1", "true", "yes", "on"}
        return 200, load_work_queue(db_path, project_ids=_query_project_ids(query), include_closed=include_closed)
    if segments == ["search"]:
        query_text = query.get("q", [""])[0].strip()
        limit = int(query.get("limit", ["20"])[0] or 20)
        return 200, search_command_centre(db_path, query_text, project_ids=_query_project_ids(query), limit=limit)
    if segments == ["session"]:
        session_key = query.get("session_key", ["workspace"])[0] or "workspace"
        return 200, get_app_session(db_path, session_key=session_key)
    if segments and segments[0] == "hardware" and len(segments) >= 2:
        project_id = segments[1]
        try:
            hardware = hardware_inventory(db_path, project_id)
        except ValueError:
            return 404, {"error": "not_found"}
        if len(segments) == 2:
            return 200, hardware
        tail = segments[2:]
        if tail == ["boards"]:
            return 200, {"project_id": project_id, **hardware, "boards": hardware.get("boards", [])}
        if tail == ["components"]:
            return 200, {"project_id": project_id, **hardware, "components": hardware.get("components", [])}
        if tail == ["bom"]:
            return 200, {"project_id": project_id, **hardware, "component_instances": hardware.get("component_instances", [])}
        if tail == ["pins"]:
            return 200, {"project_id": project_id, **hardware, "pins": hardware.get("pins", [])}
        if tail == ["validation"]:
            return 200, {"project_id": project_id, **hardware, "validations": hardware.get("validations", [])}
        if tail == ["gaps"]:
            return 200, {"project_id": project_id, **hardware, "gaps": hardware.get("gaps", [])}
        if tail == ["risks"]:
            return 200, {"project_id": project_id, **hardware, "risks": hardware.get("risks", [])}
        if tail == ["history"]:
            return 200, {"project_id": project_id, "history": {"latest_snapshot": hardware.get("summary", {}), "validation_state": hardware.get("validation_state", "unknown")}}
        if len(tail) == 2 and tail[0] == "impact":
            entity_id = tail[1]
            matches = [item for item in hardware.get("boards", []) if entity_id in json.dumps(item, sort_keys=True)]
            matches.extend(item for item in hardware.get("components", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in hardware.get("component_instances", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in hardware.get("pins", []) if entity_id in json.dumps(item, sort_keys=True))
            return 200, {"entity_id": entity_id, "count": len(matches), "items": matches, "summary": hardware.get("summary", {})}
    if segments and segments[0] == "firmware" and len(segments) >= 2:
        project_id = segments[1]
        try:
            firmware = firmware_inventory(db_path, project_id)
        except ValueError:
            return 404, {"error": "not_found"}
        if len(segments) == 2:
            return 200, firmware
        tail = segments[2:]
        if tail == ["targets"]:
            return 200, {"project_id": project_id, **firmware, "targets": firmware.get("targets", [])}
        if tail == ["environments"]:
            return 200, {"project_id": project_id, **firmware, "environments": firmware.get("environments", [])}
        if tail == ["modules"]:
            return 200, {"project_id": project_id, **firmware, "modules": firmware.get("modules", [])}
        if tail == ["tasks"]:
            return 200, {"project_id": project_id, **firmware, "tasks": firmware.get("tasks", [])}
        if tail == ["interrupts"]:
            return 200, {"project_id": project_id, **firmware, "interrupts": firmware.get("interrupts", [])}
        if tail == ["timers"]:
            return 200, {"project_id": project_id, **firmware, "timers": firmware.get("timers", [])}
        if tail == ["state-machines"]:
            return 200, {"project_id": project_id, **firmware, "state_machines": firmware.get("state_machines", [])}
        if tail == ["peripherals"]:
            return 200, {"project_id": project_id, **firmware, "peripherals": firmware.get("peripherals", [])}
        if tail == ["gpio"]:
            return 200, {"project_id": project_id, **firmware, "gpio": firmware.get("gpio", [])}
        if tail == ["protocols"]:
            return 200, {"project_id": project_id, **firmware, "protocols": firmware.get("protocols", [])}
        if tail == ["memory"]:
            return 200, {"project_id": project_id, **firmware, "memory_findings": firmware.get("memory_findings", [])}
        if tail == ["validation"]:
            return 200, {"project_id": project_id, **firmware, "validations": firmware.get("validations", [])}
        if tail == ["compatibility"]:
            return 200, {"project_id": project_id, **firmware, "compatibility": firmware.get("compatibility", [])}
        if tail == ["gaps"]:
            return 200, {"project_id": project_id, **firmware, "gaps": firmware.get("gaps", [])}
        if tail == ["risks"]:
            return 200, {"project_id": project_id, **firmware, "risks": firmware.get("risks", [])}
        if tail == ["history"]:
            return 200, {"project_id": project_id, "history": {"latest_snapshot": firmware.get("summary", {}), "compatibility_state": firmware.get("summary", {}).get("compatibility_state", "unknown")}}
        if len(tail) == 2 and tail[0] == "impact":
            entity_id = tail[1]
            matches = [item for item in firmware.get("environments", []) if entity_id in json.dumps(item, sort_keys=True)]
            matches.extend(item for item in firmware.get("targets", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("modules", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("tasks", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("interrupts", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("timers", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("state_machines", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("peripherals", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("gpio", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("protocols", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("memory_findings", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("validations", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("compatibility", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in firmware.get("risks", []) if entity_id in json.dumps(item, sort_keys=True))
            return 200, {"entity_id": entity_id, "count": len(matches), "items": matches, "summary": firmware.get("summary", {})}
    if len(segments) == 2 and segments[0] == "work":
        try:
            return 200, load_work_item(db_path, segments[1])
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 2 and segments[0] == "refresh":
        try:
            return 200, load_refresh_job(db_path, segments[1])
        except ValueError:
            return 404, {"error": "not_found"}
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
    if segments[:2] == ["requirements", "intelligence"] and len(segments) == 2:
        project_ids = _query_values(query, "project_id")
        return 200, build_requirement_intelligence(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "build"]:
        project_ids = _query_values(query, "project_id")
        return 200, build_requirement_intelligence(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "inventory"]:
        project_ids = _query_values(query, "project_id")
        return 200, requirement_inventory(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "gaps"]:
        project_ids = _query_values(query, "project_id")
        return 200, requirement_gaps(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "verification-readiness"]:
        project_ids = _query_values(query, "project_id")
        return 200, verification_readiness(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "architecture-without-requirement"]:
        project_ids = _query_values(query, "project_id")
        return 200, architecture_without_requirement(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "unimplemented"]:
        project_ids = _query_values(query, "project_id")
        return 200, unimplemented_requirements(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "untested"]:
        project_ids = _query_values(query, "project_id")
        return 200, untested_requirements(db_path, project_ids=project_ids or None)
    if segments[:3] == ["requirements", "intelligence", "history"]:
        project_ids = _query_values(query, "project_id")
        return 200, requirement_history(db_path, project_ids=project_ids or None)
    if len(segments) == 4 and segments[:3] == ["requirements", "intelligence", "show"]:
        try:
            return 200, requirement_show(db_path, segments[3])
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 4 and segments[:3] == ["requirements", "intelligence", "trace"]:
        try:
            return 200, requirement_trace(db_path, segments[3])
        except ValueError:
            return 404, {"error": "not_found"}
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
    if segments == ["registry"]:
        return 200, architecture_registry_inventory(db_path)
    if segments == ["governance"]:
        return 200, governance_report(
            db_path,
            platform_core_root=_query_platform_core_root(query),
            estate_roots=_query_governance_estate_roots(query),
        )
    if segments == ["governance", "status"]:
        return 200, governance_status(
            db_path,
            platform_core_root=_query_platform_core_root(query),
            estate_roots=_query_governance_estate_roots(query),
        )
    if segments == ["governance", "findings"]:
        return 200, governance_findings(
            db_path,
            platform_core_root=_query_platform_core_root(query),
            estate_roots=_query_governance_estate_roots(query),
        )
    if segments == ["governance", "snapshot"]:
        return 200, governance_snapshot(
            db_path,
            platform_core_root=_query_platform_core_root(query),
            estate_roots=_query_governance_estate_roots(query),
        )
    if len(segments) == 3 and segments[0] == "governance" and segments[1] == "project":
        return 200, governance_project(
            db_path,
            segments[2],
            platform_core_root=_query_platform_core_root(query),
            estate_roots=_query_governance_estate_roots(query),
        )
    if len(segments) == 2 and segments[0] == "registry":
        try:
            return 200, architecture_registry(db_path, segments[1])
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 3 and segments[0] == "registry" and segments[2] == "drift":
        try:
            return 200, architecture_registry(db_path, segments[1])["drift"]
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 3 and segments[0] == "registry" and segments[2] == "contracts":
        try:
            return 200, architecture_registry(db_path, segments[1])["contracts"]
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 3 and segments[0] == "registry" and segments[2] == "identity":
        try:
            return 200, architecture_registry(db_path, segments[1])["identity"]
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 3 and segments[0] == "registry" and segments[2] == "impact":
        try:
            return 200, architecture_impact(db_path, segments[1])
        except ValueError:
            return 404, {"error": "not_found"}
    if segments == ["workspace"]:
        include_non_first_party = query.get("include_non_first_party", ["false"])[0].lower() in {"1", "true", "yes", "on"}
        return 200, workspace_inventory(
            db_path,
            project_ids=_query_project_ids(query),
            exclude_non_first_party=not include_non_first_party,
        )
    if len(segments) >= 2 and segments[0] == "workspace":
        project_id = segments[1]
        repo_path = query.get("repo_path", [""])[0].strip() or None
        context = workspace_context(db_path, project_id, repo_path=Path(repo_path) if repo_path else None)
        if len(segments) == 2:
            return 200, context
        tail = segments[2:]
        if len(tail) == 1:
            return 200, workspace_section(db_path, project_id, tail[0], repo_path=repo_path)
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
        if tail == ["hardware"]:
            return 200, hardware_inventory(db_path, project_id)
        if tail == ["firmware"]:
            return 200, firmware_inventory(db_path, project_id)
        if tail == ["firmware", "targets"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "targets": firmware.get("targets", [])}
        if tail == ["firmware", "build-variants"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "build_variants": firmware.get("build_variants", [])}
        if tail == ["firmware", "environments"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "environments": firmware.get("environments", [])}
        if tail == ["firmware", "modules"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "modules": firmware.get("modules", [])}
        if tail == ["firmware", "tasks"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "tasks": firmware.get("tasks", [])}
        if tail == ["firmware", "rtos-primitives"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "rtos_primitives": firmware.get("rtos_primitives", [])}
        if tail == ["firmware", "interrupts"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "interrupts": firmware.get("interrupts", [])}
        if tail == ["firmware", "timers"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "timers": firmware.get("timers", [])}
        if tail == ["firmware", "timing"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "timing_facts": firmware.get("timing_facts", [])}
        if tail == ["firmware", "state-machines"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "state_machines": firmware.get("state_machines", [])}
        if tail == ["firmware", "peripherals"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "peripherals": firmware.get("peripherals", [])}
        if tail == ["firmware", "buses"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "buses": firmware.get("buses", [])}
        if tail == ["firmware", "gpio"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "gpio": firmware.get("gpio", [])}
        if tail == ["firmware", "gpio-conflicts"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "gpio_conflicts": firmware.get("gpio_conflicts", [])}
        if tail == ["firmware", "protocols"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "protocols": firmware.get("protocols", [])}
        if tail == ["firmware", "packets"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "packets": firmware.get("packets", [])}
        if tail == ["firmware", "memory"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "memory_findings": firmware.get("memory_findings", [])}
        if tail == ["firmware", "findings"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "findings": firmware.get("findings", [])}
        if tail == ["firmware", "validation"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "validations": firmware.get("validations", [])}
        if tail == ["firmware", "compatibility"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "compatibility": firmware.get("compatibility", [])}
        if tail == ["firmware", "gaps"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "gaps": firmware.get("gaps", [])}
        if tail == ["firmware", "risks"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **firmware, "risks": firmware.get("risks", [])}
        if tail == ["firmware", "history"]:
            firmware = firmware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, "history": {"latest_snapshot": firmware.get("summary", {}), "compatibility_state": firmware.get("summary", {}).get("compatibility_state", "unknown")}}
        if len(tail) == 3 and tail[0] == "firmware" and tail[1] == "impact":
            entity_id = tail[2]
            firmware = firmware_inventory(db_path, project_id)
            impact = firmware_impact(firmware, entity_id)
            return 200, {"entity_id": entity_id, **impact}
        if tail == ["hardware", "boards"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "boards": hardware.get("boards", [])}
        if tail == ["hardware", "components"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "components": hardware.get("components", [])}
        if tail == ["hardware", "bom"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "component_instances": hardware.get("component_instances", [])}
        if tail == ["hardware", "pins"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "pins": hardware.get("pins", [])}
        if tail == ["hardware", "validation"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "validations": hardware.get("validations", [])}
        if tail == ["hardware", "gaps"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "gaps": hardware.get("gaps", [])}
        if tail == ["hardware", "risks"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, **hardware, "risks": hardware.get("risks", [])}
        if tail == ["hardware", "history"]:
            hardware = hardware_inventory(db_path, project_id)
            return 200, {"project_id": project_id, "history": {"latest_snapshot": hardware.get("summary", {}), "validation_state": hardware.get("validation_state", "unknown")}}
        if len(tail) == 2 and tail[0] == "hardware" and tail[1] == "impact":
            entity_id = query.get("entity", [project_id])[0]
            hardware = hardware_inventory(db_path, project_id)
            matches = [item for item in hardware.get("boards", []) if entity_id in json.dumps(item, sort_keys=True)]
            matches.extend(item for item in hardware.get("components", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in hardware.get("component_instances", []) if entity_id in json.dumps(item, sort_keys=True))
            matches.extend(item for item in hardware.get("pins", []) if entity_id in json.dumps(item, sort_keys=True))
            return 200, {"entity_id": entity_id, "count": len(matches), "items": matches, "summary": hardware.get("summary", {})}
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
    if segments == ["session"]:
        state = body.get("state")
        if not isinstance(state, dict):
            state = {key: value for key, value in body.items() if key != "session_key"}
        session_key = str(body.get("session_key") or "workspace")
        return 200, set_app_session(db_path, state, session_key=session_key)
    if len(segments) == 3 and segments[0] == "projects" and segments[2] == "refresh":
        project_id = segments[1]
        options = body if isinstance(body, dict) else {}
        try:
            return 200, refresh_project_intelligence(db_path, project_id, options)
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 3 and segments[0] == "work" and segments[2] in {"acknowledge", "defer", "dismiss", "resolve"}:
        try:
            operator = str(body.get("operator") or "operator")
            notes = str(body.get("notes") or "")
            if segments[2] == "acknowledge":
                return 200, acknowledge_work_item(db_path, segments[1], operator=operator, notes=notes)
            if segments[2] == "defer":
                return 200, defer_work_item(db_path, segments[1], operator=operator, notes=notes)
            if segments[2] == "dismiss":
                return 200, dismiss_work_item(db_path, segments[1], operator=operator, notes=notes)
            return 200, resolve_work_item(db_path, segments[1], operator=operator, notes=notes)
        except ValueError:
            return 404, {"error": "not_found"}
    if segments[:3] == ["decisions", "intelligence", "evaluate"]:
        decision_type = str(body.get("decision_type") or "engineering_next_action").strip() or "engineering_next_action"
        title = str(body.get("title") or "Decision evaluation").strip() or "Decision evaluation"
        description = str(body.get("description") or "").strip()
        raw_options: Any = body.get("options")
        constraints = body.get("constraints")
        related_entities = body.get("related_entities")
        project_ids = _body_project_ids(body, query)
        if raw_options is not None and not isinstance(raw_options, list):
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
            options=raw_options,
            constraints=[str(item) for item in constraints] if isinstance(constraints, list) else None,
            related_entities=[str(item) for item in related_entities] if isinstance(related_entities, list) else None,
        )
        return 200, result
    if segments[:3] == ["decisions", "intelligence", "compare"]:
        question = str(body.get("question") or "Option comparison").strip()
        decision_type = str(body.get("decision_type") or "architecture").strip() or "architecture"
        compare_options_payload: Any = body.get("options")
        if not isinstance(compare_options_payload, list) or not compare_options_payload:
            return 400, {"error": "invalid_options"}
        project_ids = _body_project_ids(body, query)
        return 200, compare_options(
            db_path,
            question,
            decision_type,
            compare_options_payload,
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
    if len(segments) == 4 and segments[:3] == ["requirements", "intelligence", "confirm"]:
        try:
            return 200, confirm_requirement(
                db_path,
                segments[3],
                operator=str(body.get("operator") or "operator"),
                notes=str(body.get("notes") or ""),
            )
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 4 and segments[:3] == ["requirements", "intelligence", "reject"]:
        try:
            return 200, reject_requirement(
                db_path,
                segments[3],
                operator=str(body.get("operator") or "operator"),
                notes=str(body.get("notes") or ""),
            )
        except ValueError:
            return 404, {"error": "not_found"}
    if len(segments) == 4 and segments[:3] == ["requirements", "intelligence", "defer"]:
        try:
            return 200, defer_requirement(
                db_path,
                segments[3],
                operator=str(body.get("operator") or "operator"),
                notes=str(body.get("notes") or ""),
            )
        except ValueError:
            return 404, {"error": "not_found"}
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
