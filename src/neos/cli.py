from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .config import DB_PATH
from .core import (
    api_inventory,
    build_inventory,
    configuration_inventory,
    confirm_feature,
    context_bundle,
    decision_inventory,
    decision_show,
    dependencies_for_entity,
    documentation_inventory,
    feature_inventory,
    feature_show,
    git_state_report,
    impact_entity,
    init_project,
    project_summary,
    scan_diff,
    scan_project,
    stale_scan_status,
    symbol_inventory,
    symbol_show,
    technology_inventory,
    test_inventory,
    trace_entity,
    why_entity,
)
from .db import connect, schema_info
from .flight import (
    build_project_flight,
    create_flight_checkpoint,
    flight_checkpoints,
    flight_diff,
    flight_incidents,
    flight_regressions,
    flight_replay,
    flight_show_snapshot,
    flight_snapshots,
    flight_state,
    flight_timeline,
)
from .genome import (
    build_project_genome,
    genome_attention,
    genome_diff,
    genome_domains,
    genome_health,
    genome_markdown_report,
    genome_risks,
    genome_summary,
    genome_unknowns,
    latest_project_genome,
    render_project_report,
)
from .memory import (
    build_project_memory,
    latest_project_memory,
    memory_assumptions,
    memory_contradictions,
    memory_decisions,
    memory_diff,
    memory_experiments,
    memory_gaps,
    memory_lessons,
    memory_milestones,
    memory_timeline,
    memory_trace_entity,
)
from .service.app import serve_service


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="neos", description="New Earth Engineering OS core CLI")
    p.add_argument("--db", default=str(DB_PATH), help="Path to NEOS SQLite database")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")

    init = sub.add_parser("init-project")
    init.add_argument("--manifest", required=True)
    init.add_argument("--format", choices=("text", "json"), default="json")

    scan = sub.add_parser("scan")
    scan.add_argument("--project-id", required=True)
    scan.add_argument("--repo", required=True)
    scan.add_argument("--format", choices=("text", "json"), default="json")

    summary = sub.add_parser("project-summary")
    summary.add_argument("--project-id", required=True)
    summary.add_argument("--format", choices=("text", "json"), default="text")

    tech = sub.add_parser("technology-inventory")
    tech.add_argument("--project-id", required=True)
    tech.add_argument("--format", choices=("text", "json"), default="text")

    docs = sub.add_parser("documentation-inventory")
    docs.add_argument("--project-id", required=True)
    docs.add_argument("--format", choices=("text", "json"), default="text")

    tests = sub.add_parser("test-inventory")
    tests.add_argument("--project-id", required=True)
    tests.add_argument("--format", choices=("text", "json"), default="text")

    build = sub.add_parser("build-inventory")
    build.add_argument("--project-id", required=True)
    build.add_argument("--format", choices=("text", "json"), default="text")

    diff = sub.add_parser("scan-diff")
    diff.add_argument("--project-id", required=True)
    diff.add_argument("--format", choices=("text", "json"), default="text")

    git = sub.add_parser("git-state")
    git.add_argument("--project-id", required=True)
    git.add_argument("--format", choices=("text", "json"), default="text")

    stale = sub.add_parser("stale-scan-status")
    stale.add_argument("--project-id", required=True)
    stale.add_argument("--format", choices=("text", "json"), default="text")

    context = sub.add_parser("context-bundle")
    context.add_argument("--project-id", required=True)
    context.add_argument("--question", required=True)
    context.add_argument("--format", choices=("text", "json"), default="json")

    symbols = sub.add_parser("symbols")
    symbols.add_argument("--project-id", required=True)
    symbols.add_argument("--format", choices=("text", "json"), default="json")

    symbol = sub.add_parser("symbol")
    symbol_sub = symbol.add_subparsers(dest="symbol_cmd", required=True)
    symbol_show = symbol_sub.add_parser("show")
    symbol_show.add_argument("symbol_id")
    symbol_show.add_argument("--format", choices=("text", "json"), default="json")

    dependencies = sub.add_parser("dependencies")
    dependencies.add_argument("entity_id")
    dependencies.add_argument("--format", choices=("text", "json"), default="json")

    trace = sub.add_parser("trace")
    trace.add_argument("entity_id")
    trace.add_argument("--depth", type=int, default=3)
    trace.add_argument("--relationship")
    trace.add_argument("--direction", choices=("in", "out", "both"), default="both")
    trace.add_argument("--format", choices=("text", "json"), default="json")
    trace.add_argument("--json", action="store_true")

    impact = sub.add_parser("impact")
    impact.add_argument("entity_id")
    impact.add_argument("--depth", type=int, default=2)
    impact.add_argument("--format", choices=("text", "json"), default="json")
    impact.add_argument("--json", action="store_true")

    why = sub.add_parser("why")
    why.add_argument("entity_id")
    why.add_argument("--format", choices=("text", "json"), default="json")
    why.add_argument("--json", action="store_true")

    feature = sub.add_parser("feature")
    feature_sub = feature.add_subparsers(dest="feature_cmd", required=True)
    feature_list = feature_sub.add_parser("list")
    feature_list.add_argument("project_id")
    feature_list.add_argument("--format", choices=("text", "json"), default="json")
    feature_candidates = feature_sub.add_parser("candidates")
    feature_candidates.add_argument("project_id")
    feature_candidates.add_argument("--format", choices=("text", "json"), default="json")
    feature_show = feature_sub.add_parser("show")
    feature_show.add_argument("feature_id")
    feature_show.add_argument("--format", choices=("text", "json"), default="json")
    feature_confirm = feature_sub.add_parser("confirm")
    feature_confirm.add_argument("candidate_id")
    feature_confirm.add_argument("--format", choices=("text", "json"), default="json")

    decision = sub.add_parser("decision")
    decision_sub = decision.add_subparsers(dest="decision_cmd", required=True)
    decision_show = decision_sub.add_parser("show")
    decision_show.add_argument("decision_id")
    decision_show.add_argument("--format", choices=("text", "json"), default="json")
    decisions = sub.add_parser("decisions")
    decisions.add_argument("project_id")
    decisions.add_argument("--entity-id")
    decisions.add_argument("--format", choices=("text", "json"), default="json")

    api = sub.add_parser("api")
    api_sub = api.add_subparsers(dest="api_cmd", required=True)
    api_list = api_sub.add_parser("list")
    api_list.add_argument("project_id")
    api_list.add_argument("--format", choices=("text", "json"), default="json")

    config = sub.add_parser("config")
    config_sub = config.add_subparsers(dest="config_cmd", required=True)
    config_list = config_sub.add_parser("list")
    config_list.add_argument("project_id")
    config_list.add_argument("--format", choices=("text", "json"), default="json")

    genome = sub.add_parser("genome")
    genome_sub = genome.add_subparsers(dest="genome_cmd", required=True)
    genome_build = genome_sub.add_parser("build")
    genome_build.add_argument("project_id")
    genome_build.add_argument("--json", action="store_true")
    genome_show = genome_sub.add_parser("show")
    genome_show.add_argument("project_id")
    genome_show.add_argument("--json", action="store_true")
    genome_summary = genome_sub.add_parser("summary")
    genome_summary.add_argument("project_id")
    genome_summary.add_argument("--json", action="store_true")
    genome_export = genome_sub.add_parser("export")
    genome_export.add_argument("project_id")
    genome_export.add_argument("--json", action="store_true")
    genome_diff = genome_sub.add_parser("diff")
    genome_diff.add_argument("project_id")
    genome_diff.add_argument("--json", action="store_true")
    genome_domains = genome_sub.add_parser("domains")
    genome_domains.add_argument("project_id")
    genome_domains.add_argument("--json", action="store_true")
    genome_risks = genome_sub.add_parser("risks")
    genome_risks.add_argument("project_id")
    genome_risks.add_argument("--json", action="store_true")
    genome_unknowns = genome_sub.add_parser("unknowns")
    genome_unknowns.add_argument("project_id")
    genome_unknowns.add_argument("--json", action="store_true")
    genome_health = genome_sub.add_parser("health")
    genome_health.add_argument("project_id")
    genome_health.add_argument("--json", action="store_true")
    genome_attention = genome_sub.add_parser("attention")
    genome_attention.add_argument("project_id")
    genome_attention.add_argument("--json", action="store_true")

    report = sub.add_parser("report")
    report_sub = report.add_subparsers(dest="report_cmd", required=True)
    report_project = report_sub.add_parser("project")
    report_project.add_argument("project_id")
    report_project.add_argument("--json", action="store_true")

    memory = sub.add_parser("memory")
    memory_sub = memory.add_subparsers(dest="memory_cmd", required=True)
    memory_build = memory_sub.add_parser("build")
    memory_build.add_argument("project_id")
    memory_build.add_argument("--json", action="store_true")
    memory_show = memory_sub.add_parser("show")
    memory_show.add_argument("project_id")
    memory_show.add_argument("--json", action="store_true")
    memory_timeline_parser = memory_sub.add_parser("timeline")
    memory_timeline_parser.add_argument("project_id")
    memory_timeline_parser.add_argument("--type")
    memory_timeline_parser.add_argument("--feature")
    memory_timeline_parser.add_argument("--domain")
    memory_timeline_parser.add_argument("--since")
    memory_timeline_parser.add_argument("--until")
    memory_timeline_parser.add_argument("--json", action="store_true")
    memory_diff_parser = memory_sub.add_parser("diff")
    memory_diff_parser.add_argument("project_id")
    memory_diff_parser.add_argument("--json", action="store_true")
    for name in ("decisions", "assumptions", "experiments", "lessons", "milestones", "gaps", "contradictions"):
        parser = memory_sub.add_parser(name)
        parser.add_argument("project_id")
        parser.add_argument("--json", action="store_true")
    memory_trace_parser = memory_sub.add_parser("trace")
    memory_trace_parser.add_argument("entity_id")
    memory_trace_parser.add_argument("--json", action="store_true")

    flight = sub.add_parser("flight")
    flight_sub = flight.add_subparsers(dest="flight_cmd", required=True)

    flight_checkpoint = flight_sub.add_parser("checkpoint")
    flight_checkpoint_sub = flight_checkpoint.add_subparsers(dest="flight_checkpoint_cmd", required=True)
    flight_checkpoint_create = flight_checkpoint_sub.add_parser("create")
    flight_checkpoint_create.add_argument("project_id")
    flight_checkpoint_create.add_argument("--type", default="manual")
    flight_checkpoint_create.add_argument("--label")
    flight_checkpoint_create.add_argument("--ref")
    flight_checkpoint_create.add_argument("--json", action="store_true")

    flight_checkpoints_parser = flight_sub.add_parser("checkpoints")
    flight_checkpoints_parser.add_argument("project_id")
    flight_checkpoints_parser.add_argument("--json", action="store_true")

    flight_snapshot_parser = flight_sub.add_parser("snapshot")
    flight_snapshot_parser.add_argument("project_id")
    flight_snapshot_parser.add_argument("--ref")
    flight_snapshot_parser.add_argument("--json", action="store_true")

    flight_snapshots_parser = flight_sub.add_parser("snapshots")
    flight_snapshots_parser.add_argument("project_id")
    flight_snapshots_parser.add_argument("--json", action="store_true")

    flight_show_parser = flight_sub.add_parser("show")
    flight_show_parser.add_argument("snapshot_id")
    flight_show_parser.add_argument("--json", action="store_true")

    flight_state_parser = flight_sub.add_parser("state")
    flight_state_parser.add_argument("project_id")
    flight_state_parser.add_argument("--at")
    flight_state_parser.add_argument("--json", action="store_true")

    flight_diff_parser = flight_sub.add_parser("diff")
    flight_diff_parser.add_argument("project_id")
    flight_diff_parser.add_argument("from_ref")
    flight_diff_parser.add_argument("to_ref")
    flight_diff_parser.add_argument("--json", action="store_true")

    flight_timeline_parser = flight_sub.add_parser("timeline")
    flight_timeline_parser.add_argument("project_id")
    flight_timeline_parser.add_argument("--since")
    flight_timeline_parser.add_argument("--until")
    flight_timeline_parser.add_argument("--type")
    flight_timeline_parser.add_argument("--feature")
    flight_timeline_parser.add_argument("--domain")
    flight_timeline_parser.add_argument("--json", action="store_true")

    flight_replay_parser = flight_sub.add_parser("replay")
    flight_replay_parser.add_argument("project_id")
    flight_replay_parser.add_argument("--from", dest="from_ref", required=True)
    flight_replay_parser.add_argument("--to", dest="to_ref", required=True)
    flight_replay_parser.add_argument("--json", action="store_true")

    flight_incidents_parser = flight_sub.add_parser("incidents")
    flight_incidents_parser.add_argument("project_id")
    flight_incidents_parser.add_argument("--json", action="store_true")

    flight_regressions_parser = flight_sub.add_parser("regressions")
    flight_regressions_parser.add_argument("project_id")
    flight_regressions_parser.add_argument("--json", action="store_true")

    service = sub.add_parser("service")
    service_sub = service.add_subparsers(dest="service_cmd", required=True)
    service_start = service_sub.add_parser("start")
    service_start.add_argument("--db", default=str(DB_PATH))
    service_start.add_argument("--host", default="127.0.0.1")
    service_start.add_argument("--port", type=int, default=8765)

    sub.add_parser("version")
    return p


