from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .genome import build_project_genome, latest_project_genome

ENGINE_VERSION = "1.0.0"

REQUIREMENT_STATES = {
    "candidate",
    "confirmed",
    "rejected",
    "deferred",
    "verified",
}

REQUIREMENT_TYPES = {
    "functional",
    "constraint",
    "architecture",
    "verification",
    "release",
    "assumption",
    "unknown",
}

LINK_TYPES = {
    "feature",
    "architecture",
    "implementation",
    "test",
    "validation",
    "release",
    "documentation",
}

DEFAULT_REQUIREMENT_KEYWORDS = (
    "must",
    "must not",
    "shall",
    "shall not",
    "should",
    "required",
    "need to",
    "needs to",
    "have to",
    "cannot",
    "do not",
    "don't",
    "complete when",
    "verified",
    "ready when",
)


@dataclass(frozen=True)
class RequirementCandidate:
    id: str
    project_id: str
    requirement_key: str
    title: str
    description: str
    requirement_type: str
    status: str
    canonical_state: str
    source: str
    source_path: str
    source_line: int | None
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    provenance: str = "deterministic-requirement-extractor"
    related_feature_ids: list[str] = field(default_factory=list)
    related_architecture: list[dict[str, Any]] = field(default_factory=list)
    related_test_paths: list[str] = field(default_factory=list)
    related_validation: list[str] = field(default_factory=list)
    related_release: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["related_feature_ids_json"] = json.dumps(self.related_feature_ids, sort_keys=True)
        data["related_architecture_json"] = json.dumps(self.related_architecture, sort_keys=True)
        data["related_test_paths_json"] = json.dumps(self.related_test_paths, sort_keys=True)
        data["related_validation_json"] = json.dumps(self.related_validation, sort_keys=True)
        data["related_release_json"] = json.dumps(self.related_release, sort_keys=True)
        return data


@dataclass(frozen=True)
class RequirementEvidence:
    id: str
    requirement_id: str
    link_type: str
    entity_id: str
    source_path: str
    source_line: int | None
    confidence: float
    supports_or_opposes: str
    provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RequirementReview:
    id: str
    requirement_id: str
    operator: str
    review_state: str
    notes: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _stable_id(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _uniq(items: list[str]) -> list[str]:
    return [item for index, item in enumerate(items) if item and item not in items[:index]]


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_./-]+", text.lower()) if len(token) > 2}


def _score_overlap(left: str, right: str) -> int:
    return len(_tokenize(left) & _tokenize(right))


def _project_rows(conn, project_ids: list[str] | None = None) -> list[dict[str, Any]]:
    if project_ids:
        placeholders = ", ".join(["?"] * len(project_ids))
        rows = conn.execute(
            f"SELECT project_id, name, repo_path FROM projects WHERE project_id IN ({placeholders}) ORDER BY project_id",
            tuple(project_ids),
        ).fetchall()
    else:
        rows = conn.execute("SELECT project_id, name, repo_path FROM projects ORDER BY project_id").fetchall()
    return [dict(row) for row in rows]


def _latest_scan_id(conn, project_id: str) -> str | None:
    row = conn.execute("SELECT scan_id FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1", (project_id,)).fetchone()
    return row["scan_id"] if row else None


