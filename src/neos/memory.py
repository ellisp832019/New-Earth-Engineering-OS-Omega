from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

from .db import connect
from .genome import build_project_genome, latest_project_genome

MEMORY_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    project_id: str
    scan_id: str
    genome_id: str | None
    memory_schema_version: int
    memory_type: str
    title: str
    summary: str
    status: str
    source_type: str
    source_path: str | None
    source_commit: str | None
    source_branch: str | None
    timestamp: str
    effective_date: str | None
    confidence: float
    provenance: str
    created_at: str
    superseded_by: str | None
    related_entities: list[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DecisionRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class AssumptionRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class ExperimentRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class ObservationRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class OutcomeRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class LessonRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class MilestoneRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class ChangeRecord(MemoryRecord):
    pass


@dataclass(frozen=True)
class MemoryRelationship:
    id: str
    project_id: str
    source_record_id: str
    target_record_id: str
    relationship_type: str
    confidence: float
    provenance: str
    created_at: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class MemoryGapFinding:
    id: str
    project_id: str
    title: str
    category: str
    severity: str
    confidence: float
    reason: str
    recommended_investigation: str
    affected_entities: list[str]
    evidence: list[str]


@dataclass(frozen=True)
class MemoryContradictionFinding:
    id: str
    project_id: str
    title: str
    category: str
    severity: str
    confidence: float
    reason: str
    evidence: list[str]
    affected_entities: list[str]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return f"{prefix}-" + hashlib.sha256(payload).hexdigest()[:24]


def _json_loads(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def _project_row(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown project: {project_id}")
    return row


def _latest_scan_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _latest_genome_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM project_genomes WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _latest_memory_row(conn, project_id: str):
    return conn.execute(
        "SELECT * FROM memory_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()


def _git(repo: Path, args: list[str]) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL)


def _git_commit_date(repo: Path, rev: str) -> str | None:
    try:
        return _git(repo, ["show", "-s", "--format=%cI", rev]).strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _file_git_date(repo: Path, path: str) -> str | None:
    try:
        return _git(repo, ["log", "-1", "--format=%cI", "--", path]).strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "item"


def _humanize(name: str) -> str:
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name.title() or "Item"


def _file_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _first_paragraph(text: str) -> str:
    lines: list[str] = []
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if started and lines:
                break
            continue
        if stripped.startswith("#"):
            if started:
                break
            continue
        started = True
        lines.append(stripped)
    return " ".join(lines)[:600]


def _snippet(text: str, limit: int = 240) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:limit]


def _parse_status(text: str, default: str = "unknown") -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("passed", "success", "complete", "completed", "validated", "shipped", "released")):
        return "complete"
    if any(token in lowered for token in ("failed", "broken", "blocked", "invalidated")):
        return "failed"
    if any(token in lowered for token in ("planned", "todo", "next steps", "next action")):
        return "planned"
    if any(token in lowered for token in ("running", "in progress", "ongoing")):
        return "running"
    if any(token in lowered for token in ("abandon", "cancel", "dropped")):
        return "abandoned"
    if any(token in lowered for token in ("inconclusive", "unclear", "unknown")):
        return "inconclusive"
    return default


def _commit_type(subject: str) -> str:
    lowered = subject.lower().strip()
    for prefix, kind in (
        ("feat:", "feature"),
        ("fix:", "fix"),
        ("refactor:", "refactor"),
        ("docs:", "docs"),
        ("test:", "test"),
        ("release:", "release"),
        ("chore:", "chore"),
        ("perf:", "refactor"),
    ):
        if lowered.startswith(prefix):
            return kind
    return "unknown"


def _timeline_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        record.get("effective_date") or record.get("timestamp") or "",
        record.get("timestamp") or "",
        record["id"],
    )


