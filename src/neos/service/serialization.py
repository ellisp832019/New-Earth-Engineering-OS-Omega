from __future__ import annotations

import json
from typing import Any


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)


def json_bytes(payload: Any) -> bytes:
    return json_dumps(payload).encode("utf-8")


def json_loads(text: str | None, default: Any = None) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default