def _latest_scan_paths(conn, project_id: str) -> list[dict[str, Any]]:
    scan_id = _latest_scan_id(conn, project_id)
    if not scan_id:
        return []
    rows = conn.execute(
        """
        SELECT source_path, kind, label, metadata_json
        FROM scan_observations
        WHERE project_id=? AND scan_id=?
        ORDER BY source_path, kind, label
        """,
        (project_id, scan_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _project_repo_root(conn, project_id: str) -> Path:
    row = conn.execute("SELECT repo_path FROM projects WHERE project_id=?", (project_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown project: {project_id}")
    return Path(row["repo_path"])


def _read_text(repo_root: Path, source_path: str) -> str:
    file_path = repo_root / source_path
    if not file_path.exists() or not file_path.is_file():
        return ""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _candidate_paths(observations: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for row in observations:
        path = str(row.get("source_path") or "").strip()
        if not path:
            continue
        lowered = path.lower()
        name = Path(path).name.lower()
        if lowered.startswith(("docs/", "doc/")) or name in {"readme.md", "readme", "license.md", "contributing.md"} or any(token in lowered for token in ("requirement", "architecture", "adr", "design", "spec", "guide", "roadmap", "release", "validation", "acceptance", "do_don", "definition_of_done")):
            paths.append(path)
    return _uniq(paths)


def _classify_requirement_type(source_path: str, line: str) -> str:
    lowered = f"{source_path.lower()} {line.lower()}"
    if any(token in lowered for token in ("acceptance", "verify", "validated", "validation", "test", "tests", "evidence")):
        return "verification"
    if any(token in lowered for token in ("release", "package", "ship", "deploy", "version")):
        return "release"
    if any(token in lowered for token in ("architecture", "design", "layer", "boundary", "interface", "thin client")):
        return "architecture"
    if any(token in lowered for token in ("must not", "shall not", "cannot", "do not", "don't", "never", "forbidden")):
        return "constraint"
    if any(token in lowered for token in ("must", "shall", "required", "need to", "needs to", "have to")):
        return "functional"
    if any(token in lowered for token in ("assume", "assumption", "candidate only")):
        return "assumption"
    return "unknown"


def _looks_like_requirement(source_path: str, line: str) -> bool:
    lowered = line.lower().strip()
    if not lowered or len(lowered) < 12:
        return False
    if not any(keyword in lowered for keyword in DEFAULT_REQUIREMENT_KEYWORDS):
        return False
    if lowered.startswith("#"):
        return True
    if lowered.startswith(("-", "*", ">", "1.", "2.", "3.", "4.", "5.")):
        return True
    return any(token in source_path.lower() for token in ("requirements", "architecture", "guide", "roadmap", "spec", "adr", "release", "validation"))


def _parse_requirement_line(project_id: str, source_path: str, line_no: int, line: str, file_tokens: set[str]) -> RequirementCandidate | None:
    if not _looks_like_requirement(source_path, line):
        return None
    text = line.strip().lstrip("-*>0123456789. ").strip()
    if len(text) < 8:
        return None
    requirement_type = _classify_requirement_type(source_path, text)
    tokens = _tokenize(text)
    confidence = min(0.55 + 0.03 * len(tokens & file_tokens), 0.98)
    if requirement_type in {"verification", "architecture", "release"}:
        confidence = min(0.65 + 0.04 * len(tokens & file_tokens), 0.99)
    requirement_key = f"req-{_stable_id(project_id, source_path, line_no, text)}"
    return RequirementCandidate(
        id=requirement_key,
        project_id=project_id,
        requirement_key=requirement_key,
        title=text[:120],
        description=text,
        requirement_type=requirement_type,
        status="candidate",
        canonical_state="derived",
        source="document-line",
        source_path=source_path,
        source_line=line_no,
        confidence=round(confidence, 3),
        provenance="deterministic-document-extractor",
        metadata={
            "line": line_no,
            "file_tokens": sorted(file_tokens),
            "keywords": [keyword for keyword in DEFAULT_REQUIREMENT_KEYWORDS if keyword in text.lower()],
        },
    )


def _ensure_genome(db_path: Path, project_id: str) -> dict[str, Any]:
    genome = latest_project_genome(db_path, project_id)
    if genome:
        return genome
    return build_project_genome(db_path, project_id)["genome"]


def _evidence_for_requirement(genome: dict[str, Any], requirement: RequirementCandidate) -> list[RequirementEvidence]:
    requirement_text = f"{requirement.title} {requirement.description}"
    tokens = _tokenize(requirement_text)
    evidence: list[RequirementEvidence] = []

    def add(link_type: str, entity_id: str, source_path: str, source_line: int | None, confidence: float, supports: str, metadata: dict[str, Any]) -> None:
        evidence.append(
            RequirementEvidence(
                id=f"req-ev-{_stable_id(requirement.id, link_type, entity_id, source_path, source_line or 0)}",
                requirement_id=requirement.id,
                link_type=link_type,
                entity_id=entity_id,
                source_path=source_path,
                source_line=source_line,
                confidence=round(confidence, 3),
                supports_or_opposes=supports,
                provenance=metadata.get("provenance", "deterministic-trace"),
                metadata=metadata,
            )
        )

    for feature in genome.get("features", []):
        feature_text = f"{feature.get('name', '')} {feature.get('description', '')}"
        overlap = _score_overlap(requirement_text, feature_text)
        if overlap > 0:
            add(
                "feature",
                feature["feature_id"],
                feature.get("source_path", feature.get("name", "")),
                None,
                min(0.6 + 0.05 * overlap, 0.98),
                "supports",
                {"name": feature.get("name"), "source": feature.get("source"), "evidence_paths": feature.get("maturity", {}).get("evidence_paths", [])},
            )
            for path in feature.get("maturity", {}).get("evidence_paths", [])[:4]:
                add(
                    "implementation",
                    feature["feature_id"],
                    path,
                    None,
                    min(0.5 + 0.05 * overlap, 0.95),
                    "supports",
                    {"feature": feature.get("name"), "path": path},
                )
            for path in feature.get("maturity", {}).get("components", [{}])[0].get("evidence_paths", [])[:3]:
                add(
                    "validation",
                    feature["feature_id"],
                    path,
                    None,
                    min(0.45 + 0.04 * overlap, 0.9),
                    "supports",
                    {"feature": feature.get("name"), "path": path},
                )

    for component in genome.get("architecture", {}).get("components", []):
        overlap = _score_overlap(requirement_text, f"{component.get('name', '')} {' '.join(component.get('evidence_paths', []))}")
        if overlap > 0:
            add(
                "architecture",
                component["id"],
                component.get("evidence_paths", [""])[0] if component.get("evidence_paths") else requirement.source_path,
                None,
                min(0.55 + 0.06 * overlap, 0.97),
                "supports",
                {"name": component.get("name"), "kind": component.get("kind"), "evidence_paths": component.get("evidence_paths", [])},
            )

    for interface in genome.get("architecture", {}).get("interfaces", []):
        overlap = _score_overlap(requirement_text, f"{interface.get('name', '')} {interface.get('kind', '')}")
        if overlap > 0:
            add(
                "implementation",
                interface["name"],
                interface.get("evidence_paths", [""])[0] if interface.get("evidence_paths") else requirement.source_path,
                None,
                min(0.45 + 0.05 * overlap, 0.92),
                "supports",
                {"name": interface.get("name"), "kind": interface.get("kind"), "evidence_paths": interface.get("evidence_paths", [])},
            )

    if any(token in tokens for token in ("test", "tests", "verify", "verification", "validated", "acceptance")):
        for path in genome.get("testing", {}).get("test_files", [])[:8]:
            add("test", path, path, None, 0.82, "supports", {"path": path})
        for path in genome.get("testing", {}).get("integration_test_evidence", [])[:8]:
            add("test", path, path, None, 0.8, "supports", {"path": path})

    if any(token in tokens for token in ("release", "ship", "deploy", "version")):
        for path in genome.get("releases", {}).get("discipline", {}).get("evidence_paths", [])[:8]:
            add("release", path, path, None, 0.84, "supports", {"path": path})
        for path in genome.get("documentation", {}).get("release_docs", [])[:8]:
            add("release", path, path, None, 0.84, "supports", {"path": path})

    if any(token in tokens for token in ("evidence", "verify", "validated", "validation", "traceability")):
        for path in genome.get("quality", {}).get("validation", {}).get("evidence_paths", [])[:8]:
            add("validation", path, path, None, 0.88, "supports", {"path": path})
        for path in genome.get("quality", {}).get("traceability", {}).get("evidence_paths", [])[:8]:
            add("validation", path, path, None, 0.86, "supports", {"path": path})

    if any(token in tokens for token in ("docs", "documentation", "guide", "adr", "readme")):
        for path in genome.get("documentation", {}).get("decision_records", [])[:8]:
            add("documentation", path, path, None, 0.78, "supports", {"path": path})
        for path in genome.get("documentation", {}).get("developer_docs", [])[:8]:
            add("documentation", path, path, None, 0.74, "supports", {"path": path})

    return evidence


def _requirement_links_by_type(evidence: list[RequirementEvidence], link_type: str) -> list[RequirementEvidence]:
    return [item for item in evidence if item.link_type == link_type]


def _requirement_state(evidence: list[RequirementEvidence]) -> str:
    has_feature = any(item.link_type == "feature" for item in evidence)
    has_architecture = any(item.link_type == "architecture" for item in evidence)
    has_test = any(item.link_type == "test" for item in evidence)
    has_validation = any(item.link_type == "validation" for item in evidence)
    has_release = any(item.link_type == "release" for item in evidence)
    if has_feature and has_architecture and has_test and has_validation and has_release:
        return "verified"
    if has_feature and has_architecture and has_test:
        return "confirmed"
    return "candidate"


def _persist_requirement_state(
    db_path: Path,
    requirement: RequirementCandidate,
    evidence: list[RequirementEvidence],
    *,
    operator_state: str | None = None,
    notes: str | None = None,
) -> None:
    conn = connect(db_path)
    conn.execute(
        """
        INSERT OR REPLACE INTO requirements(
            id, project_id, requirement_key, title, description, requirement_type, status, canonical_state,
            source, source_path, source_line, confidence, created_at, updated_at, provenance,
            related_feature_ids_json, related_architecture_json, related_test_paths_json,
            related_validation_json, related_release_json, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            requirement.id,
            requirement.project_id,
            requirement.requirement_key,
            requirement.title,
            requirement.description,
            requirement.requirement_type,
            operator_state or requirement.status,
            "canonical" if operator_state == "confirmed" else requirement.canonical_state,
            requirement.source,
            requirement.source_path,
            requirement.source_line,
            requirement.confidence,
            requirement.created_at,
            _utcnow(),
            requirement.provenance,
            _json_dumps(requirement.related_feature_ids),
            _json_dumps(requirement.related_architecture),
            _json_dumps(requirement.related_test_paths),
            _json_dumps(requirement.related_validation),
            _json_dumps(requirement.related_release),
            _json_dumps(requirement.metadata | ({'notes': notes} if notes else {})),
        ),
    )
    conn.execute("DELETE FROM requirement_evidence WHERE requirement_id=?", (requirement.id,))
    conn.execute("DELETE FROM requirement_reviews WHERE requirement_id=?", (requirement.id,))
    for item in evidence:
        conn.execute(
            """
            INSERT OR REPLACE INTO requirement_evidence(
                id, requirement_id, link_type, entity_id, source_path, source_line, confidence,
                supports_or_opposes, provenance, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item.id,
                item.requirement_id,
                item.link_type,
                item.entity_id,
                item.source_path,
                item.source_line,
                item.confidence,
                item.supports_or_opposes,
                item.provenance,
                _json_dumps(item.metadata),
            ),
        )
    if operator_state in {"confirmed", "rejected", "deferred"}:
        review = RequirementReview(
            id=f"review-{_stable_id(requirement.id, operator_state, notes or '')}",
            requirement_id=requirement.id,
            operator="operator",
            review_state=operator_state,
            notes=notes or "",
            metadata={"status": operator_state},
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO requirement_reviews(id, requirement_id, operator, review_state, notes, created_at, metadata_json)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                review.id,
                review.requirement_id,
                review.operator,
                review.review_state,
                review.notes,
                review.created_at,
                _json_dumps(review.metadata),
            ),
        )
    conn.commit()
    conn.close()


def _load_requirement_row(row: Any) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "requirement_key": row["requirement_key"],
        "title": row["title"],
        "description": row["description"],
        "requirement_type": row["requirement_type"],
        "status": row["status"],
        "canonical_state": row["canonical_state"],
        "source": row["source"],
        "source_path": row["source_path"],
        "source_line": row["source_line"],
        "confidence": row["confidence"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "provenance": row["provenance"],
        "related_feature_ids": _json_loads(row["related_feature_ids_json"], []),
        "related_architecture": _json_loads(row["related_architecture_json"], []),
        "related_test_paths": _json_loads(row["related_test_paths_json"], []),
        "related_validation": _json_loads(row["related_validation_json"], []),
        "related_release": _json_loads(row["related_release_json"], []),
        "metadata": _json_loads(row["metadata_json"], {}),
    }


def _load_requirement_evidence_row(row: Any) -> RequirementEvidence:
    return RequirementEvidence(
        id=row["id"],
        requirement_id=row["requirement_id"],
        link_type=row["link_type"],
        entity_id=row["entity_id"],
        source_path=row["source_path"],
        source_line=row["source_line"],
        confidence=row["confidence"],
        supports_or_opposes=row["supports_or_opposes"],
        provenance=row["provenance"],
        metadata=_json_loads(row["metadata_json"], {}),
    )


def _requirements_for_project(db_path: Path, project_id: str) -> list[dict[str, Any]]:
    conn = connect(db_path)
    rows = conn.execute("SELECT * FROM requirements WHERE project_id=? ORDER BY updated_at DESC, id DESC", (project_id,)).fetchall()
    conn.close()
    return [_load_requirement_row(row) for row in rows]


def _requirements_with_reviews(db_path: Path, project_id: str | None = None) -> list[dict[str, Any]]:
    conn = connect(db_path)
    if project_id:
        rows = conn.execute("SELECT * FROM requirements WHERE project_id=? ORDER BY updated_at DESC, id DESC", (project_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM requirements ORDER BY project_id, updated_at DESC, id DESC").fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        requirement = _load_requirement_row(row)
        evidence_rows = conn.execute("SELECT * FROM requirement_evidence WHERE requirement_id=? ORDER BY link_type, confidence DESC, id", (requirement["id"],)).fetchall()
        review_row = conn.execute("SELECT * FROM requirement_reviews WHERE requirement_id=? ORDER BY created_at DESC, id DESC LIMIT 1", (requirement["id"],)).fetchone()
        requirement["evidence"] = [dict(item) for item in evidence_rows]
        requirement["review"] = dict(review_row) if review_row else {}
        items.append(requirement)
    conn.close()
    return items


def _extract_requirement_candidates(db_path: Path, project_id: str, genome: dict[str, Any]) -> tuple[list[RequirementCandidate], list[RequirementEvidence], dict[str, Any]]:
    conn = connect(db_path)
    repo_root = _project_repo_root(conn, project_id)
    observations = _latest_scan_paths(conn, project_id)
    conn.close()
    candidate_paths = _candidate_paths(observations)
    requirements: list[RequirementCandidate] = []
    evidence_map: dict[str, list[RequirementEvidence]] = {}
    used_paths: list[str] = []
    for source_path in candidate_paths:
        text = _read_text(repo_root, source_path)
        if not text:
            continue
        file_tokens = _tokenize(text)
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            requirement = _parse_requirement_line(project_id, source_path, line_no, line, file_tokens)
            if requirement is None:
                continue
            if requirement.id in evidence_map:
                continue
            req_evidence = _evidence_for_requirement(genome, requirement)
            if not req_evidence:
                req_evidence = [
                    RequirementEvidence(
                        id=f"req-ev-{_stable_id(requirement.id, 'source', source_path, line_no)}",
                        requirement_id=requirement.id,
                        link_type="documentation",
                        entity_id=source_path,
                        source_path=source_path,
                        source_line=line_no,
                        confidence=0.7,
                        supports_or_opposes="supports",
                        provenance="document-line",
                        metadata={"line": line_no, "text": line[:240]},
                    )
                ]
            related_feature_ids = _uniq([item.entity_id for item in req_evidence if item.link_type == "feature"])
            related_architecture = [item.metadata for item in req_evidence if item.link_type == "architecture"]
            related_test_paths = _uniq([item.source_path for item in req_evidence if item.link_type == "test"])
            related_validation = _uniq([item.source_path for item in req_evidence if item.link_type == "validation"])
            related_release = _uniq([item.source_path for item in req_evidence if item.link_type == "release"])
            requirements.append(
                RequirementCandidate(
                    id=requirement.id,
                    project_id=requirement.project_id,
                    requirement_key=requirement.requirement_key,
                    title=requirement.title,
                    description=requirement.description,
                    requirement_type=requirement.requirement_type,
                    status=requirement.status,
                    canonical_state=requirement.canonical_state,
                    source=requirement.source,
                    source_path=requirement.source_path,
                    source_line=requirement.source_line,
                    confidence=requirement.confidence,
                    created_at=requirement.created_at,
                    updated_at=requirement.updated_at,
                    provenance=requirement.provenance,
                    related_feature_ids=related_feature_ids,
                    related_architecture=related_architecture,
                    related_test_paths=related_test_paths,
                    related_validation=related_validation,
                    related_release=related_release,
                    metadata=requirement.metadata,
                )
            )
            evidence_map[requirement.id] = req_evidence
            used_paths.append(source_path)
    requirements = sorted(requirements, key=lambda item: (item.project_id, item.source_path, item.source_line or 0, item.id))
    all_evidence = [item for items in evidence_map.values() for item in items]
    summary = {
        "project_id": project_id,
        "candidate_paths": _uniq(candidate_paths),
        "matched_paths": _uniq(used_paths),
        "candidate_count": len(requirements),
        "evidence_count": len(all_evidence),
    }
    return requirements, all_evidence, summary


def build_requirement_intelligence(db_path: Path, project_ids: list[str] | None = None, *, name: str = "default") -> dict[str, Any]:
    conn = connect(db_path)
    projects = _project_rows(conn, project_ids)
    conn.close()
    if not projects:
        return {
            "project_count": 0,
            "requirement_count": 0,
            "requirements": [],
            "gaps": [],
            "architecture_without_requirement": [],
            "verification_ready": [],
            "summary": {},
        }

    all_requirements: list[dict[str, Any]] = []
    all_evidence: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    scope_ids = [project["project_id"] for project in projects]
    for project in projects:
        genome = _ensure_genome(db_path, project["project_id"])
        requirements, evidence, summary = _extract_requirement_candidates(db_path, project["project_id"], genome)
        summaries.append(summary)
        evidence_by_requirement: dict[str, list[RequirementEvidence]] = {}
        for item in evidence:
            evidence_by_requirement.setdefault(item.requirement_id, []).append(item)
        for requirement in requirements:
            requirement_evidence = evidence_by_requirement.get(requirement.id, [])
            persisted = RequirementCandidate(
                id=requirement.id,
                project_id=requirement.project_id,
                requirement_key=requirement.requirement_key,
                title=requirement.title,
                description=requirement.description,
                requirement_type=requirement.requirement_type,
                status=_requirement_state(requirement_evidence),
                canonical_state="derived",
                source=requirement.source,
                source_path=requirement.source_path,
                source_line=requirement.source_line,
                confidence=requirement.confidence,
                created_at=requirement.created_at,
                updated_at=requirement.updated_at,
                provenance=requirement.provenance,
                related_feature_ids=_uniq(requirement.related_feature_ids),
                related_architecture=requirement.related_architecture,
                related_test_paths=_uniq(requirement.related_test_paths),
                related_validation=_uniq(requirement.related_validation),
                related_release=_uniq(requirement.related_release),
                metadata=requirement.metadata,
            )
            _persist_requirement_state(db_path, persisted, requirement_evidence)
        all_requirements.extend([req.to_dict() for req in requirements])
        all_evidence.extend([item.to_dict() for item in evidence])

    analysis = requirement_inventory(db_path, project_ids=scope_ids)
    return {
        "project_count": len(projects),
        "scope": scope_ids if len(scope_ids) > 1 else scope_ids[:1],
        "requirement_count": analysis["count"],
        "requirements": analysis["items"],
        "gaps": requirement_gaps(db_path, project_ids=scope_ids)["items"],
        "architecture_without_requirement": architecture_without_requirement(db_path, project_ids=scope_ids)["items"],
        "verification_ready": verification_readiness(db_path, project_ids=scope_ids)["items"],
        "summaries": summaries,
        "summary": {
            "candidate_count": len(all_requirements),
            "evidence_count": len(all_evidence),
        },
    }


def requirement_inventory(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    if project_ids:
        placeholders = ", ".join(["?"] * len(project_ids))
        rows = conn.execute(
            f"SELECT * FROM requirements WHERE project_id IN ({placeholders}) ORDER BY project_id, status, updated_at DESC, id DESC",
            tuple(project_ids),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM requirements ORDER BY project_id, status, updated_at DESC, id DESC").fetchall()
    conn.close()
    items = [_load_requirement_row(row) for row in rows]
    return {"count": len(items), "items": items}


def requirement_show(db_path: Path, requirement_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = conn.execute("SELECT * FROM requirements WHERE id=?", (requirement_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Unknown requirement: {requirement_id}")
    evidence_rows = conn.execute("SELECT * FROM requirement_evidence WHERE requirement_id=? ORDER BY link_type, confidence DESC, id", (requirement_id,)).fetchall()
    review_row = conn.execute("SELECT * FROM requirement_reviews WHERE requirement_id=? ORDER BY created_at DESC, id DESC LIMIT 1", (requirement_id,)).fetchone()
    conn.close()
    return {
        "requirement": _load_requirement_row(row),
        "evidence": [dict(item) for item in evidence_rows],
        "review": dict(review_row) if review_row else {},
    }


def requirement_trace(db_path: Path, requirement_id: str) -> dict[str, Any]:
    shown = requirement_show(db_path, requirement_id)
    requirement = shown["requirement"]
    evidence = shown["evidence"]
    grouped: dict[str, list[dict[str, Any]]] = {link_type: [] for link_type in sorted(LINK_TYPES)}
    for item in evidence:
        grouped.setdefault(item["link_type"], []).append(item)
    return {
        "requirement": requirement,
        "evidence": evidence,
        "links": grouped,
        "verification_ready": _requirement_state([_load_requirement_evidence_row(item) for item in evidence]),
        "gaps": _requirement_gaps_for_requirement(requirement, evidence),
    }


def _requirement_gaps_for_requirement(requirement: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    link_types = {item["link_type"] for item in evidence}
    gaps: list[str] = []
    if "feature" not in link_types:
        gaps.append("no_feature_link")
    if "architecture" not in link_types:
        gaps.append("no_architecture_link")
    if "test" not in link_types:
        gaps.append("no_test_evidence")
    if "validation" not in link_types:
        gaps.append("no_validation_evidence")
    if "release" not in link_types:
        gaps.append("no_release_evidence")
    if requirement.get("canonical_state") != "canonical":
        gaps.append("not_canonical")
    return gaps


def requirement_gaps(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    analysis = requirement_inventory(db_path, project_ids=project_ids)
    items = []
    for requirement in analysis["items"]:
        shown = requirement_show(db_path, requirement["id"])
        gaps = _requirement_gaps_for_requirement(shown["requirement"], shown["evidence"])
        if gaps:
            items.append(
                {
                    "requirement_id": requirement["id"],
                    "project_id": requirement["project_id"],
                    "title": requirement["title"],
                    "requirement_type": requirement["requirement_type"],
                    "gaps": gaps,
                    "confidence": requirement["confidence"],
                }
            )
    return {"count": len(items), "items": items}


def verification_readiness(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    analysis = requirement_inventory(db_path, project_ids=project_ids)
    items = []
    for requirement in analysis["items"]:
        shown = requirement_show(db_path, requirement["id"])
        gaps = _requirement_gaps_for_requirement(shown["requirement"], shown["evidence"])
        if not gaps:
            items.append(
                {
                    "requirement_id": requirement["id"],
                    "project_id": requirement["project_id"],
                    "title": requirement["title"],
                    "requirement_type": requirement["requirement_type"],
                    "status": "verified",
                    "confidence": requirement["confidence"],
                }
            )
    return {"count": len(items), "items": items}


def architecture_without_requirement(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    projects = _project_rows(conn, project_ids)
    rows: list[dict[str, Any]] = []
    for project in projects:
        genome = _ensure_genome(db_path, project["project_id"])
        requirements = _requirements_for_project(db_path, project["project_id"])
        linked_architecture_ids = {item["entity_id"] for requirement in requirements for item in requirement_show(db_path, requirement["id"])["evidence"] if item["link_type"] == "architecture"}
        linked_architecture_ids.update({item["entity_id"] for requirement in requirements for item in requirement_show(db_path, requirement["id"])["evidence"] if item["link_type"] == "implementation"})
        for component in genome.get("architecture", {}).get("components", []):
            if component["id"] not in linked_architecture_ids:
                rows.append(
                    {
                        "project_id": project["project_id"],
                        "architecture_id": component["id"],
                        "architecture_name": component.get("name", component["id"]),
                        "confidence": component.get("confidence", 0.5),
                        "evidence_paths": component.get("evidence_paths", []),
                    }
                )
    conn.close()
    return {"count": len(rows), "items": rows}


def unimplemented_requirements(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    analysis = requirement_inventory(db_path, project_ids=project_ids)
    items = []
    for requirement in analysis["items"]:
        evidence = requirement_show(db_path, requirement["id"])["evidence"]
        if not any(item["link_type"] in {"feature", "architecture", "implementation"} for item in evidence):
            items.append(requirement)
    return {"count": len(items), "items": items}


def untested_requirements(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    analysis = requirement_inventory(db_path, project_ids=project_ids)
    items = []
    for requirement in analysis["items"]:
        evidence = requirement_show(db_path, requirement["id"])["evidence"]
        if not any(item["link_type"] == "test" for item in evidence):
            items.append(requirement)
    return {"count": len(items), "items": items}


def requirement_history(db_path: Path, project_ids: list[str] | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    if project_ids:
        placeholders = ", ".join(["?"] * len(project_ids))
        rows = conn.execute(
            f"SELECT r.*, rev.review_state, rev.operator, rev.notes FROM requirements r LEFT JOIN requirement_reviews rev ON rev.requirement_id = r.id WHERE r.project_id IN ({placeholders}) ORDER BY r.updated_at DESC, r.id DESC",
            tuple(project_ids),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT r.*, rev.review_state, rev.operator, rev.notes FROM requirements r LEFT JOIN requirement_reviews rev ON rev.requirement_id = r.id ORDER BY r.updated_at DESC, r.id DESC"
        ).fetchall()
    conn.close()
    items = []
    for row in rows:
        requirement = _load_requirement_row(row)
        requirement["review_state"] = row.get("review_state", None)
        requirement["operator"] = row.get("operator", None)
        requirement["notes"] = row.get("notes", None)
        items.append(requirement)
    return {"count": len(items), "items": items}


def confirm_requirement(db_path: Path, requirement_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    shown = requirement_show(db_path, requirement_id)
    requirement = RequirementCandidate(
        id=shown["requirement"]["id"],
        project_id=shown["requirement"]["project_id"],
        requirement_key=shown["requirement"]["requirement_key"],
        title=shown["requirement"]["title"],
        description=shown["requirement"]["description"],
        requirement_type=shown["requirement"]["requirement_type"],
        status="confirmed",
        canonical_state="canonical",
        source=shown["requirement"]["source"],
        source_path=shown["requirement"]["source_path"],
        source_line=shown["requirement"]["source_line"],
        confidence=shown["requirement"]["confidence"],
        created_at=shown["requirement"]["created_at"],
        updated_at=_utcnow(),
        provenance=shown["requirement"]["provenance"],
        related_feature_ids=shown["requirement"]["related_feature_ids"],
        related_architecture=shown["requirement"]["related_architecture"],
        related_test_paths=shown["requirement"]["related_test_paths"],
        related_validation=shown["requirement"]["related_validation"],
        related_release=shown["requirement"]["related_release"],
        metadata=shown["requirement"]["metadata"],
    )
    evidence = [_load_requirement_evidence_row(item) for item in shown["evidence"]]
    _persist_requirement_state(db_path, requirement, evidence, operator_state="confirmed", notes=notes or operator)
    return {"requirement_id": requirement_id, "status": "confirmed", "canonical_state": "canonical"}


def reject_requirement(db_path: Path, requirement_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    shown = requirement_show(db_path, requirement_id)
    requirement = RequirementCandidate(
        id=shown["requirement"]["id"],
        project_id=shown["requirement"]["project_id"],
        requirement_key=shown["requirement"]["requirement_key"],
        title=shown["requirement"]["title"],
        description=shown["requirement"]["description"],
        requirement_type=shown["requirement"]["requirement_type"],
        status="rejected",
        canonical_state="derived",
        source=shown["requirement"]["source"],
        source_path=shown["requirement"]["source_path"],
        source_line=shown["requirement"]["source_line"],
        confidence=shown["requirement"]["confidence"],
        created_at=shown["requirement"]["created_at"],
        updated_at=_utcnow(),
        provenance=shown["requirement"]["provenance"],
        related_feature_ids=shown["requirement"]["related_feature_ids"],
        related_architecture=shown["requirement"]["related_architecture"],
        related_test_paths=shown["requirement"]["related_test_paths"],
        related_validation=shown["requirement"]["related_validation"],
        related_release=shown["requirement"]["related_release"],
        metadata=shown["requirement"]["metadata"],
    )
    evidence = [_load_requirement_evidence_row(item) for item in shown["evidence"]]
    _persist_requirement_state(db_path, requirement, evidence, operator_state="rejected", notes=notes or operator)
    return {"requirement_id": requirement_id, "status": "rejected"}


def defer_requirement(db_path: Path, requirement_id: str, *, operator: str = "operator", notes: str = "") -> dict[str, Any]:
    shown = requirement_show(db_path, requirement_id)
    requirement = RequirementCandidate(
        id=shown["requirement"]["id"],
        project_id=shown["requirement"]["project_id"],
        requirement_key=shown["requirement"]["requirement_key"],
        title=shown["requirement"]["title"],
        description=shown["requirement"]["description"],
        requirement_type=shown["requirement"]["requirement_type"],
        status="deferred",
        canonical_state="derived",
        source=shown["requirement"]["source"],
        source_path=shown["requirement"]["source_path"],
        source_line=shown["requirement"]["source_line"],
        confidence=shown["requirement"]["confidence"],
        created_at=shown["requirement"]["created_at"],
        updated_at=_utcnow(),
        provenance=shown["requirement"]["provenance"],
        related_feature_ids=shown["requirement"]["related_feature_ids"],
        related_architecture=shown["requirement"]["related_architecture"],
        related_test_paths=shown["requirement"]["related_test_paths"],
        related_validation=shown["requirement"]["related_validation"],
        related_release=shown["requirement"]["related_release"],
        metadata=shown["requirement"]["metadata"],
    )
    evidence = [_load_requirement_evidence_row(item) for item in shown["evidence"]]
    _persist_requirement_state(db_path, requirement, evidence, operator_state="deferred", notes=notes or operator)
    return {"requirement_id": requirement_id, "status": "deferred"}
