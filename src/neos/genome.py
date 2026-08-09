from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect

GENOME_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProjectGenome:
    project_id: str
    scan_id: str
    source_commit: str | None
    source_branch: str | None
    generated_at: str
    genome_schema_version: int
    identity: dict[str, Any]
    technologies: list[dict[str, Any]]
    architecture: dict[str, Any]
    domains: list[dict[str, Any]]
    features: list[dict[str, Any]]
    testing: dict[str, Any]
    documentation: dict[str, Any]
    configuration: dict[str, Any]
    apis: dict[str, Any]
    engineering_decisions: list[dict[str, Any]]
    hardware: dict[str, Any]
    software: dict[str, Any]
    releases: dict[str, Any]
    quality: dict[str, Any]
    maturity: dict[str, Any]
    risks: list[dict[str, Any]]
    technical_debt: list[dict[str, Any]]
    reuse: list[dict[str, Any]]
    unknowns: list[dict[str, Any]]
    confidence: dict[str, Any]
    evidence: dict[str, Any]
    history: dict[str, Any]
    project_health: dict[str, Any]
    attention: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _git_commit(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _git_branch(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


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
        """
        SELECT *
        FROM project_genomes
        WHERE project_id=?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (project_id,),
    ).fetchone()


def _genome_rows(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM project_genomes
        WHERE project_id=?
        ORDER BY created_at DESC, id DESC
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _scan_snapshot(conn, scan_id: str | None) -> dict[str, Any]:
    if not scan_id:
        return {}
    row = conn.execute("SELECT * FROM scans WHERE scan_id=?", (scan_id,)).fetchone()
    return dict(row) if row else {}


def _observations(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT source_path, kind, label, content_hash, metadata_json
        FROM scan_observations
        WHERE project_id=?
        ORDER BY source_path, kind, label
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _scan_observation_paths(conn, project_id: str, kinds: set[str] | None = None) -> list[str]:
    query = "SELECT source_path, kind FROM scan_observations WHERE project_id=? ORDER BY source_path"
    rows = conn.execute(query, (project_id,)).fetchall()
    paths = []
    for row in rows:
        if kinds and row["kind"] not in kinds:
            continue
        paths.append(row["source_path"])
    return paths


def _count_by_kind(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1
    return counts


def _count_paths(paths: list[str], tokens: tuple[str, ...]) -> tuple[int, list[str]]:
    matches = [path for path in paths if any(token in path.lower() for token in tokens)]
    return len(matches), matches


def _category_paths(paths: list[str], category: str) -> tuple[int, list[str]]:
    tokens_by_category = {
        "implementation": ("src/", "software/", ".py", ".dart", ".cpp", ".h", ".ino", ".ino", ".c"),
        "testing": ("test", "spec", "validation"),
        "documentation": ("docs/", "readme", "guide", "adr", ".md"),
        "integration": ("api", "contracts", "workflows", "platformio", "pubspec", "flutter", "project_control"),
        "validation": ("validation", "results", "checklist", "acceptance", "health", "verification"),
        "release": ("release", "releases", "changelog", "rc"),
        "config": ("config", "platformio.ini", "pubspec.yaml", "project.neos.json", ".json", ".toml", ".yaml", ".yml", ".ini"),
        "security": ("security", "secret", "credential", "threat"),
        "hardware": ("hardware", "sensor", "relay", "esp32", "calibration", "firmware"),
    }
    return _count_paths(paths, tokens_by_category[category])


def _score_from_counts(count: int, threshold: int, weight: int) -> dict[str, Any]:
    ratio = 0.0 if threshold <= 0 else min(count / threshold, 1.0)
    score = round(ratio * weight)
    return {"count": count, "threshold": threshold, "weight": weight, "score": score, "ratio": round(ratio, 3)}


def _tech_rules() -> list[dict[str, Any]]:
    return [
        {"name": "PlatformIO", "category": "build system", "tokens": ("platformio.ini", ".pio", "platformio"), "version": None, "source": "path-heuristic"},
        {"name": "ESP32", "category": "embedded platform", "tokens": ("esp32", "esp-idf", "esp32s3", "esp32s2"), "version": None, "source": "path-heuristic"},
        {"name": "Flutter", "category": "mobile application framework", "tokens": ("flutter", "pubspec.yaml", "flutter_app"), "version": None, "source": "path-heuristic"},
        {"name": "Dart", "category": "language", "tokens": ("pubspec.yaml", "flutter_app", ".dart"), "version": None, "source": "path-heuristic"},
        {"name": "Python", "category": "language", "tokens": (".py", "pyproject.toml", "requirements", "pytest"), "version": None, "source": "path-heuristic"},
        {"name": "GitHub Actions", "category": "ci system", "tokens": (".github/workflows",), "version": None, "source": "path-heuristic"},
        {"name": "Markdown", "category": "documentation", "tokens": (".md", "readme"), "version": None, "source": "path-heuristic"},
        {"name": "SQLite", "category": "database", "tokens": (".sqlite", ".db", "sqlite"), "version": None, "source": "path-heuristic"},
        {"name": "FastAPI", "category": "web framework", "tokens": ("fastapi", "router.py", "api_route", "app/routers"), "version": None, "source": "path-heuristic"},
    ]


def _domain_rules() -> list[dict[str, Any]]:
    return [
        {"name": "firmware", "description": "Embedded firmware and low-level device code.", "tokens": ("firmware", "platformio", "esp32", "embedded"), "kind": "core"},
        {"name": "application", "description": "User-facing application code and integration glue.", "tokens": ("flutter", "app/", "software/flutter_app"), "kind": "core"},
        {"name": "configuration", "description": "Project and runtime configuration.", "tokens": ("config", "canonical.json", "project.neos.json", "platformio.ini", "pubspec.yaml"), "kind": "support"},
        {"name": "testing", "description": "Testing and validation assets.", "tokens": ("test", "tests", "validation", "acceptance"), "kind": "quality"},
        {"name": "documentation", "description": "User, architecture and release documentation.", "tokens": ("docs/", "readme", "guide", "adr"), "kind": "knowledge"},
        {"name": "api", "description": "HTTP or data interface boundaries.", "tokens": ("api", "router", "endpoint", "contracts"), "kind": "interface"},
        {"name": "device communication", "description": "Discovery, pairing and transport boundaries.", "tokens": ("pairing", "discovery", "wifi", "mqtt", "espnow", "communication"), "kind": "interface"},
        {"name": "hardware", "description": "Sensors, controllers and bench evidence.", "tokens": ("hardware", "sensor", "relay", "calibration", "bench"), "kind": "core"},
        {"name": "diagnostics", "description": "Health checks, logs and diagnostics.", "tokens": ("diagnostic", "health", "logs"), "kind": "support"},
        {"name": "release management", "description": "Release notes, gates and validation evidence.", "tokens": ("release", "releases", "changelog", "rc"), "kind": "support"},
        {"name": "project control", "description": "Project control-plane tooling and reports.", "tokens": ("project_control", "control"), "kind": "support"},
    ]


def _group_top_paths(paths: list[str], limit: int = 20) -> list[str]:
    return sorted(dict.fromkeys(paths))[:limit]


def _technology_profile(conn, project_row: Any, scan_snapshot: dict[str, Any], observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [row["source_path"] for row in observations]
    manifest = _json_loads(project_row["manifest_json"], {})
    manifest_techs = manifest.get("technologies", []) if isinstance(manifest, dict) else []
    technology_rows: list[dict[str, Any]] = []

    for rule in _tech_rules():
        count, matched_paths = _count_paths(paths, rule["tokens"])
        if rule["name"] in manifest_techs:
            count = max(count, 1)
            matched_paths = matched_paths or [project_row["manifest_path"]]
        if count == 0:
            continue
        technology_rows.append(
            {
                "name": rule["name"],
                "category": rule["category"],
                "version": rule["version"],
                "source": rule["source"] if rule["name"] not in manifest_techs else "manifest+path-heuristic",
                "confidence": round(min(0.55 + 0.1 * count, 0.99), 3),
                "evidence_paths": _group_top_paths(matched_paths),
                "usage_count": count,
            }
        )

    for tech in manifest_techs:
        if any(row["name"] == tech for row in technology_rows):
            continue
        technology_rows.append(
            {
                "name": tech,
                "category": "manifest technology",
                "version": None,
                "source": "manifest",
                "confidence": 0.75,
                "evidence_paths": [project_row["manifest_path"]],
                "usage_count": 1,
            }
        )
    technology_rows.sort(key=lambda row: (-row["confidence"], row["name"].lower()))
    return technology_rows


def _feature_evidence_groups(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT f.id, f.name, f.status, f.source, f.confidence, f.description, f.metadata_json,
               e.source_path, e.evidence_type
        FROM features f
        LEFT JOIN feature_evidence e ON e.feature_id = f.id
        WHERE f.project_id=?
        ORDER BY f.confidence DESC, f.name, e.source_path
        """,
        (project_id,),
    ).fetchall()
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        feature = grouped.setdefault(
            row["id"],
            {
                "id": row["id"],
                "name": row["name"],
                "status": row["status"],
                "source": row["source"],
                "confidence": row["confidence"],
                "description": row["description"],
                "metadata": _json_loads(row["metadata_json"], {}),
                "evidence_paths": [],
            },
        )
        if row["source_path"]:
            feature["evidence_paths"].append(row["source_path"])
    return list(grouped.values())


def _feature_maturity(feature: dict[str, Any], scan_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    evidence_paths = _group_top_paths(feature.get("evidence_paths", []), limit=20)
    implementation_paths: list[str] = []
    test_paths: list[str] = []
    documentation_paths: list[str] = []
    integration_paths: list[str] = []
    validation_paths: list[str] = []
    release_paths: list[str] = []
    config_paths: list[str] = []
    hardware_paths: list[str] = []
    for path in evidence_paths:
        lowered = path.lower()
        if any(token in lowered for token in ("test", "spec")):
            test_paths.append(path)
        if any(token in lowered for token in ("docs/", "readme", "guide", "adr", ".md")):
            documentation_paths.append(path)
        if any(token in lowered for token in ("release", "changelog", "rc")):
            release_paths.append(path)
        if any(token in lowered for token in ("validation", "results", "checklist", "acceptance", "health")):
            validation_paths.append(path)
        if any(token in lowered for token in ("api", "contracts", "workflows", "platformio", "pubspec", "flutter", "project_control")):
            integration_paths.append(path)
        if any(token in lowered for token in ("config", "platformio.ini", "pubspec.yaml", "project.neos.json", ".json", ".toml", ".yaml", ".yml", ".ini")):
            config_paths.append(path)
        if any(token in lowered for token in ("hardware", "sensor", "relay", "calibration", "bench", "firmware")):
            hardware_paths.append(path)
        if any(token in lowered for token in ("src/", "software/", ".py", ".dart", ".cpp", ".h", ".c")):
            implementation_paths.append(path)

    impl = _score_from_counts(len(implementation_paths), 3, 30)
    tests = _score_from_counts(len(test_paths), 2, 20)
    docs = _score_from_counts(len(documentation_paths), 2, 15)
    integration = _score_from_counts(len(integration_paths), 2, 15)
    validation = _score_from_counts(len(validation_paths), 1, 10)
    release = _score_from_counts(len(release_paths), 1, 10)
    total = impl["score"] + tests["score"] + docs["score"] + integration["score"] + validation["score"] + release["score"]
    evidence_paths = sorted(dict.fromkeys(evidence_paths))
    score = {
        "score": total,
        "label": "experimental" if total < 40 else "developing" if total < 65 else "maturing" if total < 85 else "established",
        "components": [
            {"name": "implementation", **impl, "evidence_paths": _group_top_paths(implementation_paths)},
            {"name": "testing", **tests, "evidence_paths": _group_top_paths(test_paths)},
            {"name": "documentation", **docs, "evidence_paths": _group_top_paths(documentation_paths)},
            {"name": "integration", **integration, "evidence_paths": _group_top_paths(integration_paths)},
            {"name": "validation", **validation, "evidence_paths": _group_top_paths(validation_paths)},
            {"name": "release", **release, "evidence_paths": _group_top_paths(release_paths)},
        ],
        "evidence_paths": evidence_paths,
        "signals": {
            "config_paths": _group_top_paths(config_paths),
            "hardware_paths": _group_top_paths(hardware_paths),
        },
    }
    confidence = round(min(0.55 + 0.05 * len(evidence_paths), 0.99), 3)
    if feature["status"] == "validated":
        confidence = min(0.99, confidence + 0.03)
    return {"feature_id": feature["id"], "name": feature["name"], "status": feature["status"], "source": feature["source"], "confidence": confidence, "maturity": score}


def _feature_maturity_summary(feature_rows: list[dict[str, Any]], scan_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    matured = [_feature_maturity(feature, scan_index) for feature in feature_rows]
    average = round(sum(item["maturity"]["score"] for item in matured) / len(matured), 1) if matured else 0.0
    return {
        "items": matured,
        "summary": {
            "average_score": average,
            "matured_count": sum(1 for item in matured if item["maturity"]["score"] >= 65),
            "experimental_count": sum(1 for item in matured if item["maturity"]["score"] < 40),
        },
    }


def _project_maturity(genome: dict[str, Any]) -> dict[str, Any]:
    feature_scores = [item["maturity"]["score"] for item in genome["features"]]
    docs = genome["documentation"]["coverage"]["score"]
    tests = genome["testing"]["coverage"]["score"]
    release = genome["releases"]["discipline"]["score"]
    traceability = genome["quality"]["traceability"]["score"]
    decisions = genome["quality"]["decision_traceability"]["score"]
    config = genome["configuration"]["coverage"]["score"]
    validation = genome["quality"]["validation"]["score"]
    security = genome["quality"]["security"]["score"]
    architecture = genome["architecture"]["coverage"]["score"]
    implementation = round(sum(feature_scores) / len(feature_scores)) if feature_scores else 0

    components = [
        {"name": "architecture", "score": architecture, "weight": 15, "evidence": genome["architecture"]["coverage"]["evidence_paths"]},
        {"name": "implementation", "score": implementation, "weight": 20, "evidence": genome["features"][0]["maturity"]["evidence_paths"][:10] if genome["features"] else []},
        {"name": "testing", "score": tests, "weight": 15, "evidence": genome["testing"]["coverage"]["evidence_paths"]},
        {"name": "documentation", "score": docs, "weight": 10, "evidence": genome["documentation"]["coverage"]["evidence_paths"]},
        {"name": "release discipline", "score": release, "weight": 10, "evidence": genome["releases"]["discipline"]["evidence_paths"]},
        {"name": "traceability", "score": traceability, "weight": 10, "evidence": genome["quality"]["traceability"]["evidence_paths"]},
        {"name": "engineering decisions", "score": decisions, "weight": 10, "evidence": genome["engineering_decisions"][:5]},
        {"name": "configuration management", "score": config, "weight": 5, "evidence": genome["configuration"]["coverage"]["evidence_paths"]},
        {"name": "validation", "score": validation, "weight": 3, "evidence": genome["quality"]["validation"]["evidence_paths"]},
        {"name": "security evidence", "score": security, "weight": 2, "evidence": genome["quality"]["security"]["evidence_paths"]},
    ]
    total = sum(item["score"] for item in components)
    return {"score": total, "label": "healthy" if total >= 75 else "attention" if total >= 50 else "risk" if total >= 30 else "unknown", "components": components}


def _coverage_from_paths(paths: list[str], category: str, weight: int, threshold: int) -> dict[str, Any]:
    count, matched_paths = _category_paths(paths, category)
    score = _score_from_counts(count, threshold, weight)
    score["evidence_paths"] = _group_top_paths(matched_paths)
    return score


def _scan_kind_counts(observations: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in observations:
        counts[row["kind"]] = counts.get(row["kind"], 0) + 1
    return counts


def _semantic_lookup(conn, table: str, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT * FROM {table} WHERE project_id=? ORDER BY id", (project_id,)).fetchall()
    return [dict(row) for row in rows]


def _top_path_groups(paths: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        parts = Path(path).parts
        if len(parts) >= 2:
            key = "/".join(parts[:2])
        elif parts:
            key = parts[0]
        else:
            key = path
        groups.setdefault(key, []).append(path)
    return groups


def _build_domains(conn, project_id: str, observations: list[dict[str, Any]], features: list[dict[str, Any]], symbols: list[dict[str, Any]], apis: list[dict[str, Any]], configs: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_paths = [row["source_path"] for row in observations]
    domains: list[dict[str, Any]] = []
    for rule in _domain_rules():
        matched_features = [feature for feature in features if any(token in feature["name"].lower() for token in rule["tokens"]) or any(token in " ".join(feature.get("evidence_paths", [])).lower() for token in rule["tokens"])]
        matched_paths = [path for path in all_paths if any(token in path.lower() for token in rule["tokens"])]
        matched_symbols = [symbol for symbol in symbols if any(token in symbol["source_path"].lower() or token in symbol["name"].lower() for token in rule["tokens"])]
        matched_apis = [api for api in apis if any(token in api["route"].lower() or token in api.get("handler", "").lower() for token in rule["tokens"])]
        matched_configs = [config for config in configs if any(token in config["source_path"].lower() or token in config["key"].lower() for token in rule["tokens"])]
        matched_decisions = [decision for decision in decisions if any(token in decision["title"].lower() or token in decision["source_path"].lower() for token in rule["tokens"])]
        if not (matched_features or matched_paths or matched_symbols or matched_apis or matched_configs or matched_decisions):
            continue
        evidence_paths = _group_top_paths(matched_paths or [feature_path for feature in matched_features for feature_path in feature.get("evidence_paths", [])])
        confidence = round(min(0.45 + 0.05 * (len(matched_features) + len(matched_paths)), 0.98), 3)
        domains.append(
            {
                "id": _stable_id("domain", project_id, rule["name"]),
                "name": rule["name"],
                "description": rule["description"],
                "project_id": project_id,
                "confidence": confidence,
                "status": "candidate",
                "kind": rule["kind"],
                "features": [{"id": feature["id"], "name": feature["name"], "status": feature["status"]} for feature in matched_features],
                "artefacts": _group_top_paths(matched_paths),
                "symbols": _group_top_paths([symbol["source_path"] for symbol in matched_symbols]),
                "tests": _group_top_paths([path for path in matched_paths if "test" in path.lower()]),
                "apis": _group_top_paths([api["route"] for api in matched_apis]),
                "config": _group_top_paths([config["source_path"] for config in matched_configs]),
                "dependencies": [],
                "decisions": _group_top_paths([decision["source_path"] for decision in matched_decisions]),
                "documentation": _group_top_paths([path for path in matched_paths if any(token in path.lower() for token in ("docs/", "readme", "guide", "adr"))]),
                "release_evidence": _group_top_paths([path for path in matched_paths if "release" in path.lower() or "validation" in path.lower()]),
                "unknowns": [],
                "evidence_paths": evidence_paths,
            }
        )
    domains.sort(key=lambda item: (-item["confidence"], item["name"]))
    return domains


def _architecture_model(project_id: str, domains: list[dict[str, Any]], observations: list[dict[str, Any]], dependencies: list[dict[str, Any]], symbols: list[dict[str, Any]], apis: list[dict[str, Any]], configs: list[dict[str, Any]]) -> dict[str, Any]:
    groups = _top_path_groups([row["source_path"] for row in observations if row["source_path"]])
    components: list[dict[str, Any]] = []
    for group_name, paths in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        if len(paths) < 2 and group_name not in {"docs", "tests"}:
            continue
        components.append(
            {
                "id": _stable_id("component", project_id, group_name),
                "name": group_name,
                "kind": "component",
                "confidence": round(min(0.5 + 0.03 * len(paths), 0.98), 3),
                "evidence_paths": _group_top_paths(paths),
            }
        )
    if not components:
        components = [{"id": _stable_id("component", project_id, "repository"), "name": "repository", "kind": "component", "confidence": 0.5, "evidence_paths": []}]
    layers = [
        {"name": "documentation", "confidence": 0.8, "evidence_paths": [path for path in groups.get("docs", [])[:20]]},
        {"name": "testing", "confidence": 0.8, "evidence_paths": [path for path in groups.get("tests", [])[:20]]},
        {"name": "application", "confidence": 0.75, "evidence_paths": [path for path in groups.get("software", [])[:20]]},
        {"name": "tooling", "confidence": 0.75, "evidence_paths": [path for path in groups.get("tools", [])[:20]]},
    ]
    interfaces = []
    for api in apis[:20]:
        interfaces.append({"name": api["route"], "kind": "api", "confidence": api["confidence"], "evidence_paths": [api["source_path"]]})
    for config in configs[:20]:
        interfaces.append({"name": config["key"], "kind": "configuration", "confidence": config["confidence"], "evidence_paths": [config["source_path"]]})
    boundaries = []
    dep_groups: dict[tuple[str, str], list[str]] = {}
    for dep in dependencies:
        src = dep.get("source_entity_id", "source")
        tgt = dep.get("target_entity_id", "target")
        dep_groups.setdefault((src, tgt), []).append(dep["id"])
    for (src, tgt), dep_ids in list(dep_groups.items())[:20]:
        boundaries.append({"source": src, "target": tgt, "confidence": 0.6, "dependency_ids": dep_ids[:10]})
    coverage = _score_from_counts(len(components) + len(interfaces), 10, 100)
    coverage["evidence_paths"] = _group_top_paths([path for component in components for path in component["evidence_paths"]])
    return {"components": components, "layers": layers, "interfaces": interfaces, "boundaries": boundaries, "coverage": coverage}


def _project_evidence_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _count_by_kind(observations)
    return {
        "total_paths": len(observations),
        "by_kind": counts,
        "paths": _group_top_paths([row["source_path"] for row in observations]),
    }


def _testing_genome(conn, project_id: str, observations: list[dict[str, Any]], symbols: list[dict[str, Any]], features: list[dict[str, Any]]) -> dict[str, Any]:
    test_files = [row["source_path"] for row in observations if row["kind"] == "test"]
    test_symbols = [symbol for symbol in symbols if symbol["kind"] in {"test_function", "test_class", "test"}]
    frameworks = []
    symbol_paths = {symbol["source_path"] for symbol in symbols}
    if any("pytest" in path.lower() for path in test_files) or test_symbols:
        frameworks.append({"name": "pytest", "confidence": 0.9, "evidence_paths": _group_top_paths(test_files[:20] or list(symbol_paths)[:20])})
    feature_tests = []
    for feature in features:
        evidence_paths = feature.get("evidence_paths", [])
        matching_tests = [path for path in evidence_paths if any(token in path.lower() for token in ("test", "spec", "validation"))]
        feature_tests.append(
            {
                "feature_id": feature["id"],
                "feature_name": feature["name"],
                "tested": bool(matching_tests),
                "status": "tested" if matching_tests else "test evidence unknown",
                "evidence_paths": _group_top_paths(matching_tests),
                "confidence": round(min(0.4 + 0.1 * len(matching_tests), 0.95), 3),
            }
        )
    coverage = _score_from_counts(sum(1 for item in feature_tests if item["tested"]), max(len(features), 1), 100)
    coverage["evidence_paths"] = _group_top_paths(test_files + [path for item in feature_tests for path in item["evidence_paths"]])
    return {
        "test_files": _group_top_paths(test_files),
        "test_functions": test_symbols,
        "frameworks": frameworks,
        "features_with_tests": [item for item in feature_tests if item["tested"]],
        "features_without_tests": [item for item in feature_tests if not item["tested"]],
        "domains_with_tests": [],
        "untested_symbols": [symbol for symbol in symbols if symbol["kind"] not in {"test_function", "test_class", "test"}][:20],
        "hardware_validation_evidence": _group_top_paths([row["source_path"] for row in observations if "validation" in row["source_path"].lower() or "hardware" in row["source_path"].lower()]),
        "integration_test_evidence": _group_top_paths([row["source_path"] for row in observations if any(token in row["source_path"].lower() for token in ("integration", "acceptance", "contract", "end_to_end"))]),
        "coverage": coverage,
    }


def _documentation_genome(observations: list[dict[str, Any]], features: list[dict[str, Any]]) -> dict[str, Any]:
    docs = [row["source_path"] for row in observations if row["kind"] in {"documentation", "release_documentation"}]
    release_docs = [path for path in docs if "release" in path.lower()]
    feature_docs = []
    for feature in features:
        evidence_paths = feature.get("evidence_paths", [])
        doc_paths = [path for path in evidence_paths if any(token in path.lower() for token in ("docs/", "readme", "guide", "adr", ".md"))]
        feature_docs.append(
            {
                "feature_id": feature["id"],
                "feature_name": feature["name"],
                "documented": bool(doc_paths),
                "status": "documented" if doc_paths else "documentation unknown",
                "evidence_paths": _group_top_paths(doc_paths),
                "confidence": round(min(0.4 + 0.1 * len(doc_paths), 0.95), 3),
            }
        )
    coverage = _score_from_counts(len(docs), 10, 100)
    coverage["evidence_paths"] = _group_top_paths(docs)
    return {
        "architecture_docs": _group_top_paths([path for path in docs if "architecture" in path.lower()]),
        "developer_docs": _group_top_paths([path for path in docs if "developer" in path.lower() or "guide" in path.lower()]),
        "user_guides": _group_top_paths([path for path in docs if "user" in path.lower() or "guide" in path.lower()]),
        "api_docs": _group_top_paths([path for path in docs if "api" in path.lower()]),
        "release_docs": _group_top_paths(release_docs),
        "decision_records": _group_top_paths([path for path in docs if "adr" in path.lower() or "decision" in path.lower()]),
        "testing_docs": _group_top_paths([path for path in docs if any(token in path.lower() for token in ("test", "validation"))]),
        "hardware_docs": _group_top_paths([path for path in docs if any(token in path.lower() for token in ("hardware", "sensor", "firmware"))]),
        "planning_docs": _group_top_paths([path for path in docs if any(token in path.lower() for token in ("roadmap", "plan", "next_steps", "checklist"))]),
        "features_with_documentation": [item for item in feature_docs if item["documented"]],
        "features_without_documentation": [item for item in feature_docs if not item["documented"]],
        "domains_with_documentation": [],
        "stale_document_candidates": [],
        "coverage": coverage,
    }


def _configuration_genome(conn, project_id: str, configs: list[dict[str, Any]]) -> dict[str, Any]:
    paths = [config["source_path"] for config in configs]
    coverage = _score_from_counts(len(configs), 20, 100)
    coverage["evidence_paths"] = _group_top_paths(paths)
    return {
        "configuration_files": _group_top_paths(paths),
        "keys": configs[:200],
        "coverage": coverage,
        "concentration": _top_path_groups(paths),
    }


def _api_genome(apis: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "endpoints": apis[:200],
        "routes": [api["route"] for api in apis],
        "coverage": _score_from_counts(len(apis), 10, 100),
    }


def _decisions_genome(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": decision["id"],
            "title": decision["title"],
            "status": decision["status"],
            "date": decision.get("date"),
            "confidence": decision.get("confidence", 0.0),
            "source_path": decision["source_path"],
            "context": decision.get("context", ""),
            "decision": decision.get("decision", ""),
            "rationale": decision.get("rationale", ""),
            "alternatives": decision.get("alternatives", ""),
            "consequences": decision.get("consequences", ""),
            "evidence_paths": [decision["source_path"]],
        }
        for decision in decisions
    ]


def _quality_model(conn, project_id: str, observations: list[dict[str, Any]], decisions: list[dict[str, Any]], features: list[dict[str, Any]], test_genome: dict[str, Any], docs_genome: dict[str, Any]) -> dict[str, Any]:
    scan_paths = [row["source_path"] for row in observations]
    traceability = _score_from_counts(len(decisions), 3, 100)
    validation = _score_from_counts(len(test_genome["test_files"]) + len(test_genome["integration_test_evidence"]), 5, 100)
    security = _score_from_counts(len([path for path in scan_paths if any(token in path.lower() for token in ("secret", "credential", "security"))]), 1, 100)
    if not security["count"]:
        security["score"] = 90
        security["ratio"] = 1.0
    decision_traceability = _score_from_counts(sum(1 for decision in decisions if decision.get("source_path")), max(len(decisions), 1), 100)
    feature_coverage = _score_from_counts(len(test_genome["features_with_tests"]), max(len(features), 1), 100)
    return {
        "traceability": {**traceability, "evidence_paths": _group_top_paths([decision["source_path"] for decision in decisions])},
        "validation": {**validation, "evidence_paths": test_genome["integration_test_evidence"]},
        "security": {**security, "evidence_paths": _group_top_paths([path for path in scan_paths if any(token in path.lower() for token in ("secret", "credential", "security"))])},
        "decision_traceability": {**decision_traceability, "evidence_paths": _group_top_paths([decision["source_path"] for decision in decisions])},
        "feature_coverage": feature_coverage,
        "unknowns": [],
    }


def _release_model(observations: list[dict[str, Any]]) -> dict[str, Any]:
    release_paths = [row["source_path"] for row in observations if row["kind"] == "release_documentation" or "release" in row["source_path"].lower()]
    discipline = _score_from_counts(len(release_paths), 5, 100)
    discipline["evidence_paths"] = _group_top_paths(release_paths)
    return {"discipline": discipline}


def _find_dependencies(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, source_entity_id, target_entity_id, dependency_type, confidence, evidence_source, scan_id, parser_source, created_at, metadata_json
        FROM dependencies
        WHERE project_id=?
        ORDER BY dependency_type, id
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _find_relationships(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, source_entity_id, target_entity_id, relationship_type, confidence, evidence_source, scan_id, parser_source, created_at, metadata_json
        FROM relationships
        WHERE project_id=?
        ORDER BY relationship_type, id
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _find_features(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, project_id, scan_id, name, description, status, introduced_version, removed_version, confidence, source, created_at, updated_at, provenance, metadata_json
        FROM features
        WHERE project_id=?
        ORDER BY confidence DESC, name
        """,
        (project_id,),
    ).fetchall()
    features = [dict(row) for row in rows]
    for feature in features:
        evidence = conn.execute(
            "SELECT source_path FROM feature_evidence WHERE feature_id=? ORDER BY source_path",
            (feature["id"],),
        ).fetchall()
        feature["evidence_paths"] = [row["source_path"] for row in evidence]
    return features


def _find_symbols(conn, project_id: str) -> list[dict[str, Any]]:
    return _semantic_lookup(conn, "symbols", project_id)


def _find_apis(conn, project_id: str) -> list[dict[str, Any]]:
    return _semantic_lookup(conn, "api_endpoints", project_id)


def _find_configs(conn, project_id: str) -> list[dict[str, Any]]:
    return _semantic_lookup(conn, "configuration_keys", project_id)


def _find_decisions(conn, project_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, project_id, scan_id, title, status, date, context, decision, rationale, alternatives, consequences, source_path, confidence, provenance, created_at, observed_at, metadata_json
        FROM engineering_decisions
        WHERE project_id=?
        ORDER BY date, title
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _find_unknowns(genome: dict[str, Any], observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unknowns: list[dict[str, Any]] = []
    for item in genome["features"]:
        if item["maturity"]["score"] < 45:
            unknowns.append(
                {
                    "id": _stable_id("unknown", genome["project_id"], item["feature_id"], "feature-coverage"),
                    "title": f"Feature coverage unknown for {item['name']}",
                    "category": "test coverage unknown",
                    "severity": "medium",
                    "confidence": round(0.6 + (45 - item["maturity"]["score"]) / 200, 3),
                    "reason": "Feature maturity is low enough that the implementation or validation surface remains partially unknown.",
                    "evidence": item["maturity"]["evidence_paths"][:10],
                    "affected_entities": [item["feature_id"]],
                    "recommended_investigation": f"Inspect the implementation and validation surface for {item['name']}.",
                }
            )
    if not any(any(token in row["source_path"].lower() for token in ("release", "rc")) for row in observations):
        unknowns.append(
            {
                "id": _stable_id("unknown", genome["project_id"], "release-provenance"),
                "title": "Release provenance unknown",
                "category": "release provenance unknown",
                "severity": "medium",
                "confidence": 0.72,
                "reason": "The current evidence does not show strong release verification for every major capability.",
                "evidence": [path for path in genome["evidence"]["paths"] if "release" in path.lower()][:10],
                "affected_entities": [genome["project_id"]],
                "recommended_investigation": "Review release notes, acceptance evidence and validation logs for missing coverage.",
            }
        )
    return unknowns


def _technical_debt(conn, genome: dict[str, Any], repo_root: Path, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    debt: list[dict[str, Any]] = []
    marker_paths: list[str] = []
    for base, _, files in os_walk(repo_root):
        for file_name in files:
            path = base / file_name
            rel = path.relative_to(repo_root).as_posix()
            if any(part.startswith((".neos", ".git")) for part in rel.split("/")):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "todo" in text.lower() or "fixme" in text.lower():
                marker_paths.append(rel)
    if marker_paths:
        debt.append(
            {
                "id": _stable_id("debt", genome["project_id"], "todo-fixme"),
                "title": "TODO/FIXME markers present",
                "category": "code hygiene",
                "severity": "low",
                "confidence": 0.75,
                "reason": "Repository text contains explicit TODO or FIXME markers.",
                "evidence": _group_top_paths(marker_paths),
                "affected_entities": [],
                "recommended_investigation": "Review open TODO/FIXME notes and decide whether they represent tracked work.",
            }
        )
    return debt


def os_walk(repo_root: Path):
    for base, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {".git", ".neos", ".venv", "__pycache__", "node_modules", "build", "dist"}]
        yield Path(base), dirs, files


def _reuse_candidates(genome: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for component in genome["architecture"]["components"][:8]:
        if len(component.get("evidence_paths", [])) < 2:
            continue
        candidates.append(
            {
                "name": component["name"],
                "source": "architecture-component",
                "reason": "Component has a clear evidence-backed boundary and repeated evidence paths.",
                "dependencies": [],
                "tests": [],
                "confidence": round(component["confidence"], 3),
                "possible_reuse_domains": [domain["name"] for domain in genome["domains"][:3]],
            }
        )
    for feature in genome["features"]:
        if feature["maturity"]["score"] >= 65:
            candidates.append(
                {
                    "name": feature["name"],
                    "source": "feature-maturity",
                    "reason": "Feature maturity is high enough to consider reuse across similar projects.",
                    "dependencies": [],
                    "tests": feature["maturity"]["components"][1]["evidence_paths"],
                    "confidence": round(feature["confidence"], 3),
                    "possible_reuse_domains": [domain["name"] for domain in genome["domains"][:2]],
                }
            )
    return candidates[:10]


def _risk_items(genome: dict[str, Any]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for item in genome["testing"]["features_without_tests"][:10]:
        risks.append(
            {
                "id": _stable_id("risk", genome["project_id"], item["feature_id"], "untested"),
                "title": f"Feature without test evidence: {item['feature_name']}",
                "category": "testing gap",
                "severity": "high" if item["status"] != "tested" else "medium",
                "confidence": item["confidence"],
                "reason": "Feature maturity lacks test evidence in the current canonical scan state.",
                "evidence": item["evidence_paths"],
                "affected_entities": [item["feature_id"]],
                "recommended_investigation": f"Add or link test evidence for {item['feature_name']}.",
            }
        )
    for item in genome["documentation"]["features_without_documentation"][:10]:
        risks.append(
            {
                "id": _stable_id("risk", genome["project_id"], item["feature_id"], "undocumented"),
                "title": f"Feature without documentation: {item['feature_name']}",
                "category": "documentation gap",
                "severity": "medium",
                "confidence": item["confidence"],
                "reason": "Feature maturity lacks documentation evidence in the current canonical scan state.",
                "evidence": item["evidence_paths"],
                "affected_entities": [item["feature_id"]],
                "recommended_investigation": f"Add or link documentation for {item['feature_name']}.",
            }
        )
    if genome["quality"]["traceability"]["score"] < 60:
        risks.append(
            {
                "id": _stable_id("risk", genome["project_id"], "traceability"),
                "title": "Weak traceability surface",
                "category": "traceability",
                "severity": "medium",
                "confidence": 0.75,
                "reason": "Decision and evidence traceability remain incomplete relative to project scale.",
                "evidence": genome["quality"]["traceability"]["evidence_paths"][:10],
                "affected_entities": [genome["project_id"]],
                "recommended_investigation": "Review how major features are linked to decisions, tests and release evidence.",
            }
        )
    return risks[:20]


def _attention_items(genome: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = sorted(genome["risks"], key=lambda item: (-{"high": 3, "medium": 2, "low": 1}.get(item["severity"], 0), -item["confidence"], item["title"]))
    attention: list[dict[str, Any]] = []
    for risk in ranked[:10]:
        attention.append(
            {
                "what": risk["title"],
                "why": risk["reason"],
                "evidence": risk["evidence"][:10],
                "confidence": risk["confidence"],
                "suggested_next_action": risk["recommended_investigation"],
            }
        )
    return attention


def _confidence_summary(genome: dict[str, Any]) -> dict[str, Any]:
    evidence_paths = genome["evidence"]["paths"]
    return {
        "score": round(min(0.6 + 0.02 * len(evidence_paths), 0.98), 3),
        "explanation": "Confidence increases with evidence breadth and repeated semantic corroboration.",
        "evidence_paths": evidence_paths[:20],
    }


def _fingerprint(project_id: str, scan_id: str, source_commit: str | None, source_branch: str | None, genome_schema_version: int) -> str:
    payload = json.dumps(
        {
            "project_id": project_id,
            "scan_id": scan_id,
            "source_commit": source_commit,
            "source_branch": source_branch,
            "genome_schema_version": genome_schema_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_project_genome(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = _project_row(conn, project_id)
    scan = _latest_scan_row(conn, project_id)
    if not scan:
        conn.close()
        raise ValueError(f"No scans available for project: {project_id}")
    repo_root = Path(project["repo_path"])
    scan_snapshot = _scan_snapshot(conn, scan["scan_id"])
    source_commit = scan["git_commit"] or _git_commit(repo_root)
    source_branch = scan["git_branch"] or _git_branch(repo_root)
    source_fingerprint = _fingerprint(project_id, scan["scan_id"], source_commit, source_branch, GENOME_SCHEMA_VERSION)
    existing = conn.execute(
        """
        SELECT *
        FROM project_genomes
        WHERE project_id=? AND source_fingerprint=? AND genome_schema_version=?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (project_id, source_fingerprint, GENOME_SCHEMA_VERSION),
    ).fetchone()
    if existing:
        genome = _json_loads(existing["genome_json"], {})
        conn.close()
        return {
            "genome": genome,
            "stored": False,
            "snapshot": dict(existing),
        }

    observations = _observations(conn, project_id)
    symbols = _find_symbols(conn, project_id)
    apis = _find_apis(conn, project_id)
    configs = _find_configs(conn, project_id)
    decisions = _find_decisions(conn, project_id)
    features = _find_features(conn, project_id)
    dependencies = _find_dependencies(conn, project_id)
    _find_relationships(conn, project_id)

    technology_rows = _technology_profile(conn, project, scan_snapshot, observations)
    feature_maturity = _feature_maturity_summary(features, {row["source_path"]: row for row in observations})

    genome_data: dict[str, Any] = {
        "project_id": project_id,
        "scan_id": scan["scan_id"],
        "source_commit": source_commit,
        "source_branch": source_branch,
        "generated_at": utc_now(),
        "genome_schema_version": GENOME_SCHEMA_VERSION,
        "identity": {
            "project_id": project_id,
            "name": project["name"],
            "repo_path": project["repo_path"],
            "manifest_path": project["manifest_path"],
            "lifecycle": project["lifecycle"],
        },
        "technologies": technology_rows,
        "domains": [],
        "features": feature_maturity["items"],
        "architecture": {},
        "testing": {},
        "documentation": {},
        "configuration": {},
        "apis": {},
        "engineering_decisions": _decisions_genome(decisions),
        "hardware": {},
        "software": {},
        "releases": {},
        "quality": {},
        "maturity": {},
        "risks": [],
        "technical_debt": [],
        "reuse": [],
        "unknowns": [],
        "confidence": {},
        "evidence": _project_evidence_summary(observations),
        "history": {"previous_genomes": _genome_rows(conn, project_id)},
        "project_health": {},
        "attention": [],
    }
    genome_data["testing"] = _testing_genome(conn, project_id, observations, symbols, features)
    genome_data["documentation"] = _documentation_genome(observations, features)
    genome_data["configuration"] = _configuration_genome(conn, project_id, configs)
    genome_data["apis"] = _api_genome(apis)
    genome_data["domains"] = _build_domains(conn, project_id, observations, features, symbols, apis, configs, decisions)
    genome_data["architecture"] = _architecture_model(project_id, genome_data["domains"], observations, dependencies, symbols, apis, configs)
    genome_data["releases"] = _release_model(observations)
    genome_data["quality"] = _quality_model(conn, project_id, observations, decisions, features, genome_data["testing"], genome_data["documentation"])
    genome_data["maturity"] = _project_maturity(genome_data)
    genome_data["risks"] = _risk_items(genome_data)
    genome_data["technical_debt"] = _technical_debt(conn, genome_data, repo_root, observations)
    genome_data["reuse"] = _reuse_candidates(genome_data)
    genome_data["unknowns"] = _find_unknowns(genome_data, observations)
    genome_data["confidence"] = _confidence_summary(genome_data)
    genome_data["project_health"] = {
        "score": genome_data["maturity"]["score"],
        "status": genome_data["maturity"]["label"],
        "dimension_scores": {
            "scan freshness": 100 if scan_snapshot and scan_snapshot.get("created_at") else 0,
            "repository cleanliness": 100,
            "test evidence": genome_data["testing"]["coverage"]["score"],
            "documentation coverage": genome_data["documentation"]["coverage"]["score"],
            "feature maturity": genome_data["features"][0]["maturity"]["score"] if genome_data["features"] else 0,
            "known risk count": max(0, 100 - len(genome_data["risks"]) * 5),
            "decision traceability": genome_data["quality"]["decision_traceability"]["score"],
            "release evidence": genome_data["releases"]["discipline"]["score"],
            "unknown areas": max(0, 100 - len(genome_data["unknowns"]) * 10),
        },
        "calculation": "Deterministic aggregate of maturity, quality and evidence coverage dimensions.",
        "evidence": genome_data["evidence"]["paths"][:20],
    }
    genome_data["attention"] = _attention_items(genome_data)

    summary = {
        "technologies": len(genome_data["technologies"]),
        "domains": len(genome_data["domains"]),
        "features": len(genome_data["features"]),
        "risks": len(genome_data["risks"]),
        "unknowns": len(genome_data["unknowns"]),
        "reuse": len(genome_data["reuse"]),
    }
    metrics = {
        "feature_maturity_average": genome_data["features"][0]["maturity"]["score"] if genome_data["features"] else 0,
        "maturity_score": genome_data["maturity"]["score"],
        "health_score": genome_data["project_health"]["score"],
        "evidence_paths": len(genome_data["evidence"]["paths"]),
    }
    conn.execute(
        """
        INSERT INTO project_genomes(
            id, project_id, scan_id, source_commit, source_branch, genome_schema_version,
            source_fingerprint, created_at, summary_json, genome_json, metrics_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            _stable_id("genome", project_id, source_fingerprint),
            project_id,
            scan["scan_id"],
            source_commit,
            source_branch,
            GENOME_SCHEMA_VERSION,
            source_fingerprint,
            genome_data["generated_at"],
            json.dumps(summary, sort_keys=True),
            json.dumps(genome_data, sort_keys=True),
            json.dumps(metrics, sort_keys=True),
        ),
    )
    conn.commit()
    snapshot = conn.execute("SELECT * FROM project_genomes WHERE project_id=? AND source_fingerprint=?", (project_id, source_fingerprint)).fetchone()
    conn.close()
    return {"genome": genome_data, "stored": True, "snapshot": dict(snapshot) if snapshot else {}}


def latest_project_genome(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    row = _latest_genome_row(conn, project_id)
    conn.close()
    if not row:
        return {}
    return _json_loads(row["genome_json"], {})


def genome_summary(genome: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": genome["project_id"],
        "scan_id": genome["scan_id"],
        "generated_at": genome["generated_at"],
        "genome_schema_version": genome["genome_schema_version"],
        "identity": genome["identity"],
        "technology_count": len(genome["technologies"]),
        "domain_count": len(genome["domains"]),
        "feature_count": len(genome["features"]),
        "risk_count": len(genome["risks"]),
        "unknown_count": len(genome["unknowns"]),
        "reuse_count": len(genome["reuse"]),
        "maturity": genome["maturity"],
        "health": genome["project_health"],
        "attention_count": len(genome["attention"]),
    }


def genome_domains(genome: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": genome["project_id"], "count": len(genome["domains"]), "items": genome["domains"]}


def genome_risks(genome: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": genome["project_id"], "count": len(genome["risks"]), "items": genome["risks"]}


def genome_unknowns(genome: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": genome["project_id"], "count": len(genome["unknowns"]), "items": genome["unknowns"]}


def genome_health(genome: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": genome["project_id"], "health": genome["project_health"]}


def genome_attention(genome: dict[str, Any]) -> dict[str, Any]:
    return {"project_id": genome["project_id"], "count": len(genome["attention"]), "items": genome["attention"]}


def _diff_lists(before: list[dict[str, Any]], after: list[dict[str, Any]], key: str = "id") -> dict[str, list[dict[str, Any]]]:
    before_map = {row.get(key): row for row in before}
    after_map = {row.get(key): row for row in after}
    added = [after_map[item] for item in sorted(set(after_map) - set(before_map), key=str)]
    removed = [before_map[item] for item in sorted(set(before_map) - set(after_map), key=str)]
    changed = []
    for item in sorted(set(before_map) & set(after_map), key=str):
        if json.dumps(before_map[item], sort_keys=True, default=str) != json.dumps(after_map[item], sort_keys=True, default=str):
            changed.append({"before": before_map[item], "after": after_map[item]})
    return {"added": added, "removed": removed, "changed": changed}


def genome_diff(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    rows = _genome_rows(conn, project_id)
    conn.close()
    if not rows:
        raise ValueError(f"No genomes available for project: {project_id}")
    latest = _json_loads(rows[0]["genome_json"], {})
    previous = _json_loads(rows[1]["genome_json"], {}) if len(rows) > 1 else {}
    if not previous:
        return {
            "project_id": project_id,
            "latest_genome_id": rows[0]["id"],
            "previous_genome_id": None,
            "changes": {
                "new_features": latest.get("features", []),
                "removed_features": [],
                "new_technologies": latest.get("technologies", []),
                "removed_technologies": [],
                "new_risks": latest.get("risks", []),
                "resolved_risks": [],
                "new_unknowns": latest.get("unknowns", []),
                "resolved_unknowns": [],
                "maturity_changes": [],
                "architecture_changes": [],
                "test_changes": [],
                "documentation_changes": [],
            },
        }
    feature_diff = _diff_lists(previous.get("features", []), latest.get("features", []), "feature_id")
    tech_diff = _diff_lists(previous.get("technologies", []), latest.get("technologies", []), "name")
    risk_diff = _diff_lists(previous.get("risks", []), latest.get("risks", []), "id")
    unknown_diff = _diff_lists(previous.get("unknowns", []), latest.get("unknowns", []), "id")
    return {
        "project_id": project_id,
        "latest_genome_id": rows[0]["id"],
        "previous_genome_id": rows[1]["id"],
        "changes": {
            "new_features": feature_diff["added"],
            "removed_features": feature_diff["removed"],
            "new_technologies": tech_diff["added"],
            "removed_technologies": tech_diff["removed"],
            "new_risks": risk_diff["added"],
            "resolved_risks": risk_diff["removed"],
            "new_unknowns": unknown_diff["added"],
            "resolved_unknowns": unknown_diff["removed"],
            "maturity_changes": [previous.get("maturity", {}), latest.get("maturity", {})],
            "architecture_changes": [previous.get("architecture", {}), latest.get("architecture", {})],
            "test_changes": [previous.get("testing", {}), latest.get("testing", {})],
            "documentation_changes": [previous.get("documentation", {}), latest.get("documentation", {})],
        },
    }


def render_project_report(genome: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": genome["project_id"],
        "sections": {
            "Executive summary": {
                "maturity": genome["maturity"],
                "health": genome["project_health"],
                "attention": genome["attention"][:5],
            },
            "Project identity": genome["identity"],
            "Architecture": genome["architecture"],
            "Technology stack": genome["technologies"],
            "Engineering domains": genome["domains"],
            "Current capabilities": genome["features"],
            "Feature maturity": genome["features"],
            "Testing": genome["testing"],
            "Documentation": genome["documentation"],
            "Engineering decisions": genome["engineering_decisions"],
            "Dependencies": genome["configuration"],
            "Risks": genome["risks"],
            "Technical debt": genome["technical_debt"],
            "Reusable components": genome["reuse"],
            "Unknown areas": genome["unknowns"],
            "Recommended engineering focus": genome["attention"],
        },
    }


def genome_markdown_report(genome: dict[str, Any]) -> str:
    lines = [f"# Project Report: {genome['identity']['name']}", ""]
    lines.append("## Executive summary")
    lines.append(f"- Maturity: {genome['maturity']['score']} / 100 ({genome['maturity']['label']})")
    lines.append(f"- Health: {genome['project_health']['status']} ({genome['project_health']['score']})")
    lines.append(f"- Technologies: {len(genome['technologies'])}")
    lines.append(f"- Domains: {len(genome['domains'])}")
    lines.append(f"- Risks: {len(genome['risks'])}")
    lines.append("")
    lines.append("## Recommended engineering focus")
    for item in genome["attention"][:10]:
        lines.append(f"- {item['what']}: {item['suggested_next_action']}")
    lines.append("")
    lines.append("## Unknown areas")
    for item in genome["unknowns"][:10]:
        lines.append(f"- {item['title']}: {item['reason']}")
    return "\n".join(lines).strip() + "\n"
