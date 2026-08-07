from pathlib import Path

from neos.classify import classify


def test_classification():
    assert classify(Path("docs/README.md")) == "documentation"
    assert classify(Path("tests/test_core.py")) == "test"
    assert classify(Path("src/main.cpp")) == "source_code"
    assert classify(Path("platformio.ini")) == "application_configuration"
    assert classify(Path(".github/workflows/ci.yml")) == "ci_workflow"
    assert classify(Path("releases/v1.0/notes.md")) == "release_documentation"
