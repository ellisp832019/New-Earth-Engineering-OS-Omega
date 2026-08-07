import json
from pathlib import Path

import pytest

from neos.manifest import ManifestError, load_manifest, validate_manifest


def test_manifest_validation_and_normalization(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest_path = tmp_path / "project.neos.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": "demo",
                "name": "Demo",
                "lifecycle": "active",
                "repository": {"path": "repo"},
                "technologies": ["Python"],
            }
        )
    )
    manifest = load_manifest(manifest_path)
    assert Path(manifest["repository"]["path"]) == repo.resolve()
    assert manifest["lifecycle"] == "active"


def test_manifest_rejects_bad_version():
    with pytest.raises(ManifestError, match="Unsupported schema_version"):
        validate_manifest(
            {
                "schema_version": "2.0",
                "project_id": "demo",
                "name": "Demo",
                "repository": {"path": "repo"},
            }
        )


def test_manifest_rejects_extra_fields():
    with pytest.raises(ManifestError, match="Unexpected field"):
        validate_manifest(
            {
                "schema_version": "1.0",
                "project_id": "demo",
                "name": "Demo",
                "repository": {"path": "repo", "extra": True},
            }
        )
