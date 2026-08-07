from pathlib import Path

from .base import PluginDescriptor


class PlatformIOPlugin:
    descriptor = PluginDescriptor("platformio", "0.1.0", ("detect", "analyze"))

    def detect(self, repo: Path) -> bool:
        return (repo / "platformio.ini").exists()

    def analyze(self, repo: Path, context: dict) -> list[dict]:
        if not self.detect(repo):
            return []
        return [
            {
                "kind": "build_definition",
                "label": "PlatformIO project",
                "source_path": "platformio.ini",
                "content_hash": "",
                "metadata": {"plugin": "platformio", "detected_from": "platformio.ini"},
            }
        ]
