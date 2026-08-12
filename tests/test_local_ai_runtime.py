from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from neos.local_ai_runtime import local_ai_runtime_report
from neos.service.app import create_service_server


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _platform_core_repo(root: Path, runtime_root: Path) -> Path:
    _write_text(
        root / "registry" / "governance.yaml",
        f"""
schema_version: 1
governance_version: "1.0"
platform_core_merge_commit: "abc123"
interfaces:
  - "GET /health"
  - "GET /v1/status"
  - "GET /v1/models"
  - "POST /v1/chat"
  - "POST /v1/generate"
  - "POST /v1/embeddings"
  - "POST /v1/route/explain"
services:
  - "new-earth-local-ai-runtime"
systems:
  - system_id: local-ai-runtime
    project_id: new-earth-local-ai-runtime
    name: New Earth Local AI Runtime
    role: AI_RUNTIME
    canonical_owner: Platform Core
    identity_kind: owned runtime service
    classification: platform_core_service
    lifecycle: active
    canonical_repository:
      path: "{runtime_root.as_posix()}"
      remote: https://github.com/ellisp832019/New-Earth-Local-AI-Runtime.git
      branch: main
    interfaces:
      - "GET /health"
      - "GET /v1/status"
      - "GET /v1/models"
      - "POST /v1/chat"
      - "POST /v1/generate"
      - "POST /v1/embeddings"
      - "POST /v1/route/explain"
    capabilities:
      - local_ai_runtime
""",
    )
    _write_text(
        root / "docs" / "integrations" / "LOCAL_AI_RUNTIME.md",
        """
# Local AI Runtime

Platform Core declares the Local AI Runtime as an owned runtime service.

- `GET /health`
- `GET /v1/status`
- `GET /v1/models`
- `POST /v1/chat`
- `POST /v1/generate`
- `POST /v1/embeddings`
- `POST /v1/route/explain`
- `POST /v1/context/provenance`
- `GET /v1/impact/advisory`
""",
    )
    _write_text(
        root / "examples" / "contracts" / "NEW_EARTH_LOCAL_AI_RUNTIME.NEW_EARTH_PROJECT.yaml",
        """
schema_version: 1
name: New Earth Local AI Runtime
project_id: new-earth-local-ai-runtime
service_subtype: AI_RUNTIME
interfaces:
  - GET /health
  - GET /v1/status
  - GET /v1/models
  - POST /v1/chat
  - POST /v1/generate
  - POST /v1/embeddings
  - POST /v1/route/explain
""",
    )
    return root


def _runtime_repo(root: Path) -> Path:
    _write_text(
        root / "PROJECT_CONTRACT.yaml",
        """
schema_version: 1
name: New Earth Local AI Runtime
project_id: new-earth-local-ai-runtime
service_subtype: AI_RUNTIME
interfaces:
  - GET /health
  - GET /v1/status
  - GET /v1/models
  - POST /v1/chat
  - POST /v1/generate
  - POST /v1/embeddings
  - POST /v1/route/explain
""",
    )
    _write_text(
        root / "docs" / "INTEGRATION_CONTRACTS.md",
        """
# Integration Contracts

Platform Core declares the runtime boundary.
GAIA consumes the runtime through a versioned client.
The Local AI Runtime owns routing and execution.
""",
    )
    _write_text(
        root / "src" / "new_earth_ai" / "api.py",
        """
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/status")
def status():
    return {"service": "new-earth-local-ai-runtime"}


@app.get("/v1/models")
def models():
    return {"models": []}


@app.post("/v1/chat")
def chat():
    return {"content": "ok"}


@app.post("/v1/generate")
def generate():
    return {"content": "ok"}


@app.post("/v1/embeddings")
def embeddings():
    return {"vectors": []}


@app.post("/v1/route/explain")
def route_explain():
    return {"decision": {"selected_model": "mock"}}
""",
    )
    _write_text(
        root / "src" / "new_earth_ai" / "service.py",
        """
class AIService:
    def health(self): ...
    def status(self): ...
    def route_explain(self): ...
    def chat(self): ...
    def generate(self): ...
    def embed(self): ...
""",
    )
    _write_text(
        root / "src" / "new_earth_ai" / "router.py",
        """
class ModelRouter:
    pass


class RoutingPolicy:
    pass
""",
    )
    return root


