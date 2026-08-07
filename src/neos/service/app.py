from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .models import ServiceConfig
from .routes import handle_get
from .serialization import json_bytes


def _local_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


class ServiceServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass, config: ServiceConfig):
        super().__init__(server_address, RequestHandlerClass)
        self.config = config


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

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def create_service_server(db_path: Path, *, host: str = "127.0.0.1", port: int = 8765) -> ServiceServer:
    if not _local_host(host):
        raise ValueError("NEOS service must bind to localhost only by default.")
    config = ServiceConfig(db_path=db_path, host=host, port=port)
    return ServiceServer((host, port), _handler_factory(), config)


def serve_service(db_path: Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = create_service_server(db_path, host=host, port=port)
    print(f"NEOS service listening on http://{host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def build_service_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neos service", description="Local NEOS service")
    sub = parser.add_subparsers(dest="service_cmd", required=True)
    start = sub.add_parser("start")
    start.add_argument("--db", required=True)
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", type=int, default=8765)
    start.add_argument("--json", action="store_true")
    return parser
