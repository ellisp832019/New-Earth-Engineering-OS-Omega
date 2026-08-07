from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str
    version: str
    capabilities: tuple[str, ...]

class AnalyzerPlugin(Protocol):
    descriptor: PluginDescriptor
    def detect(self, repo: Path) -> bool: ...
    def analyze(self, repo: Path, context: dict[str, Any]) -> list[dict[str, Any]]: ...