def _render_text(data: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(data, dict):
        lines = []
        for key in sorted(data):
            value = data[key]
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(_render_text(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {value}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(_render_text(item, indent + 2))
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    return f"{pad}{data}"


def _print(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(_render_text(data))


def _genome_or_build(db: Path, project_id: str) -> dict[str, Any]:
    genome = latest_project_genome(db, project_id)
    if genome:
        return genome
    return build_project_genome(db, project_id)["genome"]


def _memory_or_build(db: Path, project_id: str) -> dict[str, Any]:
    memory = latest_project_memory(db, project_id)
    if memory:
        return memory
    return build_project_memory(db, project_id)["memory"]


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    db = Path(args.db)
    try:
        if args.cmd == "doctor":
            conn = connect(db)
            info = schema_info(conn)
            conn.close()
            print(
                json.dumps(
                    {
                        "status": "healthy",
                        "neos_version": __version__,
                        "database_schema": info["database_schema"],
                        "migration_status": info["migration_status"],
                        "python": sys.version.split()[0],
                        "git": shutil.which("git"),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.cmd == "init-project":
            pid = init_project(db, Path(args.manifest))
            _print({"status": "ok", "project_id": pid}, args.format)
            return 0
        if args.cmd == "scan":
            _print(scan_project(db, args.project_id, Path(args.repo)), args.format)
            return 0
        if args.cmd == "project-summary":
            _print(project_summary(db, args.project_id), args.format)
            return 0
        if args.cmd == "technology-inventory":
            _print(technology_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "documentation-inventory":
            _print(documentation_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "test-inventory":
            _print(test_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "build-inventory":
            _print(build_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "scan-diff":
            _print(scan_diff(db, args.project_id), args.format)
            return 0
        if args.cmd == "git-state":
            _print(git_state_report(db, args.project_id), args.format)
            return 0
        if args.cmd == "stale-scan-status":
            _print(stale_scan_status(db, args.project_id), args.format)
            return 0
        if args.cmd == "context-bundle":
            _print(context_bundle(db, args.project_id, args.question), args.format)
            return 0
        if args.cmd == "symbols":
            _print(symbol_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "symbol" and args.symbol_cmd == "show":
            _print(symbol_show(db, args.symbol_id), args.format)
            return 0
        if args.cmd == "dependencies":
            _print(dependencies_for_entity(db, args.entity_id), args.format)
            return 0
        if args.cmd == "trace":
            _print(trace_entity(db, args.entity_id, depth=args.depth, relationship=args.relationship, direction=args.direction), "json" if args.json else args.format)
            return 0
        if args.cmd == "impact":
            _print(impact_entity(db, args.entity_id, depth=args.depth), "json" if args.json else args.format)
            return 0
        if args.cmd == "why":
            _print(why_entity(db, args.entity_id), "json" if args.json else args.format)
            return 0
        if args.cmd == "feature":
            if args.feature_cmd == "list":
                _print(feature_inventory(db, args.project_id, candidates_only=False), args.format)
            elif args.feature_cmd == "candidates":
                _print(feature_inventory(db, args.project_id, candidates_only=True), args.format)
            elif args.feature_cmd == "show":
                _print(feature_show(db, args.feature_id), args.format)
            elif args.feature_cmd == "confirm":
                _print(confirm_feature(db, args.candidate_id), args.format)
            return 0
        if args.cmd == "decision":
            if args.decision_cmd == "show":
                _print(decision_show(db, args.decision_id), args.format)
            return 0
        if args.cmd == "decisions":
            if args.entity_id:
                _print(why_entity(db, args.entity_id), args.format)
            else:
                _print(decision_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "api":
            _print(api_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "config":
            _print(configuration_inventory(db, args.project_id), args.format)
            return 0
        if args.cmd == "genome":
            if args.genome_cmd == "build":
                _print(build_project_genome(db, args.project_id), "json")
            elif args.genome_cmd == "show":
                _print(_genome_or_build(db, args.project_id), "json")
            elif args.genome_cmd == "summary":
                _print(genome_summary(_genome_or_build(db, args.project_id)), "json")
            elif args.genome_cmd == "export":
                _print(_genome_or_build(db, args.project_id), "json")
            elif args.genome_cmd == "diff":
                _print(genome_diff(db, args.project_id), "json")
            elif args.genome_cmd == "domains":
                _print(genome_domains(_genome_or_build(db, args.project_id)), "json")
            elif args.genome_cmd == "risks":
                _print(genome_risks(_genome_or_build(db, args.project_id)), "json")
            elif args.genome_cmd == "unknowns":
                _print(genome_unknowns(_genome_or_build(db, args.project_id)), "json")
            elif args.genome_cmd == "health":
                _print(genome_health(_genome_or_build(db, args.project_id)), "json")
            elif args.genome_cmd == "attention":
                _print(genome_attention(_genome_or_build(db, args.project_id)), "json")
            return 0
        if args.cmd == "report" and args.report_cmd == "project":
            genome = _genome_or_build(db, args.project_id)
            if args.json:
                _print(render_project_report(genome), "json")
            else:
                print(genome_markdown_report(genome), end="")
            return 0
        if args.cmd == "memory":
            if args.memory_cmd == "build":
                _print(build_project_memory(db, args.project_id), "json")
            elif args.memory_cmd == "show":
                _print(_memory_or_build(db, args.project_id), "json")
            elif args.memory_cmd == "timeline":
                memory = _memory_or_build(db, args.project_id)
                _print(
                    memory_timeline(
                        memory,
                        memory_type=args.type,
                        feature=args.feature,
                        domain=args.domain,
                        since=args.since,
                        until=args.until,
                    ),
                    "json" if args.json else "text",
                )
            elif args.memory_cmd == "diff":
                _print(memory_diff(db, args.project_id), "json")
            elif args.memory_cmd == "decisions":
                _print(memory_decisions(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "assumptions":
                _print(memory_assumptions(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "experiments":
                _print(memory_experiments(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "lessons":
                _print(memory_lessons(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "milestones":
                _print(memory_milestones(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "gaps":
                _print(memory_gaps(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "contradictions":
                _print(memory_contradictions(_memory_or_build(db, args.project_id)), "json")
            elif args.memory_cmd == "trace":
                _print(memory_trace_entity(db, args.entity_id), "json")
            return 0
        if args.cmd == "flight":
            if args.flight_cmd == "checkpoint" and args.flight_checkpoint_cmd == "create":
                _print(
                    create_flight_checkpoint(
                        db,
                        args.project_id,
                        checkpoint_type=args.type,
                        label=args.label,
                        source_ref=args.ref,
                    ),
                    "json" if args.json else "text",
                )
            elif args.flight_cmd == "checkpoints":
                _print(flight_checkpoints(db, args.project_id), "json" if args.json else "text")
            elif args.flight_cmd == "snapshot":
                _print(build_project_flight(db, args.project_id, ref=args.ref), "json" if args.json else "text")
            elif args.flight_cmd == "snapshots":
                _print(flight_snapshots(db, args.project_id), "json" if args.json else "text")
            elif args.flight_cmd == "show":
                _print(flight_show_snapshot(db, args.snapshot_id), "json" if args.json else "text")
            elif args.flight_cmd == "state":
                _print(flight_state(db, args.project_id, at=args.at), "json" if args.json else "text")
            elif args.flight_cmd == "diff":
                _print(flight_diff(db, args.project_id, args.from_ref, args.to_ref), "json" if args.json else "text")
            elif args.flight_cmd == "timeline":
                _print(
                    flight_timeline(
                        db,
                        args.project_id,
                        event_type=args.type,
                        feature=args.feature,
                        domain=args.domain,
                        since=args.since,
                        until=args.until,
                    ),
                    "json" if args.json else "text",
                )
            elif args.flight_cmd == "replay":
                _print(flight_replay(db, args.project_id, args.from_ref, args.to_ref), "json" if args.json else "text")
            elif args.flight_cmd == "incidents":
                _print(flight_incidents(db, args.project_id), "json" if args.json else "text")
            elif args.flight_cmd == "regressions":
                _print(flight_regressions(db, args.project_id), "json" if args.json else "text")
            return 0
        if args.cmd == "service":
            if args.service_cmd == "start":
                serve_service(Path(args.db), host=args.host, port=args.port)
            return 0
        if args.cmd == "version":
            print(__version__)
            return 0
    except (ValueError, FileNotFoundError, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1
