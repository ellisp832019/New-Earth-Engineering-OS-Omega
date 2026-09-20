"""NEOS -> Enrollment observation adapter candidate.

This adapter intentionally reuses the canonical NEOS repository observation
primitive `neos.registry.repo_profile`. It does not implement Git observation itself.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from neos.registry import repo_profile


def _parse_time(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("observed_at must be offset-aware")
    return parsed


def _stable_evidence_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "neos-enrollment-observation:" + hashlib.sha256(encoded).hexdigest()[:24]


def build_enrollment_observation(
    repo_path: str,
    *,
    observed_at: str,
    max_age_seconds: int,
) -> dict[str, Any]:
    """Map canonical NEOS repo_profile facts into Enrollment observation evidence."""
    if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be a positive integer")

    _parse_time(observed_at)

    path = Path(repo_path)
    profile = repo_profile(path)

    head = profile.get("commit")
    branch = profile.get("branch")
    dirty = profile.get("dirty")
    fingerprint = profile.get("fingerprint")

    observable = (
        isinstance(head, str)
        and bool(head.strip())
        and isinstance(dirty, bool)
    )

    status = "PASS" if observable else "UNKNOWN"
    worktree_state = (
        "DIRTY"
        if dirty is True
        else "CLEAN"
        if dirty is False
        else "UNAVAILABLE"
    )

    provenance_core = {
        "producer": "NEOS",
        "repo_path": profile.get("repo_path"),
        "project_id": profile.get("project_id"),
        "fingerprint": fingerprint,
        "branch": branch,
        "head": head,
        "worktree_state": worktree_state,
        "observed_at": observed_at,
    }
    evidence_id = _stable_evidence_id(provenance_core)

    return {
        "applicability": "REQUIRED",
        "status": status,
        "observed_at": observed_at,
        "max_age_seconds": max_age_seconds,
        "provenance": {
            "producer": "NEOS",
            "evidence_id": evidence_id,
            "source_primitive": "neos.registry.repo_profile",
            "repo_path": profile.get("repo_path"),
            "project_id": profile.get("project_id"),
            "fingerprint": fingerprint,
        },
        "branch": branch,
        "head": head,
        "dirty": dirty,
        "worktree_state": worktree_state,
        "remote_url": profile.get("remote_url"),
        "manifest_path": profile.get("manifest_path"),
        "evidence_refs": [evidence_id],
    }
