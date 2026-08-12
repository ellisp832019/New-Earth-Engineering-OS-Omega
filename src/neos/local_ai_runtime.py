from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

yaml: Any
try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is available in the dev env, but keep safe fallback.
    yaml = None

LOCAL_AI_RUNTIME_SCHEMA_VERSION = 1
LOCAL_AI_RUNTIME_RESULT_STATES = {"READY", "READY_WITH_WARNINGS", "NOT_READY", "UNKNOWN"}
LOCAL_AI_RUNTIME_FINDING_STATUSES = {"PASS", "WARNING", "ERROR", "UNKNOWN"}
LOCAL_AI_RUNTIME_SEVERITIES = {"INFO", "WARNING", "ERROR", "BLOCKER"}

_DEFAULT_PLATFORM_CORE_ENV_VARS = ("NEOS_PLATFORM_CORE_ROOT", "NEOS_PLATFORM_CORE_REPO")
_DEFAULT_GAIA_ENV_VARS = ("NEOS_GAIA_ROOT", "NEOS_AIE_ROOT", "NEOS_AI_EMPLOYEE_ROOT")
_DEFAULT_RUNTIME_ENV_VARS = ("NEOS_LOCAL_AI_RUNTIME_ROOT", "NEOS_LOCAL_AI_RUNTIME_REPO")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _normalize_text(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9/]+", " ", str(value or "").lower().replace("_", " ").replace("-", " "))
    return " ".join(cleaned.split()).strip()


