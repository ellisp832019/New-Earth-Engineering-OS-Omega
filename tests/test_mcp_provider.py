from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

import neos.mcp.provider as provider_module
from neos.mcp.provider import (
    EXPECTED_BASELINE_ID,
    EXPECTED_BUNDLE_FORMAT,
    EXPECTED_BUNDLE_ID,
    McpProviderConfig,
    McpProviderError,
    McpProviderRequest,
    McpProviderRuntime,
    McpStdioTransport,
)


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _valid_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    contracts = [
        ("contracts/identities/gaia.yaml", {"client_id": "gaia-mcp-client", "client_name": "GAIA", "owner_system_id": "gaia"}),
        (
            "contracts/identities/neos.yaml",
            {
                "server_id": "neos-engineering-read-server",
                "server_name": "NEOS Engineering Read Server",
                "owner_system_id": "neos",
            },
        ),
        (
            "contracts/capabilities/read.yaml",
            {"id": "neos.engineering.read", "mode": "read_only", "read_only": True, "tool_ids": ["neos.health.read", "neos.project.summary.read"]},
        ),
        (
            "contracts/tools/health.yaml",
            {"id": "neos.health.read", "operation": "health.read", "read_only": True, "side_effects": False},
        ),
        (
            "contracts/tools/summary.yaml",
            {"id": "neos.project.summary.read", "operation": "project.read", "read_only": True, "side_effects": False},
        ),
        ("contracts/resources/health.yaml", {"id": "neos.health", "resource_type": "health", "read_only": True}),
        ("contracts/resources/summary.yaml", {"id": "neos.project.summary", "resource_type": "project", "read_only": True}),
        ("contracts/queries/health.yaml", {"id": "neos.health.query", "parameter_schema_ref": "schemas/empty.json", "read_only": True, "side_effects": False}),
        ("contracts/queries/summary.yaml", {"id": "neos.project.summary.query", "parameter_schema_ref": "schemas/empty.json", "read_only": True, "side_effects": False}),
        (
            "contracts/manifests/neos.yaml",
            {
                "id": "neos.engineering.read.manifest",
                "server_id": "neos-engineering-read-server",
                "tool_ids": ["neos.health.read", "neos.project.summary.read"],
                "resource_ids": ["neos.health", "neos.project.summary"],
                "query_ids": ["neos.health.query", "neos.project.summary.query"],
            },
        ),
    ]
    for relative, contract in contracts:
        _write_yaml(bundle / relative, contract)
    _write_yaml(bundle / "registry/mcp.yaml", {"clients": [{"client_id": "gaia-mcp-client"}]})
    manifest = {
        "bundle_id": EXPECTED_BUNDLE_ID,
        "bundle_format_version": EXPECTED_BUNDLE_FORMAT,
        "contract_baseline_id": EXPECTED_BASELINE_ID,
        "registry_path": "registry/mcp.yaml",
        "contract_paths": [relative for relative, _ in contracts],
        "read_only": True,
    }
    (bundle / "bundle-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return bundle


def _runtime(
    bundle: Path,
    enabled: bool = True,
    health_reader: Any = None,
    health_db_path: Path | None = None,
) -> McpProviderRuntime:
    return McpProviderRuntime(
        McpProviderConfig(bundle, enabled=enabled, health_db_path=health_db_path),
        health_reader=health_reader,
    )


def test_valid_bundle_initializes(tmp_path: Path) -> None:
    runtime = _runtime(_valid_bundle(tmp_path))
    runtime.initialize()
    assert runtime.bundle is not None
    assert runtime.bundle.known_operations() == {"neos.health.read", "neos.project.summary.read"}


def test_provider_is_disabled_by_default(tmp_path: Path) -> None:
    with pytest.raises(McpProviderError, match="MCP_DISABLED"):
        _runtime(_valid_bundle(tmp_path), enabled=False).initialize()


def test_explicit_enable_is_supported(tmp_path: Path) -> None:
    runtime = _runtime(_valid_bundle(tmp_path), enabled=True)
    runtime.initialize()
    assert runtime.bundle is not None


def test_missing_invalid_identity_and_manifest_inputs_fail(tmp_path: Path) -> None:
    with pytest.raises(McpProviderError, match="BUNDLE_NOT_FOUND"):
        _runtime(tmp_path / "missing").initialize()
    bundle = _valid_bundle(tmp_path)
    (bundle / "bundle-manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(McpProviderError, match="BUNDLE_INVALID"):
        _runtime(bundle).initialize()


@pytest.mark.parametrize("field,value,code", [
    ("bundle_id", "wrong", "BUNDLE_INVALID"),
    ("bundle_format_version", "2.0.0", "BUNDLE_INVALID"),
    ("contract_baseline_id", "latest", "BASELINE_MISMATCH"),
])
def test_bundle_pins_are_enforced(tmp_path: Path, field: str, value: str, code: str) -> None:
    bundle = _valid_bundle(tmp_path)
    manifest_path = bundle / "bundle-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(McpProviderError, match=code):
        _runtime(bundle).initialize()


@pytest.mark.parametrize("missing", ["identity", "manifest"])
def test_missing_neos_identity_or_manifest_fails(tmp_path: Path, missing: str) -> None:
    bundle = _valid_bundle(tmp_path)
    manifest = json.loads((bundle / "bundle-manifest.json").read_text(encoding="utf-8"))
    path = bundle / ("contracts/identities/neos.yaml" if missing == "identity" else "contracts/manifests/neos.yaml")
    path.unlink()
    manifest["contract_paths"].remove(path.relative_to(bundle).as_posix())
    (bundle / "bundle-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(McpProviderError, match="SERVER_IDENTITY_MISSING|SERVER_MANIFEST_INVALID"):
        _runtime(bundle).initialize()


def test_manifest_server_mismatch_and_write_contract_fail(tmp_path: Path) -> None:
    bundle = _valid_bundle(tmp_path)
    manifest_path = bundle / "contracts/manifests/neos.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["server_id"] = "other-server"
    _write_yaml(manifest_path, manifest)
    with pytest.raises(McpProviderError, match="SERVER_MANIFEST_INVALID"):
        _runtime(bundle).initialize()

    bundle = _valid_bundle(tmp_path / "write")
    tool_path = bundle / "contracts/tools/health.yaml"
    tool = yaml.safe_load(tool_path.read_text(encoding="utf-8"))
    tool["operation"] = "write.update"
    _write_yaml(tool_path, tool)
    with pytest.raises(McpProviderError, match="UNSAFE_CONTRACT"):
        _runtime(bundle).initialize()


def test_operations_are_allowlisted_and_not_implemented(tmp_path: Path) -> None:
    runtime = _runtime(_valid_bundle(tmp_path), health_reader=lambda: {"status": "healthy"})
    runtime.initialize()
    health = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {}))
    assert health.status == "success"
    summary = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.project.summary.read", {}))
    assert summary.status == "not_implemented"
    assert summary.error == {"code": "NOT_IMPLEMENTED", "message": "NEOS MCP read execution is deferred"}
    unknown = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.delete", {}))
    assert unknown.error == {"code": "UNKNOWN_OPERATION"}


@pytest.mark.parametrize(
    "health_status,response_status",
    [("healthy", "success"), ("degraded", "success"), ("unknown", "unknown"), ("unavailable", "unknown")],
)
def test_health_status_is_preserved(tmp_path: Path, health_status: str, response_status: str) -> None:
    result = {"status": health_status, "service_version": "1.3.0"}
    runtime = _runtime(_valid_bundle(tmp_path), health_reader=lambda: result)
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("health-corr", "gaia-mcp-client", "neos.health.read", {}))
    assert response.status == response_status
    assert response.result == result
    assert response.correlation_id == "health-corr"
    assert response.operation_id == "neos.health.read"


