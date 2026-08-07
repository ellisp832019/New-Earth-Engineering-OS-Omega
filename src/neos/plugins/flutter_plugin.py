from __future__ import annotations

from pathlib import Path

from .base import PluginDescriptor


class FlutterPlugin:
    descriptor = PluginDescriptor("flutter", "0.1.0", ("detect", "analyze"))

    def detect(self, repo: Path) -> bool:
        return (repo / "pubspec.yaml").exists() or (repo / "lib").exists()

    def analyze(self, repo: Path, context: dict) -> list[dict]:
        if not self.detect(repo):
            return []
        findings: list[dict] = []
        if (repo / "pubspec.yaml").exists():
            findings.append(
                {
                    "kind": "application_configuration",
                    "label": "Flutter project configuration",
                    "source_path": "pubspec.yaml",
                    "content_hash": "",
                    "metadata": {"plugin": "flutter", "detected_from": "pubspec.yaml"},
                }
            )
        if (repo / "lib").exists():
            findings.append(
                {
                    "kind": "source_code",
                    "label": "Flutter source tree",
                    "source_path": "lib",
                    "content_hash": "",
                    "metadata": {"plugin": "flutter", "detected_from": "lib"},
                }
            )
        return findings
