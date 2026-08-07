from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .classify import classify
from .models import Finding

IGNORE_DIRS = {
    ".git",
    ".neos",
    ".venv",
    "node_modules",
    "build",
    "dist",
    ".dart_tool",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    "coverage",
    "out",
    "target",
    ".gradle",
}
SECRET_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json", "token.json", "secret.json"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer"}
MAX_HASH_BYTES = 50 * 1024 * 1024

def is_secret_like(path: Path) -> bool:
    n = path.name.lower()
    return (
        n in SECRET_NAMES
        or path.suffix.lower() in SECRET_SUFFIXES
        or n.startswith(".env.")
        or "secret" in n
        or "credential" in n
    )

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def scan_repo(repo: Path) -> list[Finding]:
    repo = repo.resolve()
    if not repo.is_dir():
        raise FileNotFoundError(f"Repository does not exist: {repo}")
    findings: list[Finding] = []
    for base, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        base_path = Path(base)
        for filename in sorted(files):
            full = (base_path / filename).resolve()
            try:
                full.relative_to(repo)
            except ValueError:
                continue
            rel = full.relative_to(repo)
            if is_secret_like(rel):
                continue
            try:
                size = full.stat().st_size
            except OSError:
                continue
            digest = hash_file(full) if size <= MAX_HASH_BYTES else f"skipped-size:{size}"
            findings.append(
                Finding(
                    classify(rel),
                    rel.name,
                    rel.as_posix(),
                    digest,
                    {"size": size, "suffix": rel.suffix.lower(), "origin": "scanner"},
                )
            )
    return findings
