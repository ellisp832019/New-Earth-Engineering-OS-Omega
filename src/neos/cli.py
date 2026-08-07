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
    build_inventory,
    context_bundle,
    documentation_inventory,
    git_state_report,
    init_project,
    project_summary,
    scan_diff,
    scan_project,
    stale_scan_status,
    technology_inventory,
    test_inventory,
)
from .db import connect


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


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    db = Path(args.db)
    try:
        if args.cmd == "doctor":
            conn = connect(db)
            v = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
            conn.close()
            print(
                json.dumps(
                    {
                        "status": "healthy",
                        "neos_version": __version__,
                        "schema_version": v,
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
        if args.cmd == "version":
            print(__version__)
            return 0
    except (ValueError, FileNotFoundError, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1
