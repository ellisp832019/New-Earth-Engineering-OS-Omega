from __future__ import annotations

import argparse
import ctypes
import json
import threading
import uuid
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .. import __version__
from ..db import ensure_database
from .models import ServiceConfig
from .routes import handle_get, handle_post
from .serialization import json_bytes


def _local_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


class ServiceServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass, config: ServiceConfig):
        super().__init__(server_address, RequestHandlerClass)
        self.config = config


_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_SYNCHRONIZE = 0x00100000
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102

_kernel32 = ctypes.windll.kernel32
_kernel32.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
_kernel32.OpenProcess.restype = ctypes.c_void_p
_kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_kernel32.WaitForSingleObject.restype = ctypes.c_uint
_kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
_kernel32.CloseHandle.restype = ctypes.c_int


def _process_is_alive(pid: int) -> bool:
    handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION | _SYNCHRONIZE, 0, pid)
    if not handle:
        return False
    try:
        result = _kernel32.WaitForSingleObject(handle, 0)
        return result == _WAIT_TIMEOUT
    finally:
        _kernel32.CloseHandle(handle)


def _start_owner_watchdog(server: ServiceServer) -> threading.Event | None:
    owner_pid = server.config.owner_pid
    if owner_pid is None:
        return None

    stop_event = threading.Event()

    def _watch_owner() -> None:
        while not stop_event.wait(1.0):
            if not _process_is_alive(owner_pid):
                server.shutdown()
                return

    threading.Thread(target=_watch_owner, name="neos-owner-watchdog", daemon=True).start()
    return stop_event


def _handler_factory() -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server: ServiceServer

        def _write(self, status: int, payload: Any) -> None:
            body = json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            config = self.server.config
            db_path = config.db_path
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/"):
                self._write(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            status, payload = handle_get(parsed.path, parse_qs(parsed.query), db_path, config)
            self._write(status, payload)

        def do_POST(self) -> None:
            config = self.server.config
            db_path = config.db_path
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/"):
                self._write(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except json.JSONDecodeError:
                self._write(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
                return
            status, payload = handle_post(parsed.path, parse_qs(parsed.query), body, db_path, config, self.server)
            self._write(status, payload)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def create_service_server(
    db_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    instance_id: str | None = None,
    owner_pid: int | None = None,
    shutdown_token: str | None = None,
    started_at: str | None = None,
) -> ServiceServer:
    if not _local_host(host):
        raise ValueError("NEOS service must bind to localhost only by default.")
    ensure_database(db_path)
    config = ServiceConfig(
        db_path=db_path,
        host=host,
        port=port,
        service_version=__version__,
        instance_id=instance_id or uuid.uuid4().hex,
        owner_pid=owner_pid,
        shutdown_token=shutdown_token or uuid.uuid4().hex,
        started_at=started_at or datetime.now(UTC).isoformat(),
    )
    return ServiceServer((host, port), _handler_factory(), config)


def serve_service(
    db_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    instance_id: str | None = None,
    owner_pid: int | None = None,
    shutdown_token: str | None = None,
) -> None:
    server = create_service_server(
        db_path,
        host=host,
        port=port,
        instance_id=instance_id,
        owner_pid=owner_pid,
        shutdown_token=shutdown_token,
    )
    print(f"NEOS service listening on http://{host}:{server.server_port}", flush=True)
    watchdog_stop = _start_owner_watchdog(server)
    try:
        server.serve_forever()
    finally:
        if watchdog_stop is not None:
            watchdog_stop.set()
        server.server_close()


def build_service_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neos service", description="Local NEOS service")
    sub = parser.add_subparsers(dest="service_cmd", required=True)
    start = sub.add_parser("start")
    start.add_argument("--db", required=True)
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", type=int, default=8765)
    start.add_argument("--instance-id")
    start.add_argument("--owner-pid", type=int)
    start.add_argument("--shutdown-token")
    start.add_argument("--json", action="store_true")
    return parser
