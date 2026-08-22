from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import yaml

from ..core import project_summary
from ..service.health import service_health
from ..service.models import ServiceConfig

EXPECTED_BASELINE_ID = "NE-MCP-READONLY-V1-DECLARATIVE-2026-08-21"
EXPECTED_BUNDLE_ID = "new-earth-mcp-contract-bundle-v1"
EXPECTED_BUNDLE_FORMAT = "1.0.0"
EXPECTED_SERVER_ID = "neos-engineering-read-server"
EXPECTED_MANIFEST_ID = "neos.engineering.read.manifest"
EXPECTED_CLIENT_ID = "gaia-mcp-client"
EXPECTED_CAPABILITY_ID = "neos.engineering.read"
EXPECTED_TOOL_IDS = frozenset({"neos.health.read", "neos.project.summary.read"})
EXPECTED_RESOURCE_IDS = frozenset({"neos.health", "neos.project.summary"})
EXPECTED_QUERY_IDS = frozenset({"neos.health.query", "neos.project.summary.query"})
WRITE_LIKE_TOKENS = frozenset(
    {"create", "update", "delete", "write", "mutate", "shell", "commit", "push", "merge", "actuate", "control"}
)
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PROJECT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]+$")


class McpProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class McpProviderConfig:
    bundle_path: Path
    enabled: bool = False
    health_db_path: Path | None = None

    @classmethod
    def from_environment(cls, bundle_path: Path) -> McpProviderConfig:
        enabled = os.environ.get("NEOS_MCP_PROVIDER_ENABLED", "false").strip().lower() == "true"
        return cls(bundle_path=bundle_path, enabled=enabled)


@dataclass(frozen=True)
class McpProviderRequest:
    correlation_id: str
    client_id: str
    operation_id: str
    arguments: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: Any) -> McpProviderRequest:
        if not isinstance(value, dict):
            raise McpProviderError("INVALID_REQUEST", "Request must be an object")
        fields = ("correlation_id", "client_id", "operation_id")
        if any(not isinstance(value.get(field), str) or not value[field].strip() for field in fields):
            raise McpProviderError("INVALID_REQUEST", "Request identity fields are required")
        arguments = value.get("arguments", {})
        if not isinstance(arguments, dict):
            raise McpProviderError("INVALID_REQUEST", "Request arguments must be an object")
        return cls(value["correlation_id"], value["client_id"], value["operation_id"], arguments)


