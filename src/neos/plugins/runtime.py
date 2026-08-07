from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import Finding
from .base import AnalyzerPlugin
from .example_platformio import PlatformIOPlugin
from .flutter_plugin import FlutterPlugin
from .python_plugin import PythonPlugin


@dataclass(frozen=True)
class PluginAnalysis:
    plugin_id: str
    findings: tuple[Finding, ...]


class PluginRegistry:
    def __init__(self, plugins: Iterable[AnalyzerPlugin] | None = None) -> None:
        self._plugins = tuple(plugins or default_plugins())

    @property
    def plugins(self) -> tuple[AnalyzerPlugin, ...]:
        return self._plugins

    def detect(self, repo: Path) -> list[str]:
        return [plugin.descriptor.plugin_id for plugin in self._plugins if plugin.detect(repo)]

    def analyze(self, repo: Path, context: dict[str, Any] | None = None) -> list[PluginAnalysis]:
        context = context or {}
        analyses: list[PluginAnalysis] = []
        for plugin in self._plugins:
            if not plugin.detect(repo):
                continue
            findings = []
            for item in plugin.analyze(repo, context):
                findings.append(
                    Finding(
                        kind=str(item["kind"]),
                        label=str(item["label"]),
                        source_path=str(item["source_path"]),
                        content_hash=str(item.get("content_hash", "")),
                        metadata={
                            **dict(item.get("metadata", {})),
                            "plugin": plugin.descriptor.plugin_id,
                            "plugin_version": plugin.descriptor.version,
                            "provenance": "plugin",
                        },
                    )
                )
            analyses.append(PluginAnalysis(plugin.descriptor.plugin_id, tuple(findings)))
        return analyses


def default_plugins() -> tuple[AnalyzerPlugin, ...]:
    return (PlatformIOPlugin(), FlutterPlugin(), PythonPlugin())
