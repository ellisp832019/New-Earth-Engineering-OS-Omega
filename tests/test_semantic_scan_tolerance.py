from pathlib import Path

from neos.semantic import _safe_repository_text


def test_safe_repository_text_returns_empty_for_directory(tmp_path: Path) -> None:
    directory = tmp_path / "tests"
    directory.mkdir()

    assert _safe_repository_text(directory) == ""


def test_safe_repository_text_reads_normal_file(tmp_path: Path) -> None:
    file_path = tmp_path / "example.txt"
    file_path.write_text("hello world", encoding="utf-8")

    assert _safe_repository_text(file_path) == "hello world"


def test_safe_repository_text_returns_empty_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"

    assert _safe_repository_text(missing) == ""