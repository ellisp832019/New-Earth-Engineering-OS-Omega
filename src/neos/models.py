from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Finding:
    kind: str
    label: str
    source_path: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
