import json
import subprocess
from pathlib import Path

from neos.enrollment_observation import build_enrollment_observation

NOW = "2026-09-18T08:30:00Z"


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def create_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.name", "EA Test")
    run_git(repo, "config", "user.email", "ea-test@example.invalid")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "initial")
    return repo


def test_clean_repo_uses_real_neos_repo_profile(tmp_path):
    repo = create_repo(tmp_path)
    expected_head = run_git(repo, "rev-parse", "HEAD")
    expected_branch = run_git(repo, "branch", "--show-current")

    result = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )

    assert result["status"] == "PASS"
    assert result["head"] == expected_head
    assert result["branch"] == expected_branch
    assert result["dirty"] is False
    assert result["worktree_state"] == "CLEAN"
    assert result["provenance"]["producer"] == "NEOS"
    assert result["provenance"]["source_primitive"] == "neos.registry.repo_profile"
    assert result["evidence_refs"] == [result["provenance"]["evidence_id"]]


def test_dirty_repo_is_reported_distinctly(tmp_path):
    repo = create_repo(tmp_path)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")

    result = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )

    assert result["status"] == "PASS"
    assert result["dirty"] is True
    assert result["worktree_state"] == "DIRTY"


def test_non_git_directory_fails_closed_to_unknown(tmp_path):
    directory = tmp_path / "not-a-repo"
    directory.mkdir()

    result = build_enrollment_observation(
        str(directory),
        observed_at=NOW,
        max_age_seconds=3600,
    )

    assert result["status"] == "UNKNOWN"
    assert result["head"] is None
    assert result["dirty"] is None
    assert result["worktree_state"] == "UNAVAILABLE"
    assert result["provenance"]["producer"] == "NEOS"


def test_same_facts_and_timestamp_produce_stable_evidence_id(tmp_path):
    repo = create_repo(tmp_path)

    first = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )
    second = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )

    assert first["provenance"]["evidence_id"] == second["provenance"]["evidence_id"]


def test_timestamp_changes_evidence_identity(tmp_path):
    repo = create_repo(tmp_path)

    first = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )
    second = build_enrollment_observation(
        str(repo),
        observed_at="2026-09-18T08:31:00Z",
        max_age_seconds=3600,
    )

    assert first["provenance"]["evidence_id"] != second["provenance"]["evidence_id"]


def test_invalid_max_age_is_rejected(tmp_path):
    repo = create_repo(tmp_path)

    try:
        build_enrollment_observation(
            str(repo),
            observed_at=NOW,
            max_age_seconds=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid max_age_seconds to fail")


def test_naive_timestamp_is_rejected(tmp_path):
    repo = create_repo(tmp_path)

    try:
        build_enrollment_observation(
            str(repo),
            observed_at="2026-09-18T08:30:00",
            max_age_seconds=3600,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected naive timestamp to fail")


def test_observation_shape_is_json_serializable(tmp_path):
    repo = create_repo(tmp_path)
    result = build_enrollment_observation(
        str(repo),
        observed_at=NOW,
        max_age_seconds=3600,
    )
    json.dumps(result)
