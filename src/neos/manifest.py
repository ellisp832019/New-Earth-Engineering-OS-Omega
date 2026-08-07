from __future__ import annotations

import json
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
ALLOWED_LIFECYCLES = {"concept", "experimental", "active", "maintenance", "archived"}


class ManifestError(ValueError):
    pass


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "project-manifest.schema.json"


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def _expected_type(schema: dict[str, Any]) -> tuple[type[Any], ...] | None:
    schema_type = schema.get("type")
    if schema_type is None:
        return None
    if isinstance(schema_type, list):
        types: list[Any] = []
        for entry in schema_type:
            if entry == "string":
                types.append(str)
            elif entry == "object":
                types.append(dict)
            elif entry == "array":
                types.append(list)
            elif entry == "number":
                types.append((int, float))
            elif entry == "integer":
                types.append(int)
            elif entry == "boolean":
                types.append(bool)
            elif entry == "null":
                types.append(type(None))
        return tuple(types)
    if schema_type == "string":
        return (str,)
    if schema_type == "object":
        return (dict,)
    if schema_type == "array":
        return (list,)
    if schema_type == "number":
        return (int, float)
    if schema_type == "integer":
        return (int,)
    if schema_type == "boolean":
        return (bool,)
    if schema_type == "null":
        return (type(None),)
    return None


def _validate_schema(value: Any, schema: dict[str, Any], path: str) -> None:
    expected = _expected_type(schema)
    if expected is not None and not isinstance(value, expected):
        readable = schema.get("type")
        raise ManifestError(f"{path or 'manifest'} must be of type {readable}")

    if "enum" in schema and value not in schema["enum"]:
        raise ManifestError(
            f"{path or 'manifest'} must be one of {', '.join(map(str, schema['enum']))}"
        )

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            raise ManifestError(f"{path or 'manifest'} must not be empty")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise ManifestError(f"{path or 'manifest'} does not match the required pattern")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_properties = schema.get("additionalProperties", True)
        for key in required:
            if key not in value:
                raise ManifestError(f"Missing required field: {path + key if path else key}")
        for key, nested_value in value.items():
            if key not in properties:
                if additional_properties is False:
                    raise ManifestError(f"Unexpected field: {path + key if path else key}")
                continue
            _validate_schema(
                nested_value,
                properties[key],
                f"{path}{key}.",
            )

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{index}].")


def normalise_repo_path(repo_path: str, manifest_path: Path) -> str:
    path = Path(repo_path)
    if not path.is_absolute():
        path = (manifest_path.parent / path).resolve()
    else:
        path = path.resolve()
    return str(path)


def normalize_manifest(data: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    normalized = deepcopy(data)
    repository = normalized.get("repository", {})
    repository["path"] = normalise_repo_path(str(repository["path"]), manifest_path)
    normalized["repository"] = repository
    return normalized


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema()
    _validate_schema(data, schema, "")
    if data["schema_version"] != SCHEMA_VERSION:
        raise ManifestError(f"Unsupported schema_version: {data['schema_version']!r}")
    if data.get("lifecycle") and data["lifecycle"] not in ALLOWED_LIFECYCLES:
        raise ManifestError(f"Unsupported lifecycle: {data['lifecycle']!r}")
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Manifest is not valid JSON: {exc.msg}") from exc
    validate_manifest(data)
    return normalize_manifest(data, path)
