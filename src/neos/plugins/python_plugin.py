from __future__ import annotations

from pathlib import Path

from .base import PluginDescriptor


class PythonPlugin:
    descriptor = PluginDescriptor("python", "0.1.0", ("detect", "analyze"))

    def detect(self, repo: Path) -> bool:
        return any((repo / candidate).exists() for candidate in ("pyproject.toml", "setup.py", "requirements.txt"))

    def analyze(self, repo: Path, context: dict) -> list[dict]:
        if not self.detect(repo):
            return []
        findings: list[dict] = []
        if (repo / "pyproject.toml").exists():
            findings.append(
                {
                    "kind": "application_configuration",
                    "label": "Python project configuration",
                    "source_path": "pyproject.toml",
                    "content_hash": "",
                    "metadata": {"plugin": "python", "detected_from": "pyproject.toml"},
                }
            )
        if (repo / "tests").exists():
            findings.append(
                {
                    "kind": "test",
                    "label": "Python test tree",
                    "source_path": "tests",
                    "content_hash": "",
                    "metadata": {"plugin": "python", "detected_from": "tests"},
                }
            )
        return findings