def _gaia_repo(root: Path, *, direct_bypass: bool = False) -> Path:
    _write_text(
        root / "src" / "gaia" / "local_ai_runtime.py",
        """
class LocalAIRuntimeClient:
    async def health(self): ...
    async def status(self): ...
    async def models(self): ...
    async def route_explain(self): ...
    async def chat(self): ...
    async def generate(self): ...
    async def embeddings(self): ...
""",
    )
    _write_text(
        root / "src" / "gaia" / "agent.py",
        """
from gaia.local_ai_runtime import LocalAIRuntimeClient


class AgentService:
    def __init__(self, runtime_client: LocalAIRuntimeClient) -> None:
        self.runtime_client = runtime_client

    async def ask(self):
        await self.runtime_client.health()
        await self.runtime_client.status()
        await self.runtime_client.route_explain()
        await self.runtime_client.chat()
        await self.runtime_client.generate()
""",
    )
    _write_text(
        root / "src" / "gaia" / "providers.py",
        """
from gaia.local_ai_runtime import LocalAIRuntimeClient


class RuntimeExecutionProvider:
    def __init__(self, client: LocalAIRuntimeClient) -> None:
        self.client = client
""",
    )
    _write_text(
        root / "src" / "gaia" / "api.py",
        """
from gaia.local_ai_runtime import LocalAIRuntimeClient


def create_app():
    runtime_client = LocalAIRuntimeClient(None)
    return runtime_client.models(), runtime_client.health()
""",
    )
    _write_text(
        root / "docs" / "OLLAMA_SETUP_WINDOWS.md",
        """
# OLLAMA Setup

Do not add direct `ollama` execution calls to GAIA code.
""",
    )
    if direct_bypass:
        _write_text(
            root / "src" / "gaia" / "legacy_ollama.py",
            """
import subprocess


def run_model():
    subprocess.run(["ollama", "run", "llama3"], check=True)
""",
        )
    return root