def _record_dict(record: MemoryRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["related_entities"] = list(record.related_entities)
    return payload


def _memory_insert_rows(conn, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table_columns = {row["name"] for row in conn.execute("PRAGMA table_info(memory_records)")}
    for row in rows:
        prepared = {
            **row,
            "related_entities_json": json.dumps(row.get("related_entities", []), sort_keys=True),
            "metadata_json": json.dumps(row.get("metadata", {}), sort_keys=True),
        }
        columns = [key for key in prepared if key in table_columns]
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        conn.execute(
            f"INSERT OR REPLACE INTO memory_records ({column_list}) VALUES ({placeholders})",
            tuple(prepared[column] for column in columns),
        )


def _memory_relationship_rows(conn, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table_columns = {row["name"] for row in conn.execute("PRAGMA table_info(memory_relationships)")}
    for row in rows:
        prepared = {**row, "metadata_json": json.dumps(row.get("metadata", {}), sort_keys=True)}
        columns = [key for key in prepared if key in table_columns]
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        conn.execute(
            f"INSERT OR REPLACE INTO memory_relationships ({column_list}) VALUES ({placeholders})",
            tuple(prepared[column] for column in columns),
        )


def _memory_snapshot_row(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": snapshot["id"],
        "project_id": snapshot["project_id"],
        "scan_id": snapshot["scan_id"],
        "genome_id": snapshot["genome_id"],
        "source_commit": snapshot["source_commit"],
        "source_branch": snapshot["source_branch"],
        "memory_schema_version": snapshot["memory_schema_version"],
        "source_fingerprint": snapshot["source_fingerprint"],
        "created_at": snapshot["generated_at"],
        "summary_json": json.dumps(snapshot["summary"], sort_keys=True),
        "memory_json": json.dumps(snapshot, sort_keys=True),
        "metrics_json": json.dumps(snapshot["metrics"], sort_keys=True),
    }


def _gather_decisions(conn, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> list[MemoryRecord]:
    rows = conn.execute(
        """
        SELECT d.*, COALESCE(NULLIF(e.source_path, ''), d.source_path) AS evidence_path
        FROM engineering_decisions d
        LEFT JOIN decision_evidence e ON e.decision_id = d.id
        WHERE d.project_id=?
        GROUP BY d.id
        ORDER BY d.date, d.title, d.id
        """,
        (project_id,),
    ).fetchall()
    records: list[MemoryRecord] = []
    for row in rows:
        metadata = {
            "context": row["context"],
            "decision": row["decision"],
            "rationale": row["rationale"],
            "alternatives": row["alternatives"],
            "consequences": row["consequences"],
            "decision_id": row["id"],
            "status_source": "engineering_decisions",
        }
        if row["metadata_json"]:
            metadata["source_metadata"] = _json_loads(row["metadata_json"], {})
        record = DecisionRecord(
            id=_stable_id("memory_decision", project_id, row["id"]),
            project_id=project_id,
            scan_id=scan_id,
            genome_id=genome_id,
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            memory_type="decision",
            title=row["title"],
            summary=row["decision"] or row["rationale"] or row["context"] or row["title"],
            status=row["status"] or "unknown",
            source_type="adr",
            source_path=row["source_path"],
            source_commit=source_commit,
            source_branch=source_branch,
            timestamp=row["observed_at"] or row["created_at"],
            effective_date=row["date"],
            confidence=float(row["confidence"] or 0.0),
            provenance=row["provenance"] or "adr-markdown",
            created_at=utc_now(),
            superseded_by=_json_loads(row["metadata_json"], {}).get("superseded_by") if row["metadata_json"] else None,
            related_entities=[row["id"]],
            metadata=metadata,
        )
        records.append(record)
    return records


def _group_experiment_roots(repo_root: Path) -> list[Path]:
    roots: list[Path] = []
    for base in (repo_root / "experiments", repo_root / "docs" / "project_control" / "hardware_validation"):
        if not base.exists():
            continue
        for candidate in base.rglob("*"):
            if candidate.is_dir():
                continue
            if candidate.name.lower() in {"experiment.json", "results.md", "status.md", "test_plan.md", "next_steps.md", "readme.md"} or "experiment" in candidate.as_posix().lower():
                roots.append(candidate.parent)
    unique: list[Path] = []
    seen: set[Path] = set()
    for root in sorted(roots):
        if root not in seen:
            seen.add(root)
            unique.append(root)
    return unique


def _gather_experiments(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> tuple[list[MemoryRecord], list[MemoryRelationship]]:
    records: list[MemoryRecord] = []
    relationships: list[MemoryRelationship] = []
    for root in _group_experiment_roots(repo_root):
        texts: list[str] = []
        evidence: list[str] = []
        for name in ("experiment.json", "README.md", "RESULTS.md", "STATUS.md", "TEST_PLAN.md", "NEXT_STEPS.md"):
            path = root / name
            if path.exists():
                evidence.append(path.relative_to(repo_root).as_posix())
                try:
                    texts.append(_file_text(path))
                except OSError:
                    pass
        if not texts:
            continue
        combined = "\n".join(texts)
        if not any(token in combined.lower() for token in ("experiment", "result", "hypothesis", "test plan", "status")):
            continue
        status = _parse_status(combined, default="unknown")
        title = _humanize(root.name)
        if (root / "experiment.json").exists():
            try:
                data = json.loads(_file_text(root / "experiment.json"))
                title = str(data.get("title") or data.get("name") or title)
                status = str(data.get("status") or status)
                combined = "\n".join([combined, json.dumps(data, sort_keys=True)])
            except json.JSONDecodeError:
                pass
        created = _file_git_date(repo_root, evidence[0]) or utc_now()
        record = ExperimentRecord(
            id=_stable_id("memory_experiment", project_id, root.as_posix()),
            project_id=project_id,
            scan_id=scan_id,
            genome_id=genome_id,
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            memory_type="experiment",
            title=title,
            summary=_first_paragraph(combined) or _snippet(combined),
            status=status,
            source_type="experiment_report",
            source_path=root.relative_to(repo_root).as_posix(),
            source_commit=source_commit,
            source_branch=source_branch,
            timestamp=created,
            effective_date=created,
            confidence=0.78,
            provenance="explicit-experiment-docs",
            created_at=utc_now(),
            superseded_by=None,
            related_entities=[root.relative_to(repo_root).as_posix()],
            metadata={"evidence_paths": evidence, "status_source": "experiment docs"},
        )
        records.append(record)
        if "result" in combined.lower() or "outcome" in combined.lower():
            outcome = OutcomeRecord(
                id=_stable_id("memory_outcome", project_id, root.as_posix()),
                project_id=project_id,
                scan_id=scan_id,
                genome_id=genome_id,
                memory_schema_version=MEMORY_SCHEMA_VERSION,
                memory_type="outcome",
                title=f"Outcome: {title}",
                summary=_snippet(combined),
                status=status,
                source_type="experiment_result",
                source_path=root.relative_to(repo_root).as_posix(),
                source_commit=source_commit,
                source_branch=source_branch,
                timestamp=created,
                effective_date=created,
                confidence=0.72,
                provenance="explicit-experiment-docs",
                created_at=utc_now(),
                superseded_by=None,
                related_entities=[record.id, root.relative_to(repo_root).as_posix()],
                metadata={"evidence_paths": evidence},
            )
            records.append(outcome)
            relationships.append(
                MemoryRelationship(
                    id=_stable_id("memory_rel", project_id, record.id, outcome.id, "resulted_in"),
                    project_id=project_id,
                    source_record_id=record.id,
                    target_record_id=outcome.id,
                    relationship_type="resulted_in",
                    confidence=0.9,
                    provenance="explicit-experiment-docs",
                    created_at=utc_now(),
                    metadata={"evidence_paths": evidence},
                )
            )
    return records, relationships


def _section_lines(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    current = "preamble"
    for line in text.splitlines():
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        sections[current].append(line.rstrip())
    return sections


def _extract_explicit_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            content = stripped[2:].strip()
            if content:
                bullets.append(content)
    return bullets


def _gather_assumptions(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> list[MemoryRecord]:
    patterns = ("assumption", "assumptions", "hardware availability", "network assumption", "platform support", "performance assumption", "user workflow assumption")
    records: list[MemoryRecord] = []
    candidate_paths = [
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt"}
        and any(token in path.as_posix().lower() for token in ("adr", "release", "decision", "assumption", "roadmap", "project_control"))
    ]
    for path in candidate_paths:
        try:
            text = _file_text(path)
        except OSError:
            continue
        if not any(token in text.lower() for token in patterns):
            continue
        sections = _section_lines(text)
        explicit: list[str] = []
        for key, lines in sections.items():
            if "assumption" in key:
                explicit.extend([line.strip() for line in lines if line.strip()])
        explicit.extend([line for line in _extract_explicit_bullets(text) if "assumption" in line.lower()])
        for idx, item in enumerate(explicit):
            status = "validated" if any(token in item.lower() for token in ("validated", "confirmed")) else "unvalidated"
            if any(token in item.lower() for token in ("invalidated", "rejected", "obsolete")):
                status = "invalidated"
            record = AssumptionRecord(
                id=_stable_id("memory_assumption", project_id, path.as_posix(), idx, item[:120]),
                project_id=project_id,
                scan_id=scan_id,
                genome_id=genome_id,
                memory_schema_version=MEMORY_SCHEMA_VERSION,
                memory_type="assumption",
                title=_first_heading(text) or _humanize(path.stem),
                summary=_snippet(item),
                status=status,
                source_type="assumption_doc",
                source_path=path.relative_to(repo_root).as_posix(),
                source_commit=source_commit,
                source_branch=source_branch,
                timestamp=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()) or utc_now(),
                effective_date=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()),
                confidence=0.7,
                provenance="explicit-assumption-text",
                created_at=utc_now(),
                superseded_by=None,
                related_entities=[path.relative_to(repo_root).as_posix()],
                metadata={"source_excerpt": item},
            )
            records.append(record)
    return records


def _gather_lessons(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> tuple[list[MemoryRecord], list[MemoryRelationship]]:
    records: list[MemoryRecord] = []
    relationships: list[MemoryRelationship] = []
    lesson_paths = [
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt"}
        and any(token in path.name.lower() for token in ("results", "known_limitations", "retrospective", "lessons", "lesson"))
    ]
    for path in lesson_paths:
        try:
            text = _file_text(path)
        except OSError:
            continue
        if not any(token in text.lower() for token in ("lesson", "learned", "result", "outcome", "takeaway", "limitation")):
            continue
        explicit = []
        sections = _section_lines(text)
        for key, lines in sections.items():
            if any(token in key for token in ("lesson", "learned", "result", "outcome", "limitation")):
                explicit.extend([line.strip() for line in lines if line.strip()])
        explicit.extend([line for line in _extract_explicit_bullets(text) if any(token in line.lower() for token in ("lesson", "learned", "result", "outcome", "limitation"))])
        if not explicit:
            explicit = [_first_paragraph(text)]
        for idx, item in enumerate(explicit):
            if not item:
                continue
            record = LessonRecord(
                id=_stable_id("memory_lesson", project_id, path.as_posix(), idx, item[:120]),
                project_id=project_id,
                scan_id=scan_id,
                genome_id=genome_id,
                memory_schema_version=MEMORY_SCHEMA_VERSION,
                memory_type="lesson",
                title=_first_heading(text) or _humanize(path.stem),
                summary=_snippet(item),
                status="confirmed",
                source_type="lesson_doc",
                source_path=path.relative_to(repo_root).as_posix(),
                source_commit=source_commit,
                source_branch=source_branch,
                timestamp=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()) or utc_now(),
                effective_date=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()),
                confidence=0.75,
                provenance="explicit-lesson-text",
                created_at=utc_now(),
                superseded_by=None,
                related_entities=[path.relative_to(repo_root).as_posix()],
                metadata={"source_excerpt": item},
            )
            records.append(record)
    return records, relationships


def _gather_milestones(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> list[MemoryRecord]:
    milestones: list[MemoryRecord] = []
    milestone_paths = [
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt", ".json"}
        and any(token in path.as_posix().lower() for token in ("release", "milestone", "roadmap", "version_direction", "acceptance", "phase"))
    ]
    for path in milestone_paths:
        try:
            text = _file_text(path)
        except OSError:
            continue
        if not any(token in text.lower() for token in ("milestone", "release", "phase", "acceptance", "complete", "planned", "version")):
            continue
        title = _first_heading(text) or _humanize(path.stem)
        status = _parse_status(text, default="observed")
        created = _file_git_date(repo_root, path.relative_to(repo_root).as_posix()) or utc_now()
        record = MilestoneRecord(
            id=_stable_id("memory_milestone", project_id, path.as_posix()),
            project_id=project_id,
            scan_id=scan_id,
            genome_id=genome_id,
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            memory_type="milestone",
            title=title,
            summary=_first_paragraph(text) or _snippet(text),
            status=status,
            source_type="milestone_doc",
            source_path=path.relative_to(repo_root).as_posix(),
            source_commit=source_commit,
            source_branch=source_branch,
            timestamp=created,
            effective_date=created,
            confidence=0.68,
            provenance="explicit-milestone-text",
            created_at=utc_now(),
            superseded_by=None,
            related_entities=[path.relative_to(repo_root).as_posix()],
            metadata={"source_excerpt": _snippet(text)},
        )
        milestones.append(record)
    return milestones


def _gather_observations(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> list[MemoryRecord]:
    records: list[MemoryRecord] = []
    observation_paths = [
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt", ".json"}
        and any(token in path.as_posix().lower() for token in ("results", "readme", "evidence", "validation", "status", "known_limitations", "test"))
    ]
    for path in observation_paths:
        try:
            text = _file_text(path)
        except OSError:
            continue
        if not any(token in text.lower() for token in ("evidence", "result", "validation", "observed", "status", "test", "acceptance")):
            continue
        record = ObservationRecord(
            id=_stable_id("memory_observation", project_id, path.as_posix()),
            project_id=project_id,
            scan_id=scan_id,
            genome_id=genome_id,
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            memory_type="observation",
            title=_first_heading(text) or _humanize(path.stem),
            summary=_first_paragraph(text) or _snippet(text),
            status=_parse_status(text, default="observed"),
            source_type="evidence_doc",
            source_path=path.relative_to(repo_root).as_posix(),
            source_commit=source_commit,
            source_branch=source_branch,
            timestamp=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()) or utc_now(),
            effective_date=_file_git_date(repo_root, path.relative_to(repo_root).as_posix()),
            confidence=0.72,
            provenance="explicit-evidence-text",
            created_at=utc_now(),
            superseded_by=None,
            related_entities=[path.relative_to(repo_root).as_posix()],
            metadata={"source_excerpt": _snippet(text)},
        )
        records.append(record)
    return records


def _gather_changes(repo_root: Path, project_id: str, scan_id: str, genome_id: str | None, source_commit: str | None, source_branch: str | None) -> list[MemoryRecord]:
    records: list[MemoryRecord] = []
    try:
        raw = _git(repo_root, ["log", "--date=iso-strict", "--format=%H%x1f%an%x1f%ad%x1f%s%x1e", "--name-only", "--no-renames"])
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return records
    for block in raw.strip().split("\x1e"):
        block = block.strip()
        if not block:
            continue
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        parts = lines[0].split("\x1f")
        if len(parts) < 4:
            continue
        commit_hash, author, date, subject = parts[:4]
        files = lines[1:]
        change_type = _commit_type(subject)
        created = date or _git_commit_date(repo_root, commit_hash) or utc_now()
        record = ChangeRecord(
            id=_stable_id("memory_change", project_id, commit_hash),
            project_id=project_id,
            scan_id=scan_id,
            genome_id=genome_id,
            memory_schema_version=MEMORY_SCHEMA_VERSION,
            memory_type="change",
            title=subject,
            summary=subject,
            status=change_type,
            source_type="git_commit",
            source_path=None,
            source_commit=commit_hash,
            source_branch=source_branch,
            timestamp=created,
            effective_date=created,
            confidence=0.98,
            provenance="git-history",
            created_at=utc_now(),
            superseded_by=None,
            related_entities=[commit_hash],
            metadata={"author": author, "files_changed": files, "file_count": len(files), "change_type": change_type},
        )
        records.append(record)
    return records


def _group_by_type(records: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["memory_type"]].append(record)
    for items in grouped.values():
        items.sort(key=_timeline_key)
    return dict(sorted(grouped.items()))


def _related_entity_index(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for entity in record.get("related_entities", []):
            index[entity].append(record)
        if record.get("source_path"):
            index[record["source_path"]].append(record)
        if record.get("source_commit"):
            index[record["source_commit"]].append(record)
    return index


def _build_relationships(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    by_entity = _related_entity_index(records)
    for entity, related in by_entity.items():
        if len(related) < 2:
            continue
        ordered = sorted(related, key=_timeline_key)
        for left, right in pairwise(ordered):
            relationships.append(
                {
                    "id": _stable_id("memory_rel", left["id"], right["id"], "occurred_before"),
                    "project_id": left["project_id"],
                    "source_record_id": left["id"],
                    "target_record_id": right["id"],
                    "relationship_type": "occurred_before",
                    "confidence": 0.65,
                    "provenance": "deterministic-memory-ordering",
                    "created_at": utc_now(),
                    "metadata": {"entity": entity},
                }
            )
    decisions = [record for record in records if record["memory_type"] == "decision"]
    experiments = [record for record in records if record["memory_type"] == "experiment"]
    lessons = [record for record in records if record["memory_type"] == "lesson"]
    for decision in decisions:
        for record in records:
            if record["id"] == decision["id"]:
                continue
            if record["memory_type"] in {"observation", "outcome"} and record["source_path"] == decision["source_path"]:
                relationships.append(
                    {
                        "id": _stable_id("memory_rel", record["id"], decision["id"], "supports"),
                        "project_id": record["project_id"],
                        "source_record_id": record["id"],
                        "target_record_id": decision["id"],
                        "relationship_type": "supports",
                        "confidence": 0.75,
                        "provenance": "source-path-alignment",
                        "created_at": utc_now(),
                        "metadata": {"reason": "shared source path"},
                    }
                )
    for experiment in experiments:
        for lesson in lessons:
            if experiment["source_path"] == lesson["source_path"]:
                relationships.append(
                    {
                        "id": _stable_id("memory_rel", experiment["id"], lesson["id"], "resulted_in"),
                        "project_id": experiment["project_id"],
                        "source_record_id": experiment["id"],
                        "target_record_id": lesson["id"],
                        "relationship_type": "resulted_in",
                        "confidence": 0.8,
                        "provenance": "experiment-lesson-link",
                        "created_at": utc_now(),
                        "metadata": {"reason": "shared source path"},
                    }
                )
    return relationships


def _gaps_from_records(genome: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[MemoryGapFinding] = []
    records_by_type = defaultdict(list)
    for record in records:
        records_by_type[record["memory_type"]].append(record)
    for record in records_by_type.get("decision", []):
        if not record.get("metadata", {}).get("rationale"):
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", record["id"], "decision-rationale"),
                    project_id=record["project_id"],
                    title=f"Decision has weak or missing rationale: {record['title']}",
                    category="missing rationale",
                    severity="medium",
                    confidence=0.7,
                    reason="Decision record does not capture a strong rationale.",
                    recommended_investigation="Add explicit rationale evidence or an ADR section describing the reasoning.",
                    affected_entities=[record["id"]],
                    evidence=[record.get("source_path") or record["id"]],
                )
            )
        if not record.get("metadata", {}).get("consequences"):
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", record["id"], "decision-consequence"),
                    project_id=record["project_id"],
                    title=f"Decision has no consequence record: {record['title']}",
                    category="missing consequence",
                    severity="medium",
                    confidence=0.66,
                    reason="Decision evidence does not state consequences clearly.",
                    recommended_investigation="Capture follow-up consequences or release impacts in the source decision record.",
                    affected_entities=[record["id"]],
                    evidence=[record.get("source_path") or record["id"]],
                )
            )
    for record in records_by_type.get("experiment", []):
        if record["status"] in {"unknown", "planned"}:
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", record["id"], "experiment-result"),
                    project_id=record["project_id"],
                    title=f"Experiment has no result: {record['title']}",
                    category="missing result",
                    severity="medium",
                    confidence=0.72,
                    reason="Experiment documentation exists but no result or outcome was captured.",
                    recommended_investigation="Record the experiment result in the experiment docs or result log.",
                    affected_entities=[record["id"]],
                    evidence=[record.get("source_path") or record["id"]],
                )
            )
    for record in records_by_type.get("assumption", []):
        if record["status"] in {"unvalidated", "unknown"}:
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", record["id"], "assumption-validation"),
                    project_id=record["project_id"],
                    title=f"Assumption remains unvalidated: {record['title']}",
                    category="unvalidated assumption",
                    severity="medium",
                    confidence=0.78,
                    reason="The source evidence states an assumption but not a validation outcome.",
                    recommended_investigation="Validate or invalidate the assumption against observed project evidence.",
                    affected_entities=[record["id"]],
                    evidence=[record.get("source_path") or record["id"]],
                )
            )
    for feature in genome.get("features", []):
        feature_name = str(feature.get("feature_name") or feature.get("name") or "").lower()
        feature_id = str(feature.get("feature_id") or feature.get("id") or "")
        if not any(feature_name in record["title"].lower() or feature_id in json.dumps(record.get("metadata", {})) for record in records):
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", feature_id, "feature-rationale"),
                    project_id=genome["project_id"],
                    title=f"Feature has no rationale: {feature_name or feature_id}",
                    category="missing feature rationale",
                    severity="medium",
                    confidence=0.6,
                    reason="No memory record clearly explains why the feature exists.",
                    recommended_investigation="Link the feature to a decision, experiment, lesson or release note.",
                    affected_entities=[feature_id],
                    evidence=feature.get("maturity", {}).get("evidence_paths", [])[:10],
                )
            )
    for component in genome.get("architecture", {}).get("components", []):
        if not any(component["name"].lower() in record["title"].lower() for record in records_by_type.get("decision", [])):
            gaps.append(
                MemoryGapFinding(
                    id=_stable_id("gap", component["id"], "component-decision"),
                    project_id=genome["project_id"],
                    title=f"Major architecture component has no decision record: {component['name']}",
                    category="missing architecture decision",
                    severity="medium",
                    confidence=0.58,
                    reason="No decision record was linked to the component from current memory evidence.",
                    recommended_investigation="Identify the decision or ADR that shaped this component.",
                    affected_entities=[component["id"]],
                    evidence=component.get("evidence_paths", [])[:10],
                )
            )
    return [asdict(gap) for gap in gaps]