@dataclass(frozen=True)
class McpProviderResponse:
    correlation_id: str
    status: str
    result: Any = None
    error: dict[str, str] | None = None
    operation_id: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "operation_id": self.operation_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise McpProviderError("BUNDLE_INVALID", f"Invalid JSON file: {path.name}") from exc
    if not isinstance(value, dict):
        raise McpProviderError("BUNDLE_INVALID", f"JSON file must contain an object: {path.name}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise McpProviderError("BUNDLE_INVALID", f"Invalid YAML file: {path.name}") from exc
    if not isinstance(value, dict):
        raise McpProviderError("BUNDLE_INVALID", f"Contract must contain an object: {path.name}")
    return value


def _safe_bundle_path(bundle: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise McpProviderError("BUNDLE_INVALID", f"Unsafe bundle path: {relative}")
    path = (bundle / relative).resolve()
    try:
        path.relative_to(bundle.resolve())
    except ValueError as exc:
        raise McpProviderError("BUNDLE_INVALID", f"Bundle path escapes root: {relative}") from exc
    return path


def _contains_write_like(value: Any) -> bool:
    if isinstance(value, str):
        tokens = {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}
        return bool(tokens & WRITE_LIKE_TOKENS)
    if isinstance(value, dict):
        return any(_contains_write_like(key) or _contains_write_like(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_write_like(item) for item in value)
    return False


@dataclass(frozen=True)
class McpContractBundle:
    root: Path
    manifest: dict[str, Any]
    registry: dict[str, Any]
    contracts: tuple[dict[str, Any], ...]

    @classmethod
    def load(cls, bundle_path: Path) -> McpContractBundle:
        bundle = bundle_path.expanduser().resolve()
        if not bundle.exists() or not bundle.is_dir():
            raise McpProviderError("BUNDLE_NOT_FOUND", str(bundle_path))
        manifest = _read_json(bundle / "bundle-manifest.json")
        if manifest.get("bundle_id") != EXPECTED_BUNDLE_ID:
            raise McpProviderError("BUNDLE_INVALID", "Unexpected bundle ID")
        if manifest.get("bundle_format_version") != EXPECTED_BUNDLE_FORMAT:
            raise McpProviderError("BUNDLE_INVALID", "Unsupported bundle format")
        if manifest.get("contract_baseline_id") != EXPECTED_BASELINE_ID:
            raise McpProviderError("BASELINE_MISMATCH", "Unexpected contract baseline")
        if manifest.get("read_only") is not True:
            raise McpProviderError("UNSAFE_CONTRACT", "Bundle is not read-only")
        if not isinstance(manifest.get("contract_paths"), list):
            raise McpProviderError("BUNDLE_INVALID", "Manifest contract_paths is missing")
        registry_path = _safe_bundle_path(bundle, manifest.get("registry_path"))
        if not registry_path.is_file():
            raise McpProviderError("BUNDLE_INVALID", "Registry is missing")
        registry = _read_yaml(registry_path)
        contracts: list[dict[str, Any]] = []
        for relative in manifest["contract_paths"]:
            path = _safe_bundle_path(bundle, relative)
            if not path.is_file():
                raise McpProviderError("BUNDLE_INVALID", f"Contract is missing: {relative}")
            contract = _read_yaml(path)
            if _contains_write_like(contract):
                raise McpProviderError("UNSAFE_CONTRACT", f"Write-like contract content: {relative}")
            contracts.append(contract)
        loaded = cls(bundle, manifest, registry, tuple(contracts))
        loaded._validate_identity_and_exposure()
        return loaded

    def _validate_identity_and_exposure(self) -> None:
        server_identity = next(
            (item for item in self.contracts if item.get("server_id") == EXPECTED_SERVER_ID and "server_name" in item),
            None,
        )
        if server_identity is None:
            raise McpProviderError("SERVER_IDENTITY_MISSING", EXPECTED_SERVER_ID)
        server_manifest = next((item for item in self.contracts if item.get("id") == EXPECTED_MANIFEST_ID), None)
        if server_manifest is None:
            raise McpProviderError("SERVER_MANIFEST_INVALID", EXPECTED_MANIFEST_ID)
        if server_manifest.get("server_id") != EXPECTED_SERVER_ID:
            raise McpProviderError("SERVER_MANIFEST_INVALID", "Manifest/server identity mismatch")
        if server_identity.get("owner_system_id") != "neos":
            raise McpProviderError("SERVER_IDENTITY_MISSING", "Unexpected NEOS owner")
        registry_clients = {
            str(item.get("client_id")): item
            for item in self.registry.get("clients", [])
            if isinstance(item, dict)
        }
        if EXPECTED_CLIENT_ID not in registry_clients:
            raise McpProviderError("BUNDLE_INVALID", "GAIA client is not registered")
        required = {
            "capability": {EXPECTED_CAPABILITY_ID},
            "tool": EXPECTED_TOOL_IDS,
            "resource": EXPECTED_RESOURCE_IDS,
            "query": EXPECTED_QUERY_IDS,
        }
        present: dict[str, set[str]] = {key: set() for key in required}
        for item in self.contracts:
            if "mode" in item and "tool_ids" in item:
                present["capability"].add(str(item.get("id", "")))
            if "operation" in item and str(item.get("id", "")).endswith(".read"):
                present["tool"].add(str(item.get("id", "")))
            if "resource_type" in item:
                present["resource"].add(str(item.get("id", "")))
            if "parameter_schema_ref" in item:
                present["query"].add(str(item.get("id", "")))
            if "read_only" in item and item.get("read_only") is not True:
                raise McpProviderError("UNSAFE_CONTRACT", "Exposed MCP target is not read-only")
            if "side_effects" in item and item.get("side_effects") is not False:
                raise McpProviderError("UNSAFE_CONTRACT", "Exposed MCP target is not read-only")
        for category, expected in required.items():
            if not set(expected).issubset(present[category]):
                raise McpProviderError("SERVER_MANIFEST_INVALID", f"Missing declared {category} targets")
        manifest_targets = {
            "tool": set(server_manifest.get("tool_ids", [])),
            "resource": set(server_manifest.get("resource_ids", [])),
            "query": set(server_manifest.get("query_ids", [])),
        }
        for category, expected in (("tool", EXPECTED_TOOL_IDS), ("resource", EXPECTED_RESOURCE_IDS), ("query", EXPECTED_QUERY_IDS)):
            if not expected.issubset(manifest_targets[category]):
                raise McpProviderError("SERVER_MANIFEST_INVALID", f"Manifest does not expose {category} targets")

    def known_operations(self) -> frozenset[str]:
        return frozenset(
            str(item["id"])
            for item in self.contracts
            if "operation" in item and str(item.get("id", "")).endswith(".read")
        )


class McpProviderRuntime:
    def __init__(
        self,
        config: McpProviderConfig,
        health_reader: Callable[[], dict[str, Any]] | None = None,
        project_summary_reader: Callable[[str], dict[str, Any]] | None = None,
    ):
        self.config = config
        self.bundle: McpContractBundle | None = None
        self.health_reader = health_reader or self._read_health
        self.project_summary_reader = project_summary_reader or self._read_project_summary

    def initialize(self) -> None:
        if not self.config.enabled:
            raise McpProviderError("MCP_DISABLED", "NEOS MCP provider is disabled")
        self.bundle = McpContractBundle.load(self.config.bundle_path)

    def _read_health(self) -> dict[str, Any]:
        if self.config.health_db_path is None:
            raise McpProviderError("HEALTH_UNAVAILABLE", "NEOS health database is not configured")
        return service_health(self.config.health_db_path, ServiceConfig(db_path=self.config.health_db_path))

    def _read_project_summary(self, project_id: str) -> dict[str, Any]:
        if self.config.health_db_path is None:
            raise McpProviderError("PROJECT_SUMMARY_UNAVAILABLE", "NEOS project database is not configured")
        return project_summary(self.config.health_db_path, project_id)

    def _health_response(self, request: McpProviderRequest) -> McpProviderResponse:
        if request.arguments:
            return McpProviderResponse(
                request.correlation_id,
                "rejected",
                error={"code": "INVALID_ARGUMENTS", "message": "neos.health.read accepts no arguments"},
                operation_id=request.operation_id,
            )
        try:
            result = self.health_reader()
        except McpProviderError as exc:
            return McpProviderResponse(
                request.correlation_id,
                "unknown" if exc.code == "HEALTH_UNAVAILABLE" else "error",
                error={"code": exc.code, "message": str(exc)},
                operation_id=request.operation_id,
            )
        except (KeyError, OSError, RuntimeError, TypeError, ValueError, sqlite3.Error):
            return McpProviderResponse(
                request.correlation_id,
                "error",
                error={"code": "HEALTH_READ_FAILED", "message": "NEOS health read failed"},
                operation_id=request.operation_id,
            )
        if not isinstance(result, dict) or not isinstance(result.get("status"), str):
            return McpProviderResponse(
                request.correlation_id,
                "error",
                error={"code": "INVALID_HEALTH_RESPONSE", "message": "NEOS health result is invalid"},
                operation_id=request.operation_id,
            )
        health_status = result["status"].lower()
        response_status = "unknown" if health_status in {"unknown", "unavailable"} else "error" if health_status == "error" else "success"
        return McpProviderResponse(
            request.correlation_id,
            response_status,
            result=result,
            operation_id=request.operation_id,
        )

    def _project_summary_response(self, request: McpProviderRequest) -> McpProviderResponse:
        if not isinstance(request.arguments, dict) or set(request.arguments) != {"project_id"}:
            return McpProviderResponse(
                request.correlation_id,
                "rejected",
                error={"code": "INVALID_PROJECT_ID", "message": "project_id is required"},
                operation_id=request.operation_id,
            )
        project_id = request.arguments["project_id"]
        if not isinstance(project_id, str) or PROJECT_ID_PATTERN.fullmatch(project_id) is None:
            return McpProviderResponse(
                request.correlation_id,
                "rejected",
                error={"code": "INVALID_PROJECT_ID", "message": "project_id is invalid"},
                operation_id=request.operation_id,
            )
        try:
            result = self.project_summary_reader(project_id)
        except McpProviderError as exc:
            return McpProviderResponse(
                request.correlation_id,
                "unknown" if exc.code == "PROJECT_SUMMARY_UNAVAILABLE" else "error",
                error={"code": exc.code, "message": str(exc)},
                operation_id=request.operation_id,
            )
        except ValueError as exc:
            code = "PROJECT_NOT_FOUND" if str(exc).startswith("Unknown project:") else "PROJECT_SUMMARY_FAILED"
            return McpProviderResponse(
                request.correlation_id,
                "error" if code == "PROJECT_SUMMARY_FAILED" else "unknown",
                error={"code": code, "message": "Project summary is not available" if code == "PROJECT_NOT_FOUND" else "Project summary read failed"},
                operation_id=request.operation_id,
            )
        except (KeyError, OSError, RuntimeError, TypeError, sqlite3.Error):
            return McpProviderResponse(
                request.correlation_id,
                "error",
                error={"code": "PROJECT_SUMMARY_FAILED", "message": "Project summary read failed"},
                operation_id=request.operation_id,
            )
        if not isinstance(result, dict):
            return McpProviderResponse(
                request.correlation_id,
                "error",
                error={"code": "INVALID_PROJECT_SUMMARY", "message": "Project summary result is invalid"},
                operation_id=request.operation_id,
            )
        summary_status = result.get("status")
        response_status = "unknown" if summary_status in {"unknown", "unavailable"} else "error" if summary_status == "error" else "success"
        return McpProviderResponse(
            request.correlation_id,
            response_status,
            result=result,
            operation_id=request.operation_id,
        )

    def handle(self, request: McpProviderRequest) -> McpProviderResponse:
        if self.bundle is None:
            raise McpProviderError("MCP_DISABLED", "Provider is not initialized")
        if request.client_id != EXPECTED_CLIENT_ID:
            return McpProviderResponse(request.correlation_id, "rejected", error={"code": "UNKNOWN_CLIENT"}, operation_id=request.operation_id)
        if request.operation_id not in self.bundle.known_operations():
            return McpProviderResponse(request.correlation_id, "rejected", error={"code": "UNKNOWN_OPERATION"}, operation_id=request.operation_id)
        if request.operation_id == "neos.health.read":
            return self._health_response(request)
        if request.operation_id == "neos.project.summary.read":
            return self._project_summary_response(request)
        return McpProviderResponse(
            request.correlation_id,
            "not_implemented",
            error={"code": "NOT_IMPLEMENTED", "message": "NEOS MCP read execution is deferred"},
            operation_id=request.operation_id,
        )


class McpStdioTransport:
    @staticmethod
    def read_request(stream: TextIO) -> McpProviderRequest | None:
        line = stream.readline()
        if not line:
            return None
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise McpProviderError("INVALID_REQUEST", "Input is not valid JSON") from exc
        return McpProviderRequest.from_mapping(value)

    @staticmethod
    def write_response(stream: TextIO, response: McpProviderResponse) -> None:
        stream.write(json.dumps(response.as_mapping(), sort_keys=True) + "\n")
        stream.flush()


def run_stdio(provider: McpProviderRuntime, stdin: TextIO, stdout: TextIO) -> None:
    provider.initialize()
    while True:
        request = McpStdioTransport.read_request(stdin)
        if request is None:
            return
        McpStdioTransport.write_response(stdout, provider.handle(request))