def _first_existing_path(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_structured_document(path: Path) -> dict[str, Any] | None:
    raw = _read_text(path)
    if raw is None:
        return None
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return None
    elif suffix in {".yaml", ".yml"} and yaml is not None:
        try:
            loaded = yaml.safe_load(raw)
        except yaml.YAMLError:
            return None
    else:
        return None
    return loaded if isinstance(loaded, dict) else None


def _git_output(repo_path: Path | None, *args: str) -> str | None:
    if repo_path is None:
        return None
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return None
    return output.strip() or None


def _git_dirty(repo_path: Path | None) -> bool | None:
    output = _git_output(repo_path, "status", "--porcelain")
    if output is None:
        return None
    return bool(output)


def _resolve_root(root: str | Path | None, env_vars: tuple[str, ...]) -> Path | None:
    if root is not None:
        return Path(root).expanduser().resolve()
    for env_var in env_vars:
        raw = os.environ.get(env_var, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return None


def _repo_snapshot(repo_root: Path | None) -> dict[str, Any]:
    if repo_root is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "repo_root_not_supplied",
            "root": None,
            "git": {"branch": None, "commit": None, "dirty": None, "remote": None},
        }
    if not repo_root.exists():
        return {
            "status": "UNAVAILABLE",
            "reason": "repo_root_missing",
            "root": str(repo_root),
            "git": {"branch": None, "commit": None, "dirty": None, "remote": None},
        }
    return {
        "status": "AVAILABLE",
        "reason": "observed",
        "root": str(repo_root.resolve()),
        "git": {
            "branch": _git_output(repo_root, "branch", "--show-current"),
            "commit": _git_output(repo_root, "rev-parse", "HEAD"),
            "dirty": _git_dirty(repo_root),
            "remote": _git_output(repo_root, "remote", "get-url", "origin"),
        },
    }


def _file_evidence(repo_root: Path | None, relative_path: str) -> dict[str, Any]:
    if repo_root is None:
        return {"path": relative_path, "exists": False, "status": "UNAVAILABLE", "reason": "repo_root_not_supplied"}
    path = repo_root / relative_path
    text = _read_text(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": "AVAILABLE" if text is not None else "MISSING",
        "text": text,
    }


def _structured_evidence(repo_root: Path | None, relative_paths: Iterable[str]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if repo_root is None:
        return None, {"status": "UNAVAILABLE", "reason": "repo_root_not_supplied", "path": None}
    path = _first_existing_path(repo_root / candidate for candidate in relative_paths)
    if path is None:
        return None, {"status": "MISSING", "reason": "document_missing", "path": None}
    document = _read_structured_document(path)
    if document is None:
        return None, {"status": "MISSING", "reason": "document_unreadable", "path": str(path)}
    return document, {"status": "AVAILABLE", "reason": "document_loaded", "path": str(path)}


def _text_evidence(repo_root: Path | None, relative_paths: Iterable[str]) -> dict[str, Any]:
    if repo_root is None:
        return {"status": "UNAVAILABLE", "reason": "repo_root_not_supplied", "path": None, "text": None}
    path = _first_existing_path(repo_root / candidate for candidate in relative_paths)
    if path is None:
        return {"status": "MISSING", "reason": "document_missing", "path": None, "text": None}
    text = _read_text(path)
    if text is None:
        return {"status": "MISSING", "reason": "document_unreadable", "path": str(path), "text": None}
    return {"status": "AVAILABLE", "reason": "document_loaded", "path": str(path), "text": text}


def _scan_text_matches(text: str | None, needles: Iterable[str]) -> dict[str, bool]:
    normalized = _normalize_text(text)
    return {needle: _normalize_text(needle) in normalized for needle in needles}


def _scan_source_files(root: Path | None, relative_paths: Iterable[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if root is None:
        return result
    for relative_path in relative_paths:
        path = root / relative_path
        text = _read_text(path)
        result[relative_path] = {
            "path": str(path),
            "exists": path.exists(),
            "text": text,
        }
    return result


def _scan_for_patterns(root: Path | None, *, includes: Iterable[str] = ("src",), excludes: Iterable[str] = ("tests", "docs", "__pycache__")) -> list[dict[str, Any]]:
    if root is None or not root.exists():
        return []
    hits: list[dict[str, Any]] = []
    include_prefixes = tuple(includes)
    exclude_prefixes = tuple(excludes)
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        parts = relative.parts
        if include_prefixes and not any(part == prefix or str(relative).startswith(prefix + os.sep) for prefix in include_prefixes for part in parts[:1]):
            continue
        if any(part in exclude_prefixes for part in parts):
            continue
        text = _read_text(path)
        if text is None:
            continue
        findings: list[str] = []
        for pattern in (
            r"subprocess\.(run|call|Popen)\([^)]*ollama",
            r"os\.system\([^)]*ollama",
            r"shell=True[^\\n]*ollama",
            r"command\s*=\s*[^\\n]*ollama",
            r"\bollama\b.*(run|pull|serve|chat|generate)",
        ):
            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                findings.append(pattern)
        if findings:
            hits.append({"path": str(path), "patterns": findings})
    return hits


def _finding(
    *,
    rule_id: str,
    status: str,
    severity: str,
    subject: str,
    explanation: str,
    evidence: dict[str, Any],
    affected: dict[str, Any] | None = None,
    confidence: float = 0.9,
) -> dict[str, Any]:
    payload = {
        "rule_id": rule_id,
        "status": status,
        "severity": severity,
        "subject": subject,
        "explanation": explanation,
        "evidence": evidence,
        "affected": affected or {},
        "confidence": confidence,
    }
    finding = dict(payload)
    finding["id"] = f"{rule_id.lower()}-{_stable_hash(payload)[:12]}"
    return finding


def _summary(
    findings: list[dict[str, Any]],
    *,
    platform_core_status: str,
    runtime_repo_status: str,
    gaia_repo_status: str,
    runtime_service_status: str,
    exclude_rule_ids: set[str] | None = None,
) -> dict[str, Any]:
    excluded = exclude_rule_ids or set()
    active_findings = [item for item in findings if item["rule_id"] not in excluded]
    status_counts = Counter(item["status"] for item in active_findings)
    severity_counts = Counter(item["severity"] for item in active_findings)
    if any(item["severity"] == "BLOCKER" or item["status"] == "ERROR" for item in active_findings):
        readiness = "NOT_READY"
    elif any(item["status"] == "WARNING" for item in active_findings):
        readiness = "READY_WITH_WARNINGS"
    elif any(item["status"] == "UNKNOWN" for item in active_findings):
        readiness = "UNKNOWN"
    else:
        readiness = "READY"
    if readiness not in LOCAL_AI_RUNTIME_RESULT_STATES:
        readiness = "UNKNOWN"
    return {
        "readiness": readiness,
        "finding_count": len(active_findings),
        "status_counts": dict(status_counts),
        "severity_counts": dict(severity_counts),
        "platform_core_status": platform_core_status,
        "runtime_repo_status": runtime_repo_status,
        "gaia_repo_status": gaia_repo_status,
        "runtime_service_status": runtime_service_status,
    }


def _observe_platform_core(platform_core_root: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = _repo_snapshot(platform_core_root)
    if snapshot["status"] != "AVAILABLE":
        return {
            **snapshot,
            "governance": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "integration_doc": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "contract_example": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
        }, {}

    governance_doc, governance_doc_status = _structured_evidence(
        platform_core_root,
        ("registry/governance.yaml", "registry/governance.yml", "registry/governance.json"),
    )
    integration_doc = _text_evidence(platform_core_root, ("docs/integrations/LOCAL_AI_RUNTIME.md",))
    contract_doc, contract_status = _structured_evidence(
        platform_core_root,
        ("examples/contracts/NEW_EARTH_LOCAL_AI_RUNTIME.NEW_EARTH_PROJECT.yaml", "examples/contracts/NEW_EARTH_LOCAL_AI_RUNTIME.NEW_EARTH_PROJECT.yml", "examples/contracts/NEW_EARTH_LOCAL_AI_RUNTIME.NEW_EARTH_PROJECT.json"),
    )
    declared_interfaces = []
    declared_services = []
    if isinstance(governance_doc, dict):
        for key in ("interfaces", "services"):
            declared_services.extend(_safe_list(governance_doc.get(key)))
        declared_interfaces = [
            str(item).strip()
            for item in _safe_list(governance_doc.get("interfaces"))
            if str(item).strip()
        ]
    declared_text = integration_doc.get("text") or ""
    declared_text_matches = _scan_text_matches(
        declared_text,
        (
            "Local AI Runtime",
            "GET /health",
            "GET /v1/status",
            "GET /v1/models",
            "POST /v1/chat",
            "POST /v1/generate",
            "POST /v1/embeddings",
            "POST /v1/route/explain",
            "POST /v1/context/provenance",
            "GET /v1/impact/advisory",
        ),
    )
    status = "AVAILABLE"
    if governance_doc_status["status"] != "AVAILABLE" or integration_doc["status"] != "AVAILABLE" or contract_status["status"] != "AVAILABLE":
        status = "MISSING"
    if isinstance(governance_doc, dict) and governance_doc.get("schema_version") not in {1, "1"}:
        status = "SCHEMA_MISMATCH"
    return {
        **snapshot,
        "status": status,
        "governance": {
            "status": governance_doc_status["status"],
            "path": governance_doc_status["path"],
            "document": governance_doc,
        },
        "integration_doc": {
            "status": integration_doc["status"],
            "path": integration_doc["path"],
            "matches": declared_text_matches,
        },
        "contract_example": {
            "status": contract_status["status"],
            "path": contract_status["path"],
            "document": contract_doc,
        },
        "declared_interfaces": declared_interfaces,
        "declared_services": declared_services,
    }, {
        "governance_doc": governance_doc,
        "integration_doc": integration_doc,
        "contract_doc": contract_doc,
    }


def _observe_runtime_repo(runtime_root: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = _repo_snapshot(runtime_root)
    if snapshot["status"] != "AVAILABLE":
        return {
            **snapshot,
            "contract": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "integration_docs": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "api": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "service": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "router": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
        }, {}

    contract, contract_status = _structured_evidence(runtime_root, ("PROJECT_CONTRACT.yaml", "PROJECT_CONTRACT.yml", "PROJECT_CONTRACT.json"))
    integration_docs = _text_evidence(runtime_root, ("docs/INTEGRATION_CONTRACTS.md",))
    api = _file_evidence(runtime_root, "src/new_earth_ai/api.py")
    service = _file_evidence(runtime_root, "src/new_earth_ai/service.py")
    router = _file_evidence(runtime_root, "src/new_earth_ai/router.py")
    declared_interfaces: list[str] = []
    declared_service_type = None
    if isinstance(contract, dict):
        declared_service_type = str(contract.get("service_subtype") or contract.get("service_type") or contract.get("type") or "").strip()
        for key in ("interfaces", "endpoints"):
            declared_interfaces.extend(str(item).strip() for item in _safe_list(contract.get(key)) if str(item).strip())
    api_matches = _scan_text_matches(
        api.get("text"),
        ("GET /health", "GET /v1/status", "GET /v1/models", "POST /v1/chat", "POST /v1/generate", "POST /v1/embeddings", "POST /v1/route/explain"),
    )
    service_matches = _scan_text_matches(service.get("text"), ("health(", "status(", "route_explain(", "chat(", "generate(", "embed("))
    router_matches = _scan_text_matches(router.get("text"), ("ModelRouter", "RoutingPolicy"))
    status = "AVAILABLE"
    if contract_status["status"] != "AVAILABLE" or api["status"] != "AVAILABLE" or service["status"] != "AVAILABLE" or router["status"] != "AVAILABLE":
        status = "MISSING"
    if declared_service_type and _normalize_text(declared_service_type) != "ai runtime":
        status = "SCHEMA_MISMATCH"
    return {
        **snapshot,
        "status": status,
        "contract": {
            "status": contract_status["status"],
            "path": contract_status["path"],
            "document": contract,
            "service_subtype": declared_service_type,
            "declared_interfaces": declared_interfaces,
        },
        "integration_docs": {
            "status": integration_docs["status"],
            "path": integration_docs["path"],
            "text": integration_docs["text"],
        },
        "api": {
            "status": api["status"],
            "path": api["path"],
            "matches": api_matches,
        },
        "service": {
            "status": service["status"],
            "path": service["path"],
            "matches": service_matches,
        },
        "router": {
            "status": router["status"],
            "path": router["path"],
            "matches": router_matches,
        },
    }, {
        "contract": contract,
        "integration_docs": integration_docs,
        "api": api,
        "service": service,
        "router": router,
    }


def _observe_gaia_repo(gaia_root: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = _repo_snapshot(gaia_root)
    if snapshot["status"] != "AVAILABLE":
        return {
            **snapshot,
            "runtime_client": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "agent": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "providers": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "api": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "docs": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "path": None},
            "production_scan": {"status": "UNAVAILABLE", "reason": snapshot["reason"], "required_files": {}, "missing_files": []},
            "direct_ollama_bypass": {"status": "UNAVAILABLE", "reason": snapshot["reason"]},
        }, {}

    required_files = {
        "src/gaia/local_ai_runtime.py": _file_evidence(gaia_root, "src/gaia/local_ai_runtime.py"),
        "src/gaia/agent.py": _file_evidence(gaia_root, "src/gaia/agent.py"),
        "src/gaia/providers.py": _file_evidence(gaia_root, "src/gaia/providers.py"),
        "src/gaia/api.py": _file_evidence(gaia_root, "src/gaia/api.py"),
    }
    runtime_client = required_files["src/gaia/local_ai_runtime.py"]
    agent = required_files["src/gaia/agent.py"]
    providers = required_files["src/gaia/providers.py"]
    api = required_files["src/gaia/api.py"]
    docs = _text_evidence(gaia_root, ("docs/OLLAMA_SETUP_WINDOWS.md",))
    runtime_client_matches = _scan_text_matches(
        runtime_client.get("text"),
        ("class LocalAIRuntimeClient", "async def health", "async def status", "async def models", "async def route_explain", "async def chat", "async def generate", "async def embeddings"),
    )
    agent_matches = _scan_text_matches(agent.get("text"), ("LocalAIRuntimeClient", "runtime_client.health(", "runtime_client.status(", "runtime_client.route_explain(", "runtime_client.chat(", "runtime_client.generate("))
    providers_matches = _scan_text_matches(providers.get("text"), ("LocalAIRuntimeClient", "RuntimeExecutionProvider"))
    api_matches = _scan_text_matches(api.get("text"), ("LocalAIRuntimeClient", "runtime_client.models(", "runtime_client.health("))
    docs_matches = _scan_text_matches(docs.get("text"), ("Do not add direct `ollama` execution calls to GAIA code.",))
    bypass_hits = _scan_for_patterns(gaia_root)
    production_missing = [path for path, evidence in required_files.items() if evidence["status"] != "AVAILABLE"]
    production_scan_status = "AVAILABLE" if not production_missing else "INCOMPLETE"
    return {
        **snapshot,
        "status": "AVAILABLE" if production_scan_status == "AVAILABLE" else "MISSING",
        "runtime_client": {
            "status": runtime_client["status"],
            "path": runtime_client["path"],
            "matches": runtime_client_matches,
        },
        "agent": {
            "status": agent["status"],
            "path": agent["path"],
            "matches": agent_matches,
        },
        "providers": {
            "status": providers["status"],
            "path": providers["path"],
            "matches": providers_matches,
        },
        "api": {
            "status": api["status"],
            "path": api["path"],
            "matches": api_matches,
        },
        "docs": {
            "status": docs["status"],
            "path": docs["path"],
            "matches": docs_matches,
        },
        "production_scan": {
            "status": production_scan_status,
            "reason": None if production_scan_status == "AVAILABLE" else "production_scan_incomplete",
            "required_files": {
                path: {"status": evidence["status"], "path": evidence["path"]}
                for path, evidence in required_files.items()
            },
            "missing_files": production_missing,
        },
        "direct_ollama_bypass": {
            "status": "PASS" if production_scan_status == "AVAILABLE" and not bypass_hits else "ERROR" if bypass_hits else "UNKNOWN",
            "reason": (
                None
                if production_scan_status == "AVAILABLE" and not bypass_hits
                else "production_scan_incomplete"
                if production_scan_status != "AVAILABLE"
                else "direct_ollama_bypass_detected"
                if bypass_hits
                else "unknown_bypass_state"
            ),
            "hits": bypass_hits,
        },
    }, {
        "runtime_client": runtime_client,
        "agent": agent,
        "providers": providers,
        "api": api,
        "docs": docs,
        "bypass_hits": bypass_hits,
        "production_scan_status": production_scan_status,
    }


def _observe_live_runtime(runtime_base_url: str | None, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
    if not runtime_base_url:
        return {
            "status": "UNAVAILABLE",
            "reason": "runtime_base_url_not_supplied",
            "base_url": None,
            "health": None,
            "runtime_status": None,
            "models": None,
            "route_explain": None,
        }
    base_url = runtime_base_url.rstrip("/")

    def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = _json_dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib_request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw.strip() else None
                return {"status": "AVAILABLE", "http_status": response.status, "path": path, "body": parsed}
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            try:
                parsed = json.loads(body) if body.strip() else None
            except json.JSONDecodeError:
                parsed = body or None
            return {"status": "ERROR", "http_status": exc.code, "path": path, "reason": type(exc).__name__, "body": parsed}
        except (urllib_error.URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
            return {"status": "ERROR", "http_status": None, "path": path, "reason": type(exc).__name__, "body": None}

    health = _request("GET", "/health")
    runtime_status = _request("GET", "/v1/status")
    models = _request("GET", "/v1/models")
    route_explain = _request(
        "POST",
        "/v1/route/explain",
        {
            "principal": "neos",
            "task": "observation",
            "correlation_id": "neos-local-ai-runtime-observation",
            "metadata": {"source": "neos"},
        },
    )
    status = "AVAILABLE"
    if any(item["status"] == "ERROR" for item in (health, runtime_status, models, route_explain)):
        status = "ERROR"
    return {
        "status": status,
        "reason": None if status == "AVAILABLE" else "runtime_endpoint_error",
        "base_url": base_url,
        "health": health,
        "runtime_status": runtime_status,
        "models": models,
        "route_explain": route_explain,
    }


def _observe_live_gaia_service(gaia_base_url: str | None, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
    if not gaia_base_url:
        return {
            "status": "UNAVAILABLE",
            "reason": "gaia_base_url_not_supplied",
            "base_url": None,
            "health": None,
            "model_status": None,
        }
    base_url = gaia_base_url.rstrip("/")

    def _request(path: str) -> dict[str, Any]:
        url = f"{base_url}{path}"
        req = urllib_request.Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw.strip() else None
                return {"status": "AVAILABLE", "http_status": response.status, "path": path, "body": parsed}
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            try:
                parsed = json.loads(body) if body.strip() else None
            except json.JSONDecodeError:
                parsed = body or None
            return {"status": "ERROR", "http_status": exc.code, "path": path, "reason": type(exc).__name__, "body": parsed}
        except (urllib_error.URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
            return {"status": "ERROR", "http_status": None, "path": path, "reason": type(exc).__name__, "body": None}

    health = _request("/health")
    model_status = _request("/models/status")
    status = "AVAILABLE" if health["status"] == "AVAILABLE" and model_status["status"] == "AVAILABLE" else "ERROR"
    return {
        "status": status,
        "reason": None if status == "AVAILABLE" else "gaia_service_unavailable_or_unhealthy",
        "base_url": base_url,
        "health": health,
        "model_status": model_status,
    }


def local_ai_runtime_report(
    *,
    platform_core_root: str | Path | None = None,
    gaia_root: str | Path | None = None,
    runtime_root: str | Path | None = None,
    runtime_base_url: str | None = None,
    gaia_base_url: str | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    platform_core_root_path = _resolve_root(platform_core_root, _DEFAULT_PLATFORM_CORE_ENV_VARS)
    gaia_root_path = _resolve_root(gaia_root, _DEFAULT_GAIA_ENV_VARS)
    runtime_root_path = _resolve_root(runtime_root, _DEFAULT_RUNTIME_ENV_VARS)

    platform_core, _platform_core_sources = _observe_platform_core(platform_core_root_path)
    runtime_repo, _runtime_sources = _observe_runtime_repo(runtime_root_path)
    gaia_repo, _gaia_sources = _observe_gaia_repo(gaia_root_path)
    live_runtime = _observe_live_runtime(runtime_base_url, timeout_seconds=timeout_seconds)
    gaia_service = _observe_live_gaia_service(gaia_base_url, timeout_seconds=timeout_seconds)

    findings: list[dict[str, Any]] = []

    platform_core_contract_ok = (
        platform_core["status"] == "AVAILABLE"
        and platform_core["governance"]["status"] == "AVAILABLE"
        and platform_core["integration_doc"]["status"] == "AVAILABLE"
        and platform_core["contract_example"]["status"] == "AVAILABLE"
        and all(platform_core["integration_doc"]["matches"].values())
    )
    findings.append(
        _finding(
            rule_id="LOCAL-AI-RUNTIME-001",
            status="PASS" if platform_core_contract_ok else "WARNING" if platform_core["status"] == "AVAILABLE" else "UNKNOWN",
            severity="INFO" if platform_core_contract_ok else "WARNING" if platform_core["status"] == "AVAILABLE" else "INFO",
            subject="platform_core",
            explanation="Platform Core declares the Local AI Runtime boundary, contract, and public interfaces.",
            evidence={
                "status": platform_core["status"],
                "governance_path": platform_core["governance"]["path"],
                "integration_path": platform_core["integration_doc"]["path"],
                "contract_path": platform_core["contract_example"]["path"],
                "declared_interfaces": platform_core.get("declared_interfaces", []),
            },
            affected={"repositories": ["New-Earth-Platform-Core"]},
            confidence=0.98 if platform_core_contract_ok else 0.72,
        )
    )

    runtime_contract_ok = (
        runtime_repo["status"] == "AVAILABLE"
        and runtime_repo["contract"]["status"] == "AVAILABLE"
        and runtime_repo["api"]["status"] == "AVAILABLE"
        and runtime_repo["service"]["status"] == "AVAILABLE"
        and runtime_repo["router"]["status"] == "AVAILABLE"
        and all(runtime_repo["api"]["matches"].values())
        and all(runtime_repo["service"]["matches"].values())
        and all(runtime_repo["router"]["matches"].values())
    )
    findings.append(
        _finding(
            rule_id="LOCAL-AI-RUNTIME-002",
            status="PASS" if runtime_contract_ok else "WARNING" if runtime_repo["status"] == "AVAILABLE" else "UNKNOWN",
            severity="INFO" if runtime_contract_ok else "WARNING" if runtime_repo["status"] == "AVAILABLE" else "INFO",
            subject="runtime_repo",
            explanation="Local AI Runtime repo exposes the declared read-only contract and implementation surfaces.",
            evidence={
                "status": runtime_repo["status"],
                "contract_path": runtime_repo["contract"]["path"],
                "api_path": runtime_repo["api"]["path"],
                "service_path": runtime_repo["service"]["path"],
                "router_path": runtime_repo["router"]["path"],
                "declared_interfaces": runtime_repo["contract"].get("declared_interfaces", []),
            },
            affected={"repositories": ["New-Earth-Local-AI-Runtime"]},
            confidence=0.98 if runtime_contract_ok else 0.74,
        )
    )

    gaia_runtime_boundary_ok = (
        gaia_repo["status"] == "AVAILABLE"
        and gaia_repo["runtime_client"]["status"] == "AVAILABLE"
        and gaia_repo["agent"]["status"] == "AVAILABLE"
        and gaia_repo["providers"]["status"] == "AVAILABLE"
        and gaia_repo["api"]["status"] == "AVAILABLE"
        and gaia_repo["docs"]["status"] == "AVAILABLE"
        and all(gaia_repo["runtime_client"]["matches"].values())
        and all(gaia_repo["agent"]["matches"].values())
        and all(gaia_repo["providers"]["matches"].values())
        and all(gaia_repo["api"]["matches"].values())
    )
    findings.append(
        _finding(
            rule_id="LOCAL-AI-RUNTIME-003",
            status="PASS" if gaia_runtime_boundary_ok else "WARNING" if gaia_repo["status"] == "AVAILABLE" else "UNKNOWN",
            severity="INFO" if gaia_runtime_boundary_ok else "WARNING" if gaia_repo["status"] == "AVAILABLE" else "INFO",
            subject="gaia_repo",
            explanation="GAIA production code routes runtime access through the Local AI Runtime client boundary.",
            evidence={
                "status": gaia_repo["status"],
                "runtime_client_path": gaia_repo["runtime_client"]["path"],
                "agent_path": gaia_repo["agent"]["path"],
                "providers_path": gaia_repo["providers"]["path"],
                "api_path": gaia_repo["api"]["path"],
                "doc_path": gaia_repo["docs"]["path"],
            },
            affected={"repositories": ["New-Earth-AI-Employee"]},
            confidence=0.97 if gaia_runtime_boundary_ok else 0.7,
        )
    )

    direct_bypass_status = gaia_repo["direct_ollama_bypass"]["status"]
    production_scan_trusted = gaia_repo["status"] == "AVAILABLE" and gaia_repo["production_scan"]["status"] == "AVAILABLE"
    if gaia_repo["status"] != "AVAILABLE":
        direct_bypass_report_status = "UNKNOWN"
        direct_bypass_severity = "INFO"
        direct_bypass_explanation = "GAIA repository evidence is unavailable, so the production bypass scan cannot conclude."
        direct_bypass_confidence = 0.55
    elif direct_bypass_status == "ERROR":
        direct_bypass_report_status = "ERROR"
        direct_bypass_severity = "ERROR"
        direct_bypass_explanation = "GAIA production source shows a direct Ollama execution bypass."
        direct_bypass_confidence = 0.99
    elif gaia_repo["production_scan"]["status"] != "AVAILABLE":
        direct_bypass_report_status = "WARNING"
        direct_bypass_severity = "WARNING"
        direct_bypass_explanation = "GAIA production sources are structurally incomplete, so the bypass scan is not trusted."
        direct_bypass_confidence = 0.68
    elif direct_bypass_status == "PASS" and production_scan_trusted:
        direct_bypass_report_status = "PASS"
        direct_bypass_severity = "INFO"
        direct_bypass_explanation = "GAIA production source shows no direct Ollama execution bypass."
        direct_bypass_confidence = 0.99
    else:
        direct_bypass_report_status = "UNKNOWN"
        direct_bypass_severity = "WARNING"
        direct_bypass_explanation = "GAIA bypass evidence is insufficient to conclude."
        direct_bypass_confidence = 0.6
    findings.append(
        _finding(
            rule_id="LOCAL-AI-RUNTIME-004",
            status=direct_bypass_report_status,
            severity=direct_bypass_severity,
            subject="gaia_repo",
            explanation=direct_bypass_explanation,
            evidence={
                "status": gaia_repo["direct_ollama_bypass"]["status"],
                "production_scan": gaia_repo["production_scan"],
                "trusted": production_scan_trusted,
                "hits": gaia_repo["direct_ollama_bypass"].get("hits", []),
            },
            affected={"repositories": ["New-Earth-AI-Employee"]},
            confidence=direct_bypass_confidence,
        )
    )

    live_runtime_ok = live_runtime["status"] == "AVAILABLE" and all(
        item["status"] == "AVAILABLE" and item["http_status"] == 200 for item in (live_runtime["health"], live_runtime["runtime_status"], live_runtime["models"], live_runtime["route_explain"])
    )
    findings.append(
        _finding(
            rule_id="LOCAL-AI-RUNTIME-005",
            status="PASS" if live_runtime_ok else "WARNING" if live_runtime["status"] == "AVAILABLE" else "UNKNOWN",
            severity="INFO" if live_runtime_ok else "WARNING" if live_runtime["status"] == "AVAILABLE" else "INFO",
            subject="runtime_service",
            explanation="A live Local AI Runtime endpoint responds to read-only health, status, model, and routing observations.",
            evidence=live_runtime,
            affected={"repositories": ["New-Earth-Local-AI-Runtime"]},
            confidence=0.96 if live_runtime_ok else 0.65,
        )
    )

    summary = _summary(
        findings,
        platform_core_status=platform_core["status"],
        runtime_repo_status=runtime_repo["status"],
        gaia_repo_status=gaia_repo["status"],
        runtime_service_status=live_runtime["status"],
        exclude_rule_ids={"LOCAL-AI-RUNTIME-005"},
    )
    source_fingerprint = _stable_hash(
        {
            "platform_core": platform_core,
            "runtime_repo": runtime_repo,
            "gaia_repo": gaia_repo,
            "gaia_service": gaia_service,
            "live_runtime": live_runtime,
            "findings": [item["id"] for item in findings],
            "summary": summary,
        }
    )
    snapshot_id = "lar-" + _stable_hash(
        {
            "schema_version": LOCAL_AI_RUNTIME_SCHEMA_VERSION,
            "source_fingerprint": source_fingerprint,
            "readiness": summary["readiness"],
            "status_counts": summary["status_counts"],
            "severity_counts": summary["severity_counts"],
        }
    )[:24]

    report = {
        "schema_version": LOCAL_AI_RUNTIME_SCHEMA_VERSION,
        "status": summary["readiness"],
        "summary": summary,
        "platform_core": platform_core,
        "runtime_repo": runtime_repo,
        "gaia_repo": gaia_repo,
        "gaia_service": gaia_service,
        "runtime_service": live_runtime,
        "findings": findings,
        "observed_at": utc_now(),
        "source_commit": _git_output(Path(__file__).resolve().parents[2], "rev-parse", "HEAD"),
        "snapshot": {
            "id": snapshot_id,
            "schema_version": LOCAL_AI_RUNTIME_SCHEMA_VERSION,
            "source_fingerprint": source_fingerprint,
            "observed_at": utc_now(),
            "status": summary["readiness"],
            "status_counts": summary["status_counts"],
            "severity_counts": summary["severity_counts"],
            "findings": [item["id"] for item in findings],
            "evidence_references": {
                "platform_core_root": platform_core.get("root"),
                "runtime_root": runtime_repo.get("root"),
                "gaia_root": gaia_repo.get("root"),
                "gaia_service_base_url": gaia_service.get("base_url"),
                "runtime_base_url": live_runtime.get("base_url"),
            },
        },
    }
    for item in report["findings"]:
        item["snapshot_id"] = snapshot_id
    return report


def local_ai_runtime_status(
    *,
    platform_core_root: str | Path | None = None,
    gaia_root: str | Path | None = None,
    runtime_root: str | Path | None = None,
    runtime_base_url: str | None = None,
    gaia_base_url: str | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    report = local_ai_runtime_report(
        platform_core_root=platform_core_root,
        gaia_root=gaia_root,
        runtime_root=runtime_root,
        runtime_base_url=runtime_base_url,
        gaia_base_url=gaia_base_url,
        timeout_seconds=timeout_seconds,
    )
    return {
        "schema_version": LOCAL_AI_RUNTIME_SCHEMA_VERSION,
        "status": report["status"],
        "summary": report["summary"],
        "platform_core": report["platform_core"],
        "runtime_repo": report["runtime_repo"],
        "gaia_repo": report["gaia_repo"],
        "gaia_service": report["gaia_service"],
        "runtime_service": report["runtime_service"],
        "snapshot": report["snapshot"],
    }


def local_ai_runtime_findings(
    *,
    platform_core_root: str | Path | None = None,
    gaia_root: str | Path | None = None,
    runtime_root: str | Path | None = None,
    runtime_base_url: str | None = None,
    gaia_base_url: str | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    report = local_ai_runtime_report(
        platform_core_root=platform_core_root,
        gaia_root=gaia_root,
        runtime_root=runtime_root,
        runtime_base_url=runtime_base_url,
        gaia_base_url=gaia_base_url,
        timeout_seconds=timeout_seconds,
    )
    return {
        "schema_version": LOCAL_AI_RUNTIME_SCHEMA_VERSION,
        "status": report["status"],
        "count": len(report["findings"]),
        "findings": report["findings"],
        "summary": report["summary"],
        "platform_core": report["platform_core"],
        "runtime_repo": report["runtime_repo"],
        "gaia_repo": report["gaia_repo"],
        "gaia_service": report["gaia_service"],
        "runtime_service": report["runtime_service"],
        "snapshot": report["snapshot"],
    }


def local_ai_runtime_snapshot(
    *,
    platform_core_root: str | Path | None = None,
    gaia_root: str | Path | None = None,
    runtime_root: str | Path | None = None,
    runtime_base_url: str | None = None,
    gaia_base_url: str | None = None,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    return local_ai_runtime_report(
        platform_core_root=platform_core_root,
        gaia_root=gaia_root,
        runtime_root=runtime_root,
        runtime_base_url=runtime_base_url,
        gaia_base_url=gaia_base_url,
        timeout_seconds=timeout_seconds,
    )["snapshot"]
