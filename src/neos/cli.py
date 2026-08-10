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
    firmware_build_variants,
    firmware_buses,
    firmware_compatibility,
    firmware_diff,
    firmware_environments,
    firmware_findings,
    firmware_gaps,
    firmware_gpio,
    firmware_gpio_conflicts,
    firmware_impact,
    firmware_interrupts,
    firmware_inventory,
    firmware_memory,
    firmware_modules,
    firmware_packets,
    firmware_peripherals,
    firmware_protocols,
    firmware_risks,
    firmware_rtos_primitives,
    firmware_state_machines,
    firmware_summary,
    firmware_targets,
    firmware_tasks,
    firmware_timers,
    firmware_timing,
    firmware_trace,
    firmware_validation,
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
from .decision_intelligence import (
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
from .ecosystem import (
    analyse_portfolio,
    build_portfolio_snapshot,
    ecosystem_diff,
    ecosystem_timeline,
    ecosystem_trace,
    project_registry_v2,
    render_ecosystem_report,
    search_ecosystem,
)
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
from .governance import (
    governance_findings,
    governance_project,
    governance_report,
    governance_snapshot,
    governance_status,
)
from .hardware import (
    build_hardware_intelligence,
    hardware_boards,
    hardware_bom,
    hardware_components,
    hardware_gaps,
    hardware_impact,
    hardware_pins,
    hardware_risks,
    hardware_summary,
    hardware_trace,
    hardware_validation,
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
from .registry import (
    architecture_impact,
    architecture_registry,
    architecture_registry_inventory,
)
from .requirements_intelligence import (
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
from .service.app import serve_service
from .workspace import workspace_context, workspace_inventory, workspace_section


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
    decision_intel = decision_sub.add_parser("intelligence")
    decision_intel_sub = decision_intel.add_subparsers(dest="decision_intel_cmd", required=True)
    decision_inbox = decision_intel_sub.add_parser("inbox")
    decision_inbox.add_argument("--project-id", action="append")
    decision_inbox.add_argument("--format", choices=("text", "json"), default="json")
    decision_evaluate = decision_intel_sub.add_parser("evaluate")
    decision_evaluate.add_argument("--title", required=True)
    decision_evaluate.add_argument("--description", default="")
    decision_evaluate.add_argument("--decision-type", default="engineering_next_action")
    decision_evaluate.add_argument("--project-id")
    decision_evaluate.add_argument("--project-ids", action="append")
    decision_evaluate.add_argument("--scope", choices=("project", "portfolio"), default="project")
    decision_evaluate.add_argument("--source", default="operator")
    decision_evaluate.add_argument("--format", choices=("text", "json"), default="json")
    decision_compare = decision_intel_sub.add_parser("compare")
    decision_compare.add_argument("--question", required=True)
    decision_compare.add_argument("--decision-type", default="architecture")
    decision_compare.add_argument("--project-id")
    decision_compare.add_argument("--project-ids", action="append")
    decision_compare.add_argument("--options", required=True, help="JSON array of decision options")
    decision_compare.add_argument("--format", choices=("text", "json"), default="json")
    decision_next = decision_intel_sub.add_parser("next-actions")
    decision_next.add_argument("--project-id", action="append")
    decision_next.add_argument("--format", choices=("text", "json"), default="json")
    decision_readiness = decision_intel_sub.add_parser("release-readiness")
    decision_readiness.add_argument("project_id")
    decision_readiness.add_argument("--format", choices=("text", "json"), default="json")
    decision_reuse = decision_intel_sub.add_parser("reuse")
    decision_reuse.add_argument("--project-id", action="append")
    decision_reuse.add_argument("--format", choices=("text", "json"), default="json")
    decision_test = decision_intel_sub.add_parser("test-priorities")
    decision_test.add_argument("--project-id", action="append")
    decision_test.add_argument("--format", choices=("text", "json"), default="json")
    decision_debt = decision_intel_sub.add_parser("debt-priorities")
    decision_debt.add_argument("--project-id", action="append")
    decision_debt.add_argument("--format", choices=("text", "json"), default="json")
    decision_scenario = decision_intel_sub.add_parser("scenario")
    decision_scenario.add_argument("--scenario", required=True, help="JSON object describing the scenario")
    decision_scenario.add_argument("--project-id", action="append")
    decision_scenario.add_argument("--format", choices=("text", "json"), default="json")
    decision_history_cmd = decision_intel_sub.add_parser("history")
    decision_history_cmd.add_argument("--project-id", action="append")
    decision_history_cmd.add_argument("--format", choices=("text", "json"), default="json")
    decision_accept = decision_intel_sub.add_parser("accept")
    decision_accept.add_argument("question_id")
    decision_accept.add_argument("--operator", default="operator")
    decision_accept.add_argument("--selected-option", default="")
    decision_accept.add_argument("--notes", default="")
    decision_accept.add_argument("--format", choices=("text", "json"), default="json")
    decision_reject = decision_intel_sub.add_parser("reject")
    decision_reject.add_argument("question_id")
    decision_reject.add_argument("--operator", default="operator")
    decision_reject.add_argument("--selected-option", default="")
    decision_reject.add_argument("--notes", default="")
    decision_reject.add_argument("--format", choices=("text", "json"), default="json")
    decision_defer = decision_intel_sub.add_parser("defer")
    decision_defer.add_argument("question_id")
    decision_defer.add_argument("--operator", default="operator")
    decision_defer.add_argument("--selected-option", default="")
    decision_defer.add_argument("--notes", default="")
    decision_defer.add_argument("--format", choices=("text", "json"), default="json")

    requirements = sub.add_parser("requirements")
    requirements_sub = requirements.add_subparsers(dest="requirements_cmd", required=True)
    requirements_intel = requirements_sub.add_parser("intelligence")
    requirements_intel_sub = requirements_intel.add_subparsers(dest="requirements_intel_cmd", required=True)
    requirements_build = requirements_intel_sub.add_parser("build")
    requirements_build.add_argument("--project-id", action="append")
    requirements_build.add_argument("--name", default="default")
    requirements_build.add_argument("--format", choices=("text", "json"), default="json")
    requirements_inventory = requirements_intel_sub.add_parser("inventory")
    requirements_inventory.add_argument("--project-id", action="append")
    requirements_inventory.add_argument("--format", choices=("text", "json"), default="json")
    requirements_show = requirements_intel_sub.add_parser("show")
    requirements_show.add_argument("requirement_id")
    requirements_show.add_argument("--format", choices=("text", "json"), default="json")
    requirements_trace = requirements_intel_sub.add_parser("trace")
    requirements_trace.add_argument("requirement_id")
    requirements_trace.add_argument("--format", choices=("text", "json"), default="json")
    requirements_gaps = requirements_intel_sub.add_parser("gaps")
    requirements_gaps.add_argument("--project-id", action="append")
    requirements_gaps.add_argument("--format", choices=("text", "json"), default="json")
    requirements_ready = requirements_intel_sub.add_parser("verification-readiness")
    requirements_ready.add_argument("--project-id", action="append")
    requirements_ready.add_argument("--format", choices=("text", "json"), default="json")
    requirements_arch = requirements_intel_sub.add_parser("architecture-without-requirement")
    requirements_arch.add_argument("--project-id", action="append")
    requirements_arch.add_argument("--format", choices=("text", "json"), default="json")
    requirements_unimplemented = requirements_intel_sub.add_parser("unimplemented")
    requirements_unimplemented.add_argument("--project-id", action="append")
    requirements_unimplemented.add_argument("--format", choices=("text", "json"), default="json")
    requirements_untested = requirements_intel_sub.add_parser("untested")
    requirements_untested.add_argument("--project-id", action="append")
    requirements_untested.add_argument("--format", choices=("text", "json"), default="json")
    requirements_history = requirements_intel_sub.add_parser("history")
    requirements_history.add_argument("--project-id", action="append")
    requirements_history.add_argument("--format", choices=("text", "json"), default="json")
    requirements_confirm = requirements_intel_sub.add_parser("confirm")
    requirements_confirm.add_argument("requirement_id")
    requirements_confirm.add_argument("--operator", default="operator")
    requirements_confirm.add_argument("--notes", default="")
    requirements_confirm.add_argument("--format", choices=("text", "json"), default="json")
    requirements_reject = requirements_intel_sub.add_parser("reject")
    requirements_reject.add_argument("requirement_id")
    requirements_reject.add_argument("--operator", default="operator")
    requirements_reject.add_argument("--notes", default="")
    requirements_reject.add_argument("--format", choices=("text", "json"), default="json")
    requirements_defer = requirements_intel_sub.add_parser("defer")
    requirements_defer.add_argument("requirement_id")
    requirements_defer.add_argument("--operator", default="operator")
    requirements_defer.add_argument("--notes", default="")
    requirements_defer.add_argument("--format", choices=("text", "json"), default="json")

    hardware = sub.add_parser("hardware")
    hardware_sub = hardware.add_subparsers(dest="hardware_cmd", required=True)
    hardware_summary_cmd = hardware_sub.add_parser("summary")
    hardware_summary_cmd.add_argument("project_id")
    hardware_summary_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_boards_cmd = hardware_sub.add_parser("boards")
    hardware_boards_cmd.add_argument("project_id")
    hardware_boards_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_components_cmd = hardware_sub.add_parser("components")
    hardware_components_cmd.add_argument("project_id")
    hardware_components_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_bom_cmd = hardware_sub.add_parser("bom")
    hardware_bom_cmd.add_argument("project_id")
    hardware_bom_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_pins_cmd = hardware_sub.add_parser("pins")
    hardware_pins_cmd.add_argument("project_id")
    hardware_pins_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_validation_cmd = hardware_sub.add_parser("validation")
    hardware_validation_cmd.add_argument("project_id")
    hardware_validation_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_gaps_cmd = hardware_sub.add_parser("gaps")
    hardware_gaps_cmd.add_argument("project_id")
    hardware_gaps_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_risks_cmd = hardware_sub.add_parser("risks")
    hardware_risks_cmd.add_argument("project_id")
    hardware_risks_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_trace_cmd = hardware_sub.add_parser("trace")
    hardware_trace_cmd.add_argument("project_id")
    hardware_trace_cmd.add_argument("entity_id")
    hardware_trace_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_impact_cmd = hardware_sub.add_parser("impact")
    hardware_impact_cmd.add_argument("project_id")
    hardware_impact_cmd.add_argument("entity_id")
    hardware_impact_cmd.add_argument("--format", choices=("text", "json"), default="json")
    hardware_diff_cmd = hardware_sub.add_parser("diff")
    hardware_diff_cmd.add_argument("project_id")
    hardware_diff_cmd.add_argument("--other-project-id")
    hardware_diff_cmd.add_argument("--format", choices=("text", "json"), default="json")

    def _add_output_args(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--format", choices=("text", "json"), default="json")
        command_parser.add_argument("--json", action="store_true")

    firmware = sub.add_parser("firmware")
    firmware_sub = firmware.add_subparsers(dest="firmware_cmd", required=True)
    firmware_summary_cmd = firmware_sub.add_parser("summary")
    firmware_summary_cmd.add_argument("project_id")
    _add_output_args(firmware_summary_cmd)
    firmware_targets_cmd = firmware_sub.add_parser("targets")
    firmware_targets_cmd.add_argument("project_id")
    _add_output_args(firmware_targets_cmd)
    firmware_variants_cmd = firmware_sub.add_parser("build-variants")
    firmware_variants_cmd.add_argument("project_id")
    _add_output_args(firmware_variants_cmd)
    firmware_env_cmd = firmware_sub.add_parser("environments")
    firmware_env_cmd.add_argument("project_id")
    _add_output_args(firmware_env_cmd)
    firmware_modules_cmd = firmware_sub.add_parser("modules")
    firmware_modules_cmd.add_argument("project_id")
    _add_output_args(firmware_modules_cmd)
    firmware_tasks_cmd = firmware_sub.add_parser("tasks")
    firmware_tasks_cmd.add_argument("project_id")
    _add_output_args(firmware_tasks_cmd)
    firmware_rtos_cmd = firmware_sub.add_parser("rtos-primitives")
    firmware_rtos_cmd.add_argument("project_id")
    _add_output_args(firmware_rtos_cmd)
    firmware_interrupts_cmd = firmware_sub.add_parser("interrupts")
    firmware_interrupts_cmd.add_argument("project_id")
    _add_output_args(firmware_interrupts_cmd)
    firmware_timers_cmd = firmware_sub.add_parser("timers")
    firmware_timers_cmd.add_argument("project_id")
    _add_output_args(firmware_timers_cmd)
    firmware_timing_cmd = firmware_sub.add_parser("timing")
    firmware_timing_cmd.add_argument("project_id")
    _add_output_args(firmware_timing_cmd)
    firmware_states_cmd = firmware_sub.add_parser("states")
    firmware_states_cmd.add_argument("project_id")
    _add_output_args(firmware_states_cmd)
    firmware_peripherals_cmd = firmware_sub.add_parser("peripherals")
    firmware_peripherals_cmd.add_argument("project_id")
    _add_output_args(firmware_peripherals_cmd)
    firmware_buses_cmd = firmware_sub.add_parser("buses")
    firmware_buses_cmd.add_argument("project_id")
    _add_output_args(firmware_buses_cmd)
    firmware_gpio_cmd = firmware_sub.add_parser("gpio")
    firmware_gpio_cmd.add_argument("project_id")
    _add_output_args(firmware_gpio_cmd)
    firmware_gpio_conflicts_cmd = firmware_sub.add_parser("gpio-conflicts")
    firmware_gpio_conflicts_cmd.add_argument("project_id")
    _add_output_args(firmware_gpio_conflicts_cmd)
    firmware_protocols_cmd = firmware_sub.add_parser("protocols")
    firmware_protocols_cmd.add_argument("project_id")
    _add_output_args(firmware_protocols_cmd)
    firmware_packets_cmd = firmware_sub.add_parser("packets")
    firmware_packets_cmd.add_argument("project_id")
    _add_output_args(firmware_packets_cmd)
    firmware_memory_cmd = firmware_sub.add_parser("memory")
    firmware_memory_cmd.add_argument("project_id")
    _add_output_args(firmware_memory_cmd)
    firmware_findings_cmd = firmware_sub.add_parser("findings")
    firmware_findings_cmd.add_argument("project_id")
    _add_output_args(firmware_findings_cmd)
    firmware_validation_cmd = firmware_sub.add_parser("validation")
    firmware_validation_cmd.add_argument("project_id")
    _add_output_args(firmware_validation_cmd)
    firmware_compatibility_cmd = firmware_sub.add_parser("compatibility")
    firmware_compatibility_cmd.add_argument("project_id")
    _add_output_args(firmware_compatibility_cmd)
    firmware_gaps_cmd = firmware_sub.add_parser("gaps")
    firmware_gaps_cmd.add_argument("project_id")
    _add_output_args(firmware_gaps_cmd)
    firmware_risks_cmd = firmware_sub.add_parser("risks")
    firmware_risks_cmd.add_argument("project_id")
    _add_output_args(firmware_risks_cmd)
    firmware_trace_cmd = firmware_sub.add_parser("trace")
    firmware_trace_cmd.add_argument("project_id")
    firmware_trace_cmd.add_argument("entity_id")
    _add_output_args(firmware_trace_cmd)
    firmware_impact_cmd = firmware_sub.add_parser("impact")
    firmware_impact_cmd.add_argument("project_id")
    firmware_impact_cmd.add_argument("entity_id")
    _add_output_args(firmware_impact_cmd)
    firmware_diff_cmd = firmware_sub.add_parser("diff")
    firmware_diff_cmd.add_argument("project_id")
    firmware_diff_cmd.add_argument("--other-project-id")
    _add_output_args(firmware_diff_cmd)

    registry = sub.add_parser("registry")
    registry_sub = registry.add_subparsers(dest="registry_cmd", required=True)
    registry_inventory = registry_sub.add_parser("inventory")
    registry_inventory.add_argument("--format", choices=("text", "json"), default="json")
    registry_inventory.add_argument("--json", action="store_true")
    registry_show = registry_sub.add_parser("show")
    registry_show.add_argument("project_id")
    registry_show.add_argument("--format", choices=("text", "json"), default="json")
    registry_show.add_argument("--json", action="store_true")
    registry_drift = registry_sub.add_parser("drift")
    registry_drift.add_argument("project_id")
    registry_drift.add_argument("--format", choices=("text", "json"), default="json")
    registry_drift.add_argument("--json", action="store_true")
    registry_impact = registry_sub.add_parser("impact")
    registry_impact.add_argument("project_id")
    registry_impact.add_argument("--peer-project-id")
    registry_impact.add_argument("--peer-repo-path")
    registry_impact.add_argument("--format", choices=("text", "json"), default="json")
    registry_impact.add_argument("--json", action="store_true")

    workspace = sub.add_parser("workspace")
    workspace_sub = workspace.add_subparsers(dest="workspace_cmd", required=True)
    workspace_inventory = workspace_sub.add_parser("inventory")
    workspace_inventory.add_argument("--project-id", action="append")
    workspace_inventory.add_argument("--include-non-first-party", action="store_true")
    workspace_inventory.add_argument("--json", action="store_true")
    workspace_show = workspace_sub.add_parser("show")
    workspace_show.add_argument("project_id")
    workspace_show.add_argument("--repo-path")
    workspace_show.add_argument("--json", action="store_true")
    workspace_summary = workspace_sub.add_parser("summary")
    workspace_summary.add_argument("project_id")
    workspace_summary.add_argument("--repo-path")
    workspace_summary.add_argument("--json", action="store_true")
    workspace_classification = workspace_sub.add_parser("classification")
    workspace_classification.add_argument("project_id")
    workspace_classification.add_argument("--repo-path")
    workspace_classification.add_argument("--json", action="store_true")
    workspace_integration = workspace_sub.add_parser("integration")
    workspace_integration.add_argument("project_id")
    workspace_integration.add_argument("--repo-path")
    workspace_integration.add_argument("--json", action="store_true")
    workspace_contracts = workspace_sub.add_parser("contracts")
    workspace_contracts.add_argument("project_id")
    workspace_contracts.add_argument("--repo-path")
    workspace_contracts.add_argument("--json", action="store_true")
    workspace_dependencies = workspace_sub.add_parser("dependencies")
    workspace_dependencies.add_argument("project_id")
    workspace_dependencies.add_argument("--repo-path")
    workspace_dependencies.add_argument("--json", action="store_true")
    workspace_evidence = workspace_sub.add_parser("evidence")
    workspace_evidence.add_argument("project_id")
    workspace_evidence.add_argument("--repo-path")
    workspace_evidence.add_argument("--json", action="store_true")
    workspace_drift = workspace_sub.add_parser("drift")
    workspace_drift.add_argument("project_id")
    workspace_drift.add_argument("--repo-path")
    workspace_drift.add_argument("--json", action="store_true")
    workspace_impact = workspace_sub.add_parser("impact")
    workspace_impact.add_argument("project_id")
    workspace_impact.add_argument("--repo-path")
    workspace_impact.add_argument("--json", action="store_true")
    workspace_freshness = workspace_sub.add_parser("freshness")
    workspace_freshness.add_argument("project_id")
    workspace_freshness.add_argument("--repo-path")
    workspace_freshness.add_argument("--json", action="store_true")
    workspace_provenance = workspace_sub.add_parser("provenance")
    workspace_provenance.add_argument("project_id")
    workspace_provenance.add_argument("--repo-path")
    workspace_provenance.add_argument("--json", action="store_true")
    workspace_release = workspace_sub.add_parser("release")
    workspace_release.add_argument("project_id")
    workspace_release.add_argument("--repo-path")
    workspace_release.add_argument("--json", action="store_true")
    workspace_safety = workspace_sub.add_parser("safety")
    workspace_safety.add_argument("project_id")
    workspace_safety.add_argument("--repo-path")
    workspace_safety.add_argument("--json", action="store_true")

    governance = sub.add_parser("governance")
    governance_sub = governance.add_subparsers(dest="governance_cmd", required=True)

    def _governance_args(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--platform-core-root")
        command_parser.add_argument("--estate-root", action="append")
        command_parser.add_argument("--json", action="store_true")

    governance_status_cmd = governance_sub.add_parser("status")
    _governance_args(governance_status_cmd)
    governance_findings_cmd = governance_sub.add_parser("findings")
    _governance_args(governance_findings_cmd)
    governance_project_cmd = governance_sub.add_parser("project")
    governance_project_cmd.add_argument("project_id")
    _governance_args(governance_project_cmd)
    governance_report_cmd = governance_sub.add_parser("report")
    _governance_args(governance_report_cmd)
    governance_snapshot_cmd = governance_sub.add_parser("snapshot")
    _governance_args(governance_snapshot_cmd)

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
    report_ecosystem = report_sub.add_parser("ecosystem")
    report_ecosystem.add_argument("--name", default="default")
    report_ecosystem.add_argument("--json", action="store_true")

    ecosystem = sub.add_parser("ecosystem")
    ecosystem_sub = ecosystem.add_subparsers(dest="ecosystem_cmd", required=True)
    ecosystem_build = ecosystem_sub.add_parser("build")
    ecosystem_build.add_argument("--name", default="default")
    ecosystem_build.add_argument("--project-id", action="append")
    ecosystem_build.add_argument("--json", action="store_true")
    ecosystem_summary = ecosystem_sub.add_parser("summary")
    ecosystem_summary.add_argument("--name", default="default")
    ecosystem_summary.add_argument("--project-id", action="append")
    ecosystem_summary.add_argument("--json", action="store_true")
    ecosystem_projects = ecosystem_sub.add_parser("projects")
    ecosystem_projects.add_argument("--json", action="store_true")
    ecosystem_capabilities = ecosystem_sub.add_parser("capabilities")
    ecosystem_capabilities.add_argument("--project-id", action="append")
    ecosystem_capabilities.add_argument("--json", action="store_true")
    ecosystem_technologies = ecosystem_sub.add_parser("technologies")
    ecosystem_technologies.add_argument("--project-id", action="append")
    ecosystem_technologies.add_argument("--json", action="store_true")
    ecosystem_reuse = ecosystem_sub.add_parser("reuse")
    ecosystem_reuse.add_argument("--project-id", action="append")
    ecosystem_reuse.add_argument("--json", action="store_true")
    ecosystem_duplication = ecosystem_sub.add_parser("duplication")
    ecosystem_duplication.add_argument("--project-id", action="append")
    ecosystem_duplication.add_argument("--json", action="store_true")
    ecosystem_dependencies = ecosystem_sub.add_parser("dependencies")
    ecosystem_dependencies.add_argument("--project-id", action="append")
    ecosystem_dependencies.add_argument("--json", action="store_true")
    ecosystem_risks = ecosystem_sub.add_parser("risks")
    ecosystem_risks.add_argument("--project-id", action="append")
    ecosystem_risks.add_argument("--json", action="store_true")
    ecosystem_unknowns = ecosystem_sub.add_parser("unknowns")
    ecosystem_unknowns.add_argument("--project-id", action="append")
    ecosystem_unknowns.add_argument("--json", action="store_true")
    ecosystem_attention = ecosystem_sub.add_parser("attention")
    ecosystem_attention.add_argument("--project-id", action="append")
    ecosystem_attention.add_argument("--json", action="store_true")
    ecosystem_timeline_parser = ecosystem_sub.add_parser("timeline")
    ecosystem_timeline_parser.add_argument("--json", action="store_true")
    ecosystem_diff_parser = ecosystem_sub.add_parser("diff")
    ecosystem_diff_parser.add_argument("from_snapshot_id")
    ecosystem_diff_parser.add_argument("to_snapshot_id")
    ecosystem_diff_parser.add_argument("--json", action="store_true")
    ecosystem_trace_parser = ecosystem_sub.add_parser("trace")
    ecosystem_trace_parser.add_argument("entity_id")
    ecosystem_trace_parser.add_argument("--json", action="store_true")
    ecosystem_search_parser = ecosystem_sub.add_parser("search")
    ecosystem_search_parser.add_argument("query")
    ecosystem_search_parser.add_argument("--project-id", action="append")
    ecosystem_search_parser.add_argument("--limit", type=int, default=20)
    ecosystem_search_parser.add_argument("--offset", type=int, default=0)
    ecosystem_search_parser.add_argument("--json", action="store_true")

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
    service_start.add_argument("--instance-id")
    service_start.add_argument("--owner-pid", type=int)
    service_start.add_argument("--shutdown-token")

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


def _hardware_or_build(db: Path, project_id: str) -> dict[str, Any]:
    return build_hardware_intelligence(db, project_id)


def _firmware_or_build(db: Path, project_id: str) -> dict[str, Any]:
    return firmware_inventory(db, project_id)


def _registry_or_build(db: Path, project_id: str) -> dict[str, Any]:
    return architecture_registry(db, project_id)


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
        if args.cmd == "requirements":
            project_ids = getattr(args, "project_id", None)
            if args.requirements_cmd == "intelligence":
                if args.requirements_intel_cmd == "build":
                    _print(build_requirement_intelligence(db, project_ids=project_ids, name=args.name), args.format)
                elif args.requirements_intel_cmd == "inventory":
                    _print(requirement_inventory(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "show":
                    _print(requirement_show(db, args.requirement_id), args.format)
                elif args.requirements_intel_cmd == "trace":
                    _print(requirement_trace(db, args.requirement_id), args.format)
                elif args.requirements_intel_cmd == "gaps":
                    _print(requirement_gaps(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "verification-readiness":
                    _print(verification_readiness(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "architecture-without-requirement":
                    _print(architecture_without_requirement(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "unimplemented":
                    _print(unimplemented_requirements(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "untested":
                    _print(untested_requirements(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "history":
                    _print(requirement_history(db, project_ids=project_ids), args.format)
                elif args.requirements_intel_cmd == "confirm":
                    _print(confirm_requirement(db, args.requirement_id, operator=args.operator, notes=args.notes), args.format)
                elif args.requirements_intel_cmd == "reject":
                    _print(reject_requirement(db, args.requirement_id, operator=args.operator, notes=args.notes), args.format)
                elif args.requirements_intel_cmd == "defer":
                    _print(defer_requirement(db, args.requirement_id, operator=args.operator, notes=args.notes), args.format)
            return 0
        if args.cmd == "hardware":
            hardware = _hardware_or_build(db, args.project_id)
            if args.hardware_cmd == "summary":
                _print(hardware_summary(hardware), args.format)
            elif args.hardware_cmd == "boards":
                _print(hardware_boards(hardware), args.format)
            elif args.hardware_cmd == "components":
                _print(hardware_components(hardware), args.format)
            elif args.hardware_cmd == "bom":
                _print(hardware_bom(hardware), args.format)
            elif args.hardware_cmd == "pins":
                _print(hardware_pins(hardware), args.format)
            elif args.hardware_cmd == "validation":
                _print(hardware_validation(hardware), args.format)
            elif args.hardware_cmd == "gaps":
                _print(hardware_gaps(hardware), args.format)
            elif args.hardware_cmd == "risks":
                _print(hardware_risks(hardware), args.format)
            elif args.hardware_cmd == "trace":
                _print(hardware_trace(hardware, args.entity_id), args.format)
            elif args.hardware_cmd == "impact":
                _print(hardware_impact(hardware, args.entity_id), args.format)
            elif args.hardware_cmd == "diff":
                other = _hardware_or_build(db, args.other_project_id or args.project_id)
                _print(
                    {
                        "from_project_id": args.project_id,
                        "to_project_id": args.other_project_id or args.project_id,
                        "from_summary": hardware_summary(hardware),
                        "to_summary": hardware_summary(other),
                        "board_count_delta": hardware_summary(other).get("board_count", 0) - hardware_summary(hardware).get("board_count", 0),
                        "component_count_delta": hardware_summary(other).get("component_count", 0) - hardware_summary(hardware).get("component_count", 0),
                        "pin_mapping_count_delta": hardware_summary(other).get("pin_mapping_count", 0) - hardware_summary(hardware).get("pin_mapping_count", 0),
                    },
                    args.format,
                )
            return 0
        if args.cmd == "firmware":
            firmware = _firmware_or_build(db, args.project_id)
            fmt = "json" if getattr(args, "json", False) else args.format
            if args.firmware_cmd == "summary":
                _print(firmware_summary(firmware), fmt)
            elif args.firmware_cmd == "targets":
                _print(firmware_targets(firmware), fmt)
            elif args.firmware_cmd == "build-variants":
                _print(firmware_build_variants(firmware), fmt)
            elif args.firmware_cmd == "environments":
                _print(firmware_environments(firmware), fmt)
            elif args.firmware_cmd == "modules":
                _print(firmware_modules(firmware), fmt)
            elif args.firmware_cmd == "tasks":
                _print(firmware_tasks(firmware), fmt)
            elif args.firmware_cmd == "rtos-primitives":
                _print(firmware_rtos_primitives(firmware), fmt)
            elif args.firmware_cmd == "interrupts":
                _print(firmware_interrupts(firmware), fmt)
            elif args.firmware_cmd == "timers":
                _print(firmware_timers(firmware), fmt)
            elif args.firmware_cmd == "timing":
                _print(firmware_timing(firmware), fmt)
            elif args.firmware_cmd == "states":
                _print(firmware_state_machines(firmware), fmt)
            elif args.firmware_cmd == "peripherals":
                _print(firmware_peripherals(firmware), fmt)
            elif args.firmware_cmd == "buses":
                _print(firmware_buses(firmware), fmt)
            elif args.firmware_cmd == "gpio":
                _print(firmware_gpio(firmware), fmt)
            elif args.firmware_cmd == "gpio-conflicts":
                _print(firmware_gpio_conflicts(firmware), fmt)
            elif args.firmware_cmd == "protocols":
                _print(firmware_protocols(firmware), fmt)
            elif args.firmware_cmd == "packets":
                _print(firmware_packets(firmware), fmt)
            elif args.firmware_cmd == "memory":
                _print(firmware_memory(firmware), fmt)
            elif args.firmware_cmd == "findings":
                _print(firmware_findings(firmware), fmt)
            elif args.firmware_cmd == "validation":
                _print(firmware_validation(firmware), fmt)
            elif args.firmware_cmd == "compatibility":
                _print(firmware_compatibility(firmware), fmt)
            elif args.firmware_cmd == "gaps":
                _print(firmware_gaps(firmware), fmt)
            elif args.firmware_cmd == "risks":
                _print(firmware_risks(firmware), fmt)
            elif args.firmware_cmd == "trace":
                _print(firmware_trace(firmware, args.entity_id), fmt)
            elif args.firmware_cmd == "impact":
                _print(firmware_impact(firmware, args.entity_id), fmt)
            elif args.firmware_cmd == "diff":
                _print(firmware_diff(db, args.project_id, args.other_project_id), fmt)
            return 0
        if args.cmd == "registry":
            fmt = "json" if getattr(args, "json", False) else args.format
            if args.registry_cmd == "inventory":
                _print(architecture_registry_inventory(db), fmt)
            elif args.registry_cmd == "show":
                _print(_registry_or_build(db, args.project_id), fmt)
            elif args.registry_cmd == "drift":
                _print(_registry_or_build(db, args.project_id)["drift"], fmt)
            elif args.registry_cmd == "impact":
                _print(
                    architecture_impact(
                        db,
                        args.project_id,
                        peer_project_id=getattr(args, "peer_project_id", None),
                        peer_repo_path=getattr(args, "peer_repo_path", None),
                    ),
                    fmt,
                )
            return 0
        if args.cmd == "workspace":
            repo_path = Path(args.repo_path).resolve() if getattr(args, "repo_path", None) else None
            if args.workspace_cmd == "inventory":
                _print(
                    workspace_inventory(
                        db,
                        project_ids=getattr(args, "project_id", None),
                        exclude_non_first_party=not args.include_non_first_party,
                    ),
                    "json",
                )
            elif args.workspace_cmd == "show":
                _print(workspace_context(db, args.project_id, repo_path=repo_path), "json")
            elif args.workspace_cmd in {"summary", "classification", "integration", "contracts", "dependencies", "evidence", "drift", "impact", "freshness", "provenance", "release", "safety"}:
                section = workspace_section(db, args.project_id, args.workspace_cmd, repo_path=repo_path)
                _print(section, "json")
            return 0
        if args.cmd == "governance":
            fmt = "json" if getattr(args, "json", False) else "text"
            if args.governance_cmd == "status":
                _print(
                    governance_status(
                        db,
                        platform_core_root=getattr(args, "platform_core_root", None),
                        estate_roots=getattr(args, "estate_root", None),
                    ),
                    fmt,
                )
            elif args.governance_cmd == "findings":
                _print(
                    governance_findings(
                        db,
                        platform_core_root=getattr(args, "platform_core_root", None),
                        estate_roots=getattr(args, "estate_root", None),
                    ),
                    fmt,
                )
            elif args.governance_cmd == "project":
                _print(
                    governance_project(
                        db,
                        args.project_id,
                        platform_core_root=getattr(args, "platform_core_root", None),
                        estate_roots=getattr(args, "estate_root", None),
                    ),
                    fmt,
                )
            elif args.governance_cmd == "report":
                _print(
                    governance_report(
                        db,
                        platform_core_root=getattr(args, "platform_core_root", None),
                        estate_roots=getattr(args, "estate_root", None),
                    ),
                    fmt,
                )
            elif args.governance_cmd == "snapshot":
                _print(
                    governance_snapshot(
                        db,
                        platform_core_root=getattr(args, "platform_core_root", None),
                        estate_roots=getattr(args, "estate_root", None),
                    ),
                    fmt,
                )
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
            elif args.decision_cmd == "intelligence":
                project_ids = getattr(args, "project_ids", None)
                if args.decision_intel_cmd == "inbox":
                    _print(decision_history(db, project_ids=project_ids), args.format)
                elif args.decision_intel_cmd == "evaluate":
                    options = None
                    if getattr(args, "options", None):
                        options = json.loads(args.options)
                    _print(
                        evaluate_decision_question(
                            db,
                            args.title,
                            args.description,
                            args.decision_type,
                            project_id=getattr(args, "project_id", None),
                            project_ids=project_ids,
                            scope=args.scope,
                            source=args.source,
                            options=options,
                        ),
                        args.format,
                    )
                elif args.decision_intel_cmd == "compare":
                    options = json.loads(args.options)
                    _print(
                        compare_options(
                            db,
                            args.question,
                            args.decision_type,
                            options,
                            project_ids=project_ids,
                        ),
                        args.format,
                    )
                elif args.decision_intel_cmd == "next-actions":
                    _print(get_next_actions(db, project_ids=project_ids), args.format)
                elif args.decision_intel_cmd == "release-readiness":
                    _print(get_release_readiness(db, args.project_id), args.format)
                elif args.decision_intel_cmd == "reuse":
                    _print(review_reuse_candidate(db, project_ids=project_ids), args.format)
                elif args.decision_intel_cmd == "test-priorities":
                    _print(
                        evaluate_decision_question(
                            db,
                            "Test priority review",
                            "Which tests should be prioritised next?",
                            "test_priority",
                            project_ids=project_ids,
                            scope="portfolio" if project_ids else "project",
                            source="cli",
                        ),
                        args.format,
                    )
                elif args.decision_intel_cmd == "debt-priorities":
                    _print(
                        evaluate_decision_question(
                            db,
                            "Technical debt review",
                            "Which technical debt items should be prioritised next?",
                            "technical_debt",
                            project_ids=project_ids,
                            scope="portfolio" if project_ids else "project",
                            source="cli",
                        ),
                        args.format,
                    )
                elif args.decision_intel_cmd == "scenario":
                    scenario = json.loads(args.scenario)
                    _print(run_scenario_analysis(db, scenario, project_ids=project_ids), args.format)
                elif args.decision_intel_cmd == "history":
                    _print(decision_history(db, project_ids=project_ids), args.format)
                elif args.decision_intel_cmd == "accept":
                    _print(
                        accept_decision(db, args.question_id, operator=args.operator, selected_option=args.selected_option, notes=args.notes),
                        args.format,
                    )
                elif args.decision_intel_cmd == "reject":
                    _print(
                        reject_decision(db, args.question_id, operator=args.operator, selected_option=args.selected_option, notes=args.notes),
                        args.format,
                    )
                elif args.decision_intel_cmd == "defer":
                    _print(
                        defer_decision(db, args.question_id, operator=args.operator, selected_option=args.selected_option, notes=args.notes),
                        args.format,
                    )
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
        if args.cmd == "report" and args.report_cmd == "ecosystem":
            analysis = analyse_portfolio(db, project_ids=None, name=args.name)
            if args.json:
                _print(analysis, "json")
            else:
                print(render_ecosystem_report(analysis), end="")
            return 0
        if args.cmd == "ecosystem":
            project_ids = getattr(args, "project_id", None)
            if args.ecosystem_cmd == "build":
                _print(build_portfolio_snapshot(db, project_ids=project_ids, name=args.name), "json")
            elif args.ecosystem_cmd == "summary":
                _print(analyse_portfolio(db, project_ids=project_ids, name=args.name), "json" if args.json else "text")
            elif args.ecosystem_cmd == "projects":
                _print(project_registry_v2(db), "json" if args.json else "text")
            elif args.ecosystem_cmd == "capabilities":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print(analysis["capability_matrix"], "json" if args.json else "text")
            elif args.ecosystem_cmd == "technologies":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print(analysis["technology_portfolio"], "json" if args.json else "text")
            elif args.ecosystem_cmd == "reuse":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["reuse_candidates"]), "items": analysis["reuse_candidates"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "duplication":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["duplicate_findings"]), "items": analysis["duplicate_findings"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "dependencies":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["cross_project_dependencies"]), "items": analysis["cross_project_dependencies"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "risks":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["portfolio_risks"]), "items": analysis["portfolio_risks"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "unknowns":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["unknown_surface"]), "items": analysis["unknown_surface"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "attention":
                analysis = analyse_portfolio(db, project_ids=project_ids, name=args.name)
                _print({"count": len(analysis["attention"]), "items": analysis["attention"]}, "json" if args.json else "text")
            elif args.ecosystem_cmd == "timeline":
                _print(ecosystem_timeline(db), "json" if args.json else "text")
            elif args.ecosystem_cmd == "diff":
                _print(ecosystem_diff(db, args.from_snapshot_id, args.to_snapshot_id), "json" if args.json else "text")
            elif args.ecosystem_cmd == "trace":
                _print(ecosystem_trace(db, args.entity_id), "json" if args.json else "text")
            elif args.ecosystem_cmd == "search":
                _print(
                    search_ecosystem(db, args.query, limit=args.limit, offset=args.offset, project_ids=project_ids),
                    "json" if args.json else "text",
                )
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
                serve_service(
                    Path(args.db),
                    host=args.host,
                    port=args.port,
                    instance_id=args.instance_id,
                    owner_pid=args.owner_pid,
                    shutdown_token=args.shutdown_token,
                )
            return 0
        if args.cmd == "version":
            print(__version__)
            return 0
    except (ValueError, FileNotFoundError, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1