def test_health_read_uses_in_process_source_without_http(tmp_path: Path) -> None:
    calls: list[str] = []

    def read_health() -> dict[str, Any]:
        calls.append("health")
        return {"status": "healthy", "source": "service_health"}

    runtime = _runtime(_valid_bundle(tmp_path), health_reader=read_health)
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {}))
    assert response.status == "success"
    assert calls == ["health"]


def test_default_health_reader_uses_canonical_service_health(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observed: dict[str, Any] = {}

    def canonical_health(db_path: Path, config: Any) -> dict[str, Any]:
        observed["db_path"] = db_path
        observed["config_db_path"] = config.db_path
        return {"status": "healthy", "source": "canonical"}

    monkeypatch.setattr(provider_module, "service_health", canonical_health)
    db_path = tmp_path / "neos.db"
    runtime = _runtime(_valid_bundle(tmp_path), health_db_path=db_path)
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {}))
    assert response.result == {"status": "healthy", "source": "canonical"}
    assert observed == {"db_path": db_path, "config_db_path": db_path}


def test_health_failure_is_controlled_without_stack_trace(tmp_path: Path) -> None:
    def fail_health() -> dict[str, Any]:
        raise RuntimeError("secret stack detail")

    runtime = _runtime(_valid_bundle(tmp_path), health_reader=fail_health)
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {}))
    assert response.status == "error"
    assert response.error == {"code": "HEALTH_READ_FAILED", "message": "NEOS health read failed"}
    assert "secret stack detail" not in json.dumps(response.as_mapping())


def test_health_rejects_arguments_without_calling_reader(tmp_path: Path) -> None:
    calls: list[str] = []

    def read_health() -> dict[str, Any]:
        calls.append("called")
        return {"status": "healthy"}

    runtime = _runtime(_valid_bundle(tmp_path), health_reader=read_health)
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {"path": "x"}))
    assert response.status == "rejected"
    assert response.error and response.error["code"] == "INVALID_ARGUMENTS"
    assert calls == []


def test_health_requires_configured_source_when_no_reader_is_injected(tmp_path: Path) -> None:
    runtime = _runtime(_valid_bundle(tmp_path))
    runtime.initialize()
    response = runtime.handle(McpProviderRequest("corr", "gaia-mcp-client", "neos.health.read", {}))
    assert response.status == "unknown"
    assert response.error and response.error["code"] == "HEALTH_UNAVAILABLE"


def test_request_client_and_stdio_boundaries(tmp_path: Path) -> None:
    runtime = _runtime(_valid_bundle(tmp_path), health_reader=lambda: {"status": "healthy"})
    runtime.initialize()
    unknown = runtime.handle(McpProviderRequest("corr", "unknown", "neos.health.read", {}))
    assert unknown.error == {"code": "UNKNOWN_CLIENT"}
    with pytest.raises(McpProviderError, match="INVALID_REQUEST"):
        McpProviderRequest.from_mapping({"client_id": "gaia-mcp-client"})
    input_stream = io.StringIO('{"correlation_id":"c","client_id":"gaia-mcp-client","operation_id":"neos.health.read","arguments":{}}\n')
    request = McpStdioTransport.read_request(input_stream)
    assert request is not None
    output_stream = io.StringIO()
    McpStdioTransport.write_response(output_stream, runtime.handle(request))
    output = json.loads(output_stream.getvalue())
    assert output["status"] == "success"
    assert output["operation_id"] == "neos.health.read"