class _RuntimeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            payload = {"status": "ok", "service": "new-earth-local-ai-runtime", "version": "0.1.0", "local_only": True}
        elif self.path == "/v1/status":
            payload = {
                "service": "new-earth-local-ai-runtime",
                "version": "0.1.0",
                "local_only": True,
                "host": "127.0.0.1",
                "port": self.server.server_address[1],
                "api_base": f"http://127.0.0.1:{self.server.server_address[1]}/v1",
                "providers": {"mock": True},
            }
        elif self.path == "/v1/models":
            payload = {"service": "new-earth-local-ai-runtime", "version": "0.1.0", "models": []}
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:
        if self.path != "/v1/route/explain":
            self.send_response(404)
            self.end_headers()
            return
        payload = {
            "decision": {
                "schema_version": "v1",
                "requested_task": "observation",
                "requested_model": None,
                "selected_model": "mock",
                "selected_provider": "mock",
                "provider_model_name": "mock",
                "reason": "mock runtime",
                "fallback_used": False,
                "resource_constraints": {},
                "resource_snapshot": {"os_name": "Windows"},
            }
        }
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _start_runtime_server() -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RuntimeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class _GaiaServiceHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            payload = {"status": "ok", "version": "1.0.0"}
        elif self.path == "/models/status":
            payload = {"status": "ok", "selected_default_model": "mock"}
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _start_gaia_server() -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _GaiaServiceHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_local_ai_runtime_report_tracks_repo_and_live_service(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia")
    runtime_server, runtime_thread = _start_runtime_server()
    gaia_server, gaia_thread = _start_gaia_server()
    try:
        report = local_ai_runtime_report(
            platform_core_root=platform_core,
            runtime_root=runtime,
            gaia_root=gaia,
            runtime_base_url=f"http://127.0.0.1:{runtime_server.server_address[1]}",
            gaia_base_url=f"http://127.0.0.1:{gaia_server.server_address[1]}",
        )
        repeat = local_ai_runtime_report(
            platform_core_root=platform_core,
            runtime_root=runtime,
            gaia_root=gaia,
            runtime_base_url=f"http://127.0.0.1:{runtime_server.server_address[1]}",
            gaia_base_url=f"http://127.0.0.1:{gaia_server.server_address[1]}",
        )
    finally:
        runtime_server.shutdown()
        runtime_server.server_close()
        runtime_thread.join(timeout=5)
        gaia_server.shutdown()
        gaia_server.server_close()
        gaia_thread.join(timeout=5)

    assert report["status"] in {"READY", "READY_WITH_WARNINGS"}
    assert report["platform_core"]["status"] == "AVAILABLE"
    assert report["runtime_repo"]["status"] == "AVAILABLE"
    assert report["gaia_repo"]["status"] == "AVAILABLE"
    assert report["gaia_service"]["status"] == "AVAILABLE"
    assert report["runtime_service"]["status"] == "AVAILABLE"
    assert report["findings"][0]["rule_id"] == "LOCAL-AI-RUNTIME-001"
    assert {item["rule_id"]: item["status"] for item in report["findings"]}["LOCAL-AI-RUNTIME-001"] == "PASS"
    assert {item["rule_id"]: item["status"] for item in report["findings"]}["LOCAL-AI-RUNTIME-002"] == "PASS"
    assert {item["rule_id"]: item["status"] for item in report["findings"]}["LOCAL-AI-RUNTIME-003"] == "PASS"
    assert {item["rule_id"]: item["status"] for item in report["findings"]}["LOCAL-AI-RUNTIME-004"] == "PASS"
    assert {item["rule_id"]: item["status"] for item in report["findings"]}["LOCAL-AI-RUNTIME-005"] == "PASS"
    assert report["snapshot"]["id"].startswith("lar-")
    assert repeat["snapshot"]["id"] == report["snapshot"]["id"]


def test_local_ai_runtime_gaia_unavailable_does_not_pass_bypass(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    report = local_ai_runtime_report(
        platform_core_root=platform_core,
        runtime_root=runtime,
        gaia_root=tmp_path / "missing-gaia",
    )

    statuses = {item["rule_id"]: item["status"] for item in report["findings"]}
    assert statuses["LOCAL-AI-RUNTIME-004"] in {"UNKNOWN", "WARNING"}
    assert statuses["LOCAL-AI-RUNTIME-004"] != "PASS"
    assert report["gaia_repo"]["status"] == "UNAVAILABLE"
    assert report["gaia_service"]["status"] == "UNAVAILABLE"
    assert report["gaia_service"]["reason"] == "gaia_base_url_not_supplied"


def test_local_ai_runtime_gaia_available_without_bypass_passes(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia")
    report = local_ai_runtime_report(
        platform_core_root=platform_core,
        runtime_root=runtime,
        gaia_root=gaia,
    )

    assert report["status"] in {"READY", "READY_WITH_WARNINGS"}
    statuses = {item["rule_id"]: item["status"] for item in report["findings"]}
    assert statuses["LOCAL-AI-RUNTIME-004"] == "PASS"
    assert report["gaia_repo"]["status"] == "AVAILABLE"
    assert report["gaia_service"]["status"] == "UNAVAILABLE"
    assert report["runtime_service"]["status"] == "UNAVAILABLE"


def test_local_ai_runtime_missing_runtime_repo_does_not_pass(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia")
    report = local_ai_runtime_report(
        platform_core_root=platform_core,
        runtime_root=tmp_path / "missing-runtime",
        gaia_root=gaia,
    )

    statuses = {item["rule_id"]: item["status"] for item in report["findings"]}
    assert statuses["LOCAL-AI-RUNTIME-002"] in {"UNKNOWN", "WARNING"}
    assert statuses["LOCAL-AI-RUNTIME-002"] != "PASS"
    assert report["runtime_repo"]["status"] == "UNAVAILABLE"


def test_local_ai_runtime_gaia_available_with_direct_bypass_errors(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia", direct_bypass=True)

    report = local_ai_runtime_report(
        platform_core_root=platform_core,
        runtime_root=runtime,
        gaia_root=gaia,
    )

    statuses = {item["rule_id"]: item["status"] for item in report["findings"]}
    assert statuses["LOCAL-AI-RUNTIME-004"] == "ERROR"
    assert report["gaia_repo"]["status"] == "AVAILABLE"
    assert report["gaia_repo"]["direct_ollama_bypass"]["status"] == "ERROR"


def test_local_ai_runtime_snapshot_is_json_serializable(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia")

    report = local_ai_runtime_report(platform_core_root=platform_core, runtime_root=runtime, gaia_root=gaia)
    json.dumps(report, sort_keys=True)


def test_local_ai_runtime_cli_and_api_surfaces(tmp_path: Path) -> None:
    platform_core = _platform_core_repo(tmp_path / "platform-core", tmp_path / "runtime")
    runtime = _runtime_repo(tmp_path / "runtime")
    gaia = _gaia_repo(tmp_path / "gaia")
    db = tmp_path / "neos.db"
    sqlite3.connect(db).close()
    runtime_server, runtime_thread = _start_runtime_server()
    gaia_server, gaia_thread = _start_gaia_server()
    neos_server = create_service_server(db, host="127.0.0.1", port=0)
    neos_thread = threading.Thread(target=neos_server.serve_forever, daemon=True)
    neos_thread.start()
    try:
        runtime_base_url = f"http://127.0.0.1:{runtime_server.server_address[1]}"
        gaia_base_url = f"http://127.0.0.1:{gaia_server.server_address[1]}"
        cli = subprocess.run(
            [
                sys.executable,
                "-m",
                "neos",
                "--db",
                str(db),
                "governance",
                "local-ai-runtime",
                "--json",
                "--platform-core-root",
                str(platform_core),
                "--gaia-root",
                str(gaia),
                "--runtime-root",
                str(runtime),
                "--runtime-base-url",
                runtime_base_url,
                "--gaia-base-url",
                gaia_base_url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cli_report = json.loads(cli.stdout)
        assert cli_report["status"] in {"READY", "READY_WITH_WARNINGS"}
        assert cli_report["gaia_service"]["status"] == "AVAILABLE"

        api_query = urllib_parse.urlencode(
            {
                "platform_core_root": str(platform_core),
                "gaia_root": str(gaia),
                "runtime_root": str(runtime),
                "runtime_base_url": runtime_base_url,
                "gaia_base_url": gaia_base_url,
            }
        )
        api_url = f"http://127.0.0.1:{neos_server.server_address[1]}/governance/local-ai-runtime?{api_query}"
        with urllib_request.urlopen(api_url, timeout=30) as response:
            api_report = json.loads(response.read().decode("utf-8"))
        assert api_report["status"] in {"READY", "READY_WITH_WARNINGS"}
        assert api_report["gaia_service"]["status"] == "AVAILABLE"
    finally:
        runtime_server.shutdown()
        runtime_server.server_close()
        runtime_thread.join(timeout=5)
        gaia_server.shutdown()
        gaia_server.server_close()
        gaia_thread.join(timeout=5)
        neos_server.shutdown()
        neos_server.server_close()
        neos_thread.join(timeout=5)