def _contradictions_from_records(records: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contradictions: list[MemoryContradictionFinding] = []
    record_map = {record["id"]: record for record in records}
    incoming = defaultdict(list)
    for rel in relationships:
        incoming[rel["target_record_id"]].append(rel)
    for record in records:
        if record["memory_type"] == "assumption" and record["status"] == "invalidated" and incoming.get(record["id"]):
            contradictions.append(
                    MemoryContradictionFinding(
                        id=_stable_id("contradiction", record["id"], "invalidated-assumption-dependency"),
                        project_id=record["project_id"],
                        title=f"Invalidated assumption still has dependencies: {record['title']}",
                        category="invalidated_assumption_dependency",
                        severity="high",
                        confidence=0.74,
                        reason="An invalidated assumption remains connected to later memory records.",
                        evidence=[record.get("source_path") or record["id"]],
                        affected_entities=[record["id"]],
                    )
                )
        if record["memory_type"] == "decision" and record["superseded_by"]:
            target = record_map.get(record["superseded_by"])
            if target and target.get("status") in {"accepted", "implemented"}:
                contradictions.append(
                    MemoryContradictionFinding(
                        id=_stable_id("contradiction", record["id"], "superseded-reference"),
                        project_id=record["project_id"],
                        title=f"Superseded decision still looks current: {record['title']}",
                        category="superseded_reference",
                        severity="medium",
                        confidence=0.72,
                        reason="A decision marked as superseded still appears active in the memory graph.",
                        evidence=[record.get("source_path") or record["id"]],
                        affected_entities=[record["id"], record["superseded_by"]],
                    )
                )
    return [asdict(item) for item in contradictions]


def _memory_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    counts = {kind: len(items) for kind, items in snapshot["records"].items()}
    total = sum(counts.values())
    return {
        "project_id": snapshot["project_id"],
        "memory_schema_version": snapshot["memory_schema_version"],
        "record_count": total,
        "record_counts": counts,
        "relationship_count": len(snapshot["relationships"]),
        "gap_count": len(snapshot["gaps"]),
        "contradiction_count": len(snapshot["contradictions"]),
        "timeline_count": len(snapshot["timeline"]),
        "health": snapshot["memory_health"],
    }


def _memory_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_count": sum(len(items) for items in snapshot["records"].values()),
        "decision_count": len(snapshot["records"].get("decision", [])),
        "assumption_count": len(snapshot["records"].get("assumption", [])),
        "experiment_count": len(snapshot["records"].get("experiment", [])),
        "observation_count": len(snapshot["records"].get("observation", [])),
        "outcome_count": len(snapshot["records"].get("outcome", [])),
        "lesson_count": len(snapshot["records"].get("lesson", [])),
        "milestone_count": len(snapshot["records"].get("milestone", [])),
        "change_count": len(snapshot["records"].get("change", [])),
        "relationship_count": len(snapshot["relationships"]),
        "contradiction_count": len(snapshot["contradictions"]),
        "gap_count": len(snapshot["gaps"]),
    }


