from pathlib import Path

from neos.scanner import scan_repo


def test_scanner_excludes_secret_like(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('ok')")
    (tmp_path / ".env").write_text("SECRET=bad")
    rows=scan_repo(tmp_path)
    names={r.source_path for r in rows}
    assert "main.py" in names
    assert ".env" not in names
