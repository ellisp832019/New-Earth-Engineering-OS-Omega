from pathlib import Path

from neos.plugins.runtime import PluginRegistry


def test_default_plugins_detect_expected_markers(tmp_path: Path):
    (tmp_path / "platformio.ini").write_text("[env]\n")
    (tmp_path / "pubspec.yaml").write_text("name: demo\n")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    (tmp_path / "tests").mkdir()

    registry = PluginRegistry()
    detected = registry.detect(tmp_path)
    assert detected == ["platformio", "flutter", "python"]

    analyses = registry.analyze(tmp_path)
    plugin_ids = {analysis.plugin_id for analysis in analyses}
    assert plugin_ids == {"platformio", "flutter", "python"}
    assert any(finding.metadata["provenance"] == "plugin" for analysis in analyses for finding in analysis.findings)