def _memory_health(snapshot: dict[str, Any]) -> dict[str, Any]:
    score = 100
    score -= len(snapshot["gaps"]) * 3
    score -= len(snapshot["contradictions"]) * 5
    score -= max(0, 5 - len(snapshot["records"].get("decision", []))) * 2
    score -= max(0, 3 - len(snapshot["records"].get("experiment", []))) * 2
    score = max(0, min(100, score))
    if score >= 85:
        status = "healthy"
    elif score >= 70:
        status = "watch"
    else:
        status = "attention"
    return {"score": score, "status": status}


def _build_snapshot(snapshot_row, genome_row, records: list[dict[str, Any]], relationships: list[dict[str, Any]], genome: dict[str, Any]) -> dict[str, Any]:
    grouped = _group_by_type(records)
    timeline = sorted(records, key=_timeline_key)
    snapshot: dict[str, Any] = {
        "id": snapshot_row["id"] if snapshot_row else _stable_id("memory_snapshot", genome["project_id"], genome_row["id"], MEMORY_SCHEMA_VERSION),
        "project_id": genome["project_id"],
        "scan_id": genome["scan_id"],
        "genome_id": genome_row["id"],
        "source_commit": genome["source_commit"],
        "source_branch": genome["source_branch"],
        "memory_schema_version": MEMORY_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "records": grouped,
        "relationships": relationships,
        "timeline": timeline,
        "gaps": _gaps_from_records(genome, records),
        "contradictions": _contradictions_from_records(records, relationships),
        "provenance": {
            "source_commit": genome["source_commit"],
            "source_branch": genome["source_branch"],
            "scan_id": genome["scan_id"],
            "genome_id": genome_row["id"],
            "genome_schema_version": genome_row["genome_schema_version"],
        },
    }
    snapshot["memory_health"] = _memory_health(snapshot)
    snapshot["summary"] = _memory_summary(snapshot)
    snapshot["metrics"] = _memory_metrics(snapshot)
    snapshot["source_fingerprint"] = _stable_id(
        "memory_fp",
        genome["project_id"],
        genome["scan_id"],
        genome_row["id"],
        genome["source_commit"],
        genome["source_branch"],
        MEMORY_SCHEMA_VERSION,
        [(record["id"], record["memory_type"], record["status"], record["source_path"], record["source_commit"]) for record in timeline],
    )
    return snapshot


def build_project_memory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    scan = _latest_scan_row(conn, project_id)
    if not scan:
        conn.close()
        raise ValueError(f"No scans available for project: {project_id}")
    genome_row = _latest_genome_row(conn, project_id)
    if not genome_row:
        conn.close()
        build_project_genome(db_path, project_id)
        conn = connect(db_path)
        project = _project_row(conn, project_id)
        scan = _latest_scan_row(conn, project_id)
        genome_row = _latest_genome_row(conn, project_id)
    if not genome_row:
        conn.close()
        raise ValueError(f"No genome snapshots available for project: {project_id}")
    repo_root = Path(project["repo_path"])
    genome = latest_project_genome(db_path, project_id)
    records: list[MemoryRecord] = []
    source_commit = genome_row["source_commit"] or scan["git_commit"]
    source_branch = genome_row["source_branch"] or scan["git_branch"]
    records.extend(_gather_decisions(conn, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch))
    experiment_records, experiment_relationships = _gather_experiments(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch)
    records.extend(experiment_records)
    records.extend(_gather_assumptions(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch))
    lesson_records, lesson_relationships = _gather_lessons(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch)
    records.extend(lesson_records)
    records.extend(_gather_milestones(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch))
    records.extend(_gather_observations(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch))
    records.extend(_gather_changes(repo_root, project_id, scan["scan_id"], genome_row["id"], source_commit, source_branch))
    unique_records = {record.id: record for record in records}
    records = list(unique_records.values())
    record_rows = [_record_dict(record) for record in records]
    relationships = _build_relationships(record_rows)
    relationships.extend([asdict(rel) for rel in experiment_relationships + lesson_relationships])
    snapshot = _build_snapshot(None, genome_row, record_rows, relationships, genome)
    existing = conn.execute(
        """
        SELECT *
        FROM memory_snapshots
        WHERE project_id=? AND memory_schema_version=? AND source_fingerprint=?
        LIMIT 1
        """,
        (project_id, MEMORY_SCHEMA_VERSION, snapshot["source_fingerprint"]),
    ).fetchone()
    if existing:
        loaded = _json_loads(existing["memory_json"], {})
        conn.close()
        return {"memory": loaded, "stored": False, "snapshot": dict(existing)}

    _memory_insert_rows(conn, record_rows)
    _memory_relationship_rows(conn, relationships)
    conn.execute(
        """
        INSERT INTO memory_snapshots(
            id, project_id, scan_id, genome_id, source_commit, source_branch, memory_schema_version,
            source_fingerprint, created_at, summary_json, memory_json, metrics_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            snapshot["id"],
            snapshot["project_id"],
            snapshot["scan_id"],
            snapshot["genome_id"],
            snapshot["source_commit"],
            snapshot["source_branch"],
            snapshot["memory_schema_version"],
            snapshot["source_fingerprint"],
            snapshot["generated_at"],
            json.dumps(snapshot["summary"], sort_keys=True),
            json.dumps(snapshot, sort_keys=True),
            json.dumps(snapshot["metrics"], sort_keys=True),
        ),
    )
    conn.commit()
    stored = conn.execute("SELECT * FROM memory_snapshots WHERE id=?", (snapshot["id"],)).fetchone()
    conn.close()
    return {"memory": snapshot, "stored": True, "snapshot": dict(stored) if stored else {}}


def latest_project_memory(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = _latest_memory_row(conn, project_id)
    conn.close()
    if not row:
        return {}
    return _json_loads(row["memory_json"], {})


def memory_summary(memory: dict[str, Any]) -> dict[str, Any]:
    return memory.get("summary", {})


def memory_timeline(
    memory: dict[str, Any],
    *,
    memory_type: str | None = None,
    feature: str | None = None,
    domain: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    entries = list(memory.get("timeline", []))
    if memory_type:
        entries = [entry for entry in entries if entry.get("memory_type") == memory_type]
    if feature:
        entries = [entry for entry in entries if feature.lower() in json.dumps(entry, sort_keys=True).lower()]
    if domain:
        entries = [entry for entry in entries if domain.lower() in json.dumps(entry, sort_keys=True).lower()]
    if since:
        entries = [entry for entry in entries if (entry.get("effective_date") or entry.get("timestamp") or "") >= since]
    if until:
        entries = [entry for entry in entries if (entry.get("effective_date") or entry.get("timestamp") or "") <= until]
    entries = sorted(entries, key=_timeline_key)
    return {"project_id": memory.get("project_id"), "count": len(entries), "items": entries}


def memory_decisions(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("records", {}).get("decision", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_assumptions(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("records", {}).get("assumption", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_experiments(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("records", {}).get("experiment", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_lessons(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("records", {}).get("lesson", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_milestones(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("records", {}).get("milestone", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_gaps(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("gaps", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_contradictions(memory: dict[str, Any]) -> dict[str, Any]:
    items = memory.get("contradictions", [])
    return {"project_id": memory.get("project_id"), "count": len(items), "items": items}


def memory_trace(memory: dict[str, Any], entity_id: str) -> dict[str, Any]:
    records = [record for group in memory.get("records", {}).values() for record in group]
    relationships = memory.get("relationships", [])
    seed_records = [record for record in records if entity_id in record.get("related_entities", []) or entity_id in (record.get("source_path") or "") or entity_id in (record.get("source_commit") or "")]
    if not seed_records:
        seed_records = [record for record in records if entity_id.lower() in json.dumps(record, sort_keys=True).lower()]
    visited = {record["id"] for record in seed_records}
    nodes = [{"id": record["id"], "record": record, "depth": 0} for record in seed_records]
    edges = []
    frontier = [(record["id"], 0) for record in seed_records]
    while frontier:
        current_id, depth = frontier.pop(0)
        if depth >= 4:
            continue
        for rel in relationships:
            if rel["source_record_id"] != current_id and rel["target_record_id"] != current_id:
                continue
            next_id = rel["target_record_id"] if rel["source_record_id"] == current_id else rel["source_record_id"]
            edges.append({**rel, "depth": depth + 1})
            if next_id not in visited:
                visited.add(next_id)
                record = next(record for record in records if record["id"] == next_id)
                nodes.append({"id": next_id, "record": record, "depth": depth + 1})
                frontier.append((next_id, depth + 1))
    return {"entity_id": entity_id, "count": len(nodes), "nodes": nodes, "edges": edges}


def memory_trace_entity(db_path: Path, entity_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project_ids = [row["project_id"] for row in conn.execute("SELECT DISTINCT project_id FROM memory_snapshots ORDER BY project_id")]
    conn.close()
    for project_id in project_ids:
        memory = latest_project_memory(db_path, project_id)
        if not memory:
            continue
        trace = memory_trace(memory, entity_id)
        if trace["count"]:
            return trace
    return {"entity_id": entity_id, "count": 0, "nodes": [], "edges": []}


def memory_why(memory: dict[str, Any], entity_id: str) -> dict[str, Any]:
    trace = memory_trace(memory, entity_id)
    records = [node["record"] for node in trace["nodes"]]
    recorded_rationale = []
    supporting_evidence = []
    related_decisions = []
    historical_changes = []
    unknown_rationale = []
    for record in records:
        if record["memory_type"] == "decision":
            recorded_rationale.append(record.get("metadata", {}).get("rationale") or record["summary"])
            related_decisions.append(record)
        elif record["memory_type"] == "change":
            historical_changes.append(record)
        elif record["memory_type"] in {"experiment", "lesson", "outcome"}:
            supporting_evidence.append(record)
    if not recorded_rationale:
        unknown_rationale.append("Rationale not recorded in current engineering memory.")
    return {
        "entity_id": entity_id,
        "recorded_rationale": recorded_rationale,
        "supporting_evidence": supporting_evidence,
        "related_decisions": related_decisions,
        "historical_changes": historical_changes,
        "unknown_rationale": unknown_rationale,
        "trace": trace,
    }


def _diff_records(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    before_map = {row["id"]: row for row in before}
    after_map = {row["id"]: row for row in after}
    added = [after_map[key] for key in sorted(set(after_map) - set(before_map))]
    removed = [before_map[key] for key in sorted(set(before_map) - set(after_map))]
    changed = [after_map[key] for key in sorted(set(before_map) & set(after_map)) if json.dumps(before_map[key], sort_keys=True) != json.dumps(after_map[key], sort_keys=True)]
    return {"added": added, "removed": removed, "changed": changed}


def memory_diff(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT * FROM memory_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 2",
        (project_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return {"project_id": project_id, "latest_memory_id": None, "previous_memory_id": None, "changes": {}}
    latest = _json_loads(rows[0]["memory_json"], {})
    previous = _json_loads(rows[1]["memory_json"], {}) if len(rows) > 1 else {}
    changes = {
        "new_decisions": _diff_records(previous.get("records", {}).get("decision", []), latest.get("records", {}).get("decision", [])),
        "new_assumptions": _diff_records(previous.get("records", {}).get("assumption", []), latest.get("records", {}).get("assumption", [])),
        "new_experiments": _diff_records(previous.get("records", {}).get("experiment", []), latest.get("records", {}).get("experiment", [])),
        "new_lessons": _diff_records(previous.get("records", {}).get("lesson", []), latest.get("records", {}).get("lesson", [])),
        "new_milestones": _diff_records(previous.get("records", {}).get("milestone", []), latest.get("records", {}).get("milestone", [])),
        "new_changes": _diff_records(previous.get("records", {}).get("change", []), latest.get("records", {}).get("change", [])),
        "resolved_memory_gaps": _diff_records(previous.get("gaps", []), latest.get("gaps", [])),
        "new_memory_gaps": _diff_records(previous.get("gaps", []), latest.get("gaps", [])),
        "new_contradictions": _diff_records(previous.get("contradictions", []), latest.get("contradictions", [])),
    }
    return {
        "project_id": project_id,
        "latest_memory_id": rows[0]["id"],
        "previous_memory_id": rows[1]["id"] if len(rows) > 1 else None,
        "changes": changes,
    }


def render_memory_report(memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": memory.get("project_id"),
        "sections": {
            "Executive summary": memory_summary(memory),
            "Decisions": memory_decisions(memory),
            "Assumptions": memory_assumptions(memory),
            "Experiments": memory_experiments(memory),
            "Lessons": memory_lessons(memory),
            "Milestones": memory_milestones(memory),
            "Timeline": memory_timeline(memory),
            "Gaps": memory_gaps(memory),
            "Contradictions": memory_contradictions(memory),
        },
    }


def memory_markdown_report(memory: dict[str, Any]) -> str:
    summary = memory_summary(memory)
    lines = [
        f"# Engineering Memory Report: {memory.get('project_id')}",
        "",
        f"- Records: {summary.get('record_count', 0)}",
        f"- Decisions: {summary.get('record_counts', {}).get('decision', 0)}",
        f"- Assumptions: {summary.get('record_counts', {}).get('assumption', 0)}",
        f"- Experiments: {summary.get('record_counts', {}).get('experiment', 0)}",
        f"- Lessons: {summary.get('record_counts', {}).get('lesson', 0)}",
        f"- Milestones: {summary.get('record_counts', {}).get('milestone', 0)}",
        f"- Changes: {summary.get('record_counts', {}).get('change', 0)}",
        f"- Gaps: {summary.get('gap_count', 0)}",
        f"- Contradictions: {summary.get('contradiction_count', 0)}",
        "",
        "## Recorded rationale",
    ]
    rationale = []
    for item in memory.get("records", {}).get("decision", []):
        if item.get("metadata", {}).get("rationale"):
            rationale.append(f"- {item['title']}: {item['metadata']['rationale']}")
    lines.extend(rationale or ["- Rationale not recorded in current engineering memory."])
    lines.append("")
    lines.append("## Timeline")
    for item in memory_timeline(memory).get("items", [])[:30]:
        lines.append(f"- {item.get('effective_date') or item.get('timestamp')}: [{item['memory_type']}] {item['title']} ({item['status']})")
    return "\n".join(lines)
