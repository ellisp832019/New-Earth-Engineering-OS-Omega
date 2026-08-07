from __future__ import annotations

import ast
import configparser
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Finding

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
    from yaml import YAMLError  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None
    YAMLError = ValueError


INJECTION_MARKERS = (
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "assistant message",
    "prompt injection",
)


@dataclass(frozen=True)
class SemanticEntity:
    id: str
    project_id: str
    scan_id: str
    name: str
    kind: str
    status: str
    source_path: str
    start_line: int | None
    end_line: int | None
    content_hash: str
    parser_source: str
    created_at: str
    observed_at: str
    confidence: float
    provenance: str
    metadata: dict[str, Any]
    parent_id: str | None = None


@dataclass(frozen=True)
class Relationship:
    id: str
    project_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float
    evidence_source: str
    scan_id: str
    parser_source: str
    created_at: str
    metadata: dict[str, Any]


def utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _clean_doc_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def _is_secret_key(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("password", "token", "secret", "private_key", "api_key", "credential"))


def _entity(
    *,
    prefix: str,
    project_id: str,
    scan_id: str,
    name: str,
    kind: str,
    status: str = "observed",
    source_path: str,
    start_line: int | None,
    end_line: int | None,
    content_hash: str,
    parser_source: str,
    confidence: float,
    provenance: str,
    metadata: dict[str, Any] | None = None,
    parent_id: str | None = None,
    entity_id: str | None = None,
) -> SemanticEntity:
    entity_id = entity_id or stable_id(prefix, project_id, source_path, kind, name, start_line, end_line, parent_id)
    now = utc_now()
    return SemanticEntity(
        id=entity_id,
        project_id=project_id,
        scan_id=scan_id,
        name=name,
        kind=kind,
        status=status,
        source_path=source_path,
        start_line=start_line,
        end_line=end_line,
        content_hash=content_hash,
        parser_source=parser_source,
        created_at=now,
        observed_at=now,
        confidence=confidence,
        provenance=provenance,
        metadata=metadata or {},
        parent_id=parent_id,
    )


def _relationship(
    *,
    project_id: str,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    confidence: float,
    evidence_source: str,
    scan_id: str,
    parser_source: str,
    metadata: dict[str, Any] | None = None,
) -> Relationship:
    rid = stable_id(
        "rel",
        project_id,
        source_entity_id,
        target_entity_id,
        relationship_type,
        evidence_source,
        scan_id,
    )
    return Relationship(
        id=rid,
        project_id=project_id,
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        relationship_type=relationship_type,
        confidence=confidence,
        evidence_source=evidence_source,
        scan_id=scan_id,
        parser_source=parser_source,
        created_at=utc_now(),
        metadata=metadata or {},
    )


def _line_count(text: str) -> int:
    return text.count("\n") + 1


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _safe_json_loads(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _safe_yaml_loads(text: str) -> Any | None:
    if yaml is not None:  # pragma: no branch
        try:
            return yaml.safe_load(text)
        except YAMLError:
            return None
    # Minimal fallback for simple YAML mappings/lists.
    parsed: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(0, parsed)]
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            parent.setdefault("_items", []).append(content[2:].strip())
            continue
        if ":" in content:
            key, value = content.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                parent[key] = {}
                stack.append((indent + 2, parent[key]))
            else:
                parent[key] = value
    return parsed


def _walk_json_config(value: Any, path_parts: list[str], results: list[dict[str, Any]], source_path: str, scan_id: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _walk_json_config(child, path_parts + [str(key)], results, source_path, scan_id)
        return
    if isinstance(value, list):
        results.append(
            {
                "key": ".".join(path_parts),
                "section": ".".join(path_parts[:-1]) if len(path_parts) > 1 else None,
                "source_path": source_path,
                "value_type": "array",
                "default_value": None if _is_secret_key(path_parts[-1]) else json.dumps(value, sort_keys=True),
                "scan_id": scan_id,
            }
        )
        return
    key_name = path_parts[-1] if path_parts else ""
    secret = _is_secret_key(key_name)
    results.append(
        {
            "key": ".".join(path_parts),
            "section": ".".join(path_parts[:-1]) if len(path_parts) > 1 else None,
            "source_path": source_path,
            "value_type": type(value).__name__,
            "default_value": None if secret else value,
            "scan_id": scan_id,
        }
    )


def extract_configuration_keys(file_path: Path, scan_id: str) -> list[dict[str, Any]]:
    text = _clean_doc_text(_read_text(file_path))
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()
    parsed: Any | None = None
    if suffix == ".json":
        parsed = _safe_json_loads(text)
    elif suffix == ".toml" or name == "pyproject.toml":
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            parsed = None
    elif suffix == ".ini" or name == "platformio.ini":
        parser = configparser.ConfigParser()
        try:
            parser.read_string(text)
            parsed = {section: dict(parser[section]) for section in parser.sections()}
        except configparser.Error:
            parsed = None
    elif suffix in {".yaml", ".yml"} or name == "pubspec.yaml":
        parsed = _safe_yaml_loads(text)
    if parsed is None:
        return []

    results: list[dict[str, Any]] = []
    if isinstance(parsed, dict):
        _walk_json_config(parsed, [], results, file_path.as_posix(), scan_id)
    return results


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _decorator_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return None


def _decorator_route_and_method(decorator: ast.expr) -> tuple[str | None, str | None, float]:
    if not isinstance(decorator, ast.Call):
        return None, None, 0.0
    name = _decorator_name(decorator.func) or ""
    route: str | None = None
    method: str | None = None
    confidence = 0.0
    if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
        route = decorator.args[0].value
    for keyword in decorator.keywords:
        values: list[str] = []
        if keyword.arg == "path" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            route = keyword.value.value
        if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
            values = [elt.value for elt in keyword.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
        if values:
            method = values[0].upper()
        if keyword.arg == "method" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            method = keyword.value.value.upper()
    if name.endswith((".get", ".post", ".put", ".delete", ".patch", ".options")):
        method = name.rsplit(".", 1)[-1].upper()
        confidence = 0.98
    elif name.endswith((".route", ".api_route")):
        confidence = 0.85 if method else 0.65
    return route, method, confidence


def extract_python_symbols(
    file_path: Path,
    text: str,
    project_id: str,
    scan_id: str,
    content_hash: str,
) -> tuple[list[SemanticEntity], list[Relationship], list[dict[str, Any]], list[dict[str, Any]]]:
    symbols: list[SemanticEntity] = []
    relationships: list[Relationship] = []
    api_endpoints: list[dict[str, Any]] = []
    dependency_rows: list[dict[str, Any]] = []

    module_name = file_path.as_posix()
    module_id = stable_id("sym", project_id, module_name, "module")
    module_symbol = _entity(
        prefix="sym",
        project_id=project_id,
        scan_id=scan_id,
        name=module_name,
        kind="module",
        source_path=module_name,
        start_line=1,
        end_line=_line_count(text),
        content_hash=content_hash,
        parser_source="python-ast",
        confidence=1.0,
        provenance="python-ast",
        metadata={"language": "python"},
        entity_id=module_id,
    )
    symbols.append(module_symbol)

    try:
        tree = ast.parse(text, filename=file_path.as_posix())
    except SyntaxError as exc:
        symbols.append(
            _entity(
                prefix="sym",
                project_id=project_id,
                scan_id=scan_id,
                name=f"{file_path.name}:syntax_error",
                kind="parse_error",
                source_path=module_name,
                start_line=exc.lineno,
                end_line=exc.lineno,
                content_hash=content_hash,
                parser_source="python-ast",
                confidence=0.2,
                provenance="python-ast",
                metadata={"error": exc.msg},
                parent_id=module_id,
            )
        )
        return symbols, relationships, api_endpoints, dependency_rows

    def visit_body(body: list[ast.stmt], parent_id: str, parent_kind: str, class_name: str | None = None) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                kind = "test_class" if node.name.startswith("Test") else "class"
                symbol = _entity(
                    prefix="sym",
                    project_id=project_id,
                    scan_id=scan_id,
                    name=node.name,
                    kind=kind,
                    status="observed",
                    source_path=module_name,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    content_hash=content_hash,
                    parser_source="python-ast",
                    confidence=0.98,
                    provenance="python-ast",
                    metadata={"decorators": [_decorator_name(d) for d in node.decorator_list if _decorator_name(d)]},
                    parent_id=parent_id,
                )
                symbols.append(symbol)
                relationships.append(
                    _relationship(
                        project_id=project_id,
                        source_entity_id=parent_id,
                        target_entity_id=symbol.id,
                        relationship_type="defines",
                        confidence=0.98,
                        evidence_source=module_name,
                        scan_id=scan_id,
                        parser_source="python-ast",
                        metadata={"parent_kind": parent_kind},
                    )
                )
                for deco in node.decorator_list:
                    deco_name = _decorator_name(deco)
                    if deco_name:
                        deco_symbol = _entity(
                            prefix="sym",
                            project_id=project_id,
                            scan_id=scan_id,
                            name=deco_name,
                            kind="decorator",
                            source_path=module_name,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            content_hash=content_hash,
                            parser_source="python-ast",
                            confidence=0.8,
                            provenance="python-ast",
                            metadata={"applies_to": node.name},
                            parent_id=symbol.id,
                        )
                        symbols.append(deco_symbol)
                        relationships.append(
                            _relationship(
                                project_id=project_id,
                                source_entity_id=deco_symbol.id,
                                target_entity_id=symbol.id,
                                relationship_type="decorates",
                                confidence=0.8,
                                evidence_source=module_name,
                                scan_id=scan_id,
                                parser_source="python-ast",
                                metadata={},
                            )
                        )
                visit_body(node.body, symbol.id, kind, node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_test = node.name.startswith("test") or module_name.startswith("tests/") or "/tests/" in module_name
                kind = "test_function" if is_test else ("method" if parent_kind == "class" else ("async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"))
                symbol = _entity(
                    prefix="sym",
                    project_id=project_id,
                    scan_id=scan_id,
                    name=node.name,
                    kind=kind,
                    status="observed",
                    source_path=module_name,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    content_hash=content_hash,
                    parser_source="python-ast",
                    confidence=0.99,
                    provenance="python-ast",
                    metadata={"decorators": [_decorator_name(d) for d in node.decorator_list if _decorator_name(d)]},
                    parent_id=parent_id,
                )
                symbols.append(symbol)
                relationships.append(
                    _relationship(
                        project_id=project_id,
                        source_entity_id=parent_id,
                        target_entity_id=symbol.id,
                        relationship_type="defines",
                        confidence=0.99,
                        evidence_source=module_name,
                        scan_id=scan_id,
                        parser_source="python-ast",
                        metadata={"parent_kind": parent_kind},
                    )
                )

                for deco in node.decorator_list:
                    deco_name = _decorator_name(deco)
                    if deco_name:
                        deco_symbol = _entity(
                            prefix="sym",
                            project_id=project_id,
                            scan_id=scan_id,
                            name=deco_name,
                            kind="decorator",
                            source_path=module_name,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            content_hash=content_hash,
                            parser_source="python-ast",
                            confidence=0.8,
                            provenance="python-ast",
                            metadata={"applies_to": node.name},
                            parent_id=symbol.id,
                        )
                        symbols.append(deco_symbol)
                        relationships.append(
                            _relationship(
                                project_id=project_id,
                                source_entity_id=deco_symbol.id,
                                target_entity_id=symbol.id,
                                relationship_type="decorates",
                                confidence=0.8,
                                evidence_source=module_name,
                                scan_id=scan_id,
                                parser_source="python-ast",
                                metadata={},
                            )
                        )
                        route, method, route_conf = _decorator_route_and_method(deco)
                        if route:
                            endpoint_id = stable_id("api", project_id, module_name, node.name, route, method)
                            api_endpoints.append(
                                {
                                    "id": endpoint_id,
                                    "project_id": project_id,
                                    "scan_id": scan_id,
                                    "method": method,
                                    "route": route,
                                    "handler": node.name,
                                    "source_path": module_name,
                                    "line": node.lineno,
                                    "content_hash": content_hash,
                                    "confidence": route_conf,
                                    "provenance": "python-ast",
                                    "created_at": utc_now(),
                                    "observed_at": utc_now(),
                                    "metadata": {"decorator": deco_name},
                                }
                            )
                            relationships.append(
                                _relationship(
                                    project_id=project_id,
                                    source_entity_id=symbol.id,
                                    target_entity_id=endpoint_id,
                                    relationship_type="exposes",
                                    confidence=route_conf,
                                    evidence_source=module_name,
                                    scan_id=scan_id,
                                    parser_source="python-ast",
                                    metadata={"route": route, "method": method},
                                )
                            )

                visit_body(node.body, symbol.id, kind, node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    symbol = _entity(
                        prefix="sym",
                        project_id=project_id,
                        scan_id=scan_id,
                        name=name,
                        kind="import",
                        source_path=module_name,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        content_hash=content_hash,
                        parser_source="python-ast",
                        confidence=0.96,
                        provenance="python-ast",
                        metadata={"imported": alias.name, "alias": alias.asname},
                        parent_id=parent_id,
                    )
                    symbols.append(symbol)
                    target_id = stable_id("dep", project_id, alias.name)
                    dependency_rows.append(
                        {
                            "id": stable_id("dep", project_id, module_id, alias.name, node.lineno),
                            "project_id": project_id,
                            "scan_id": scan_id,
                            "source_entity_id": module_id,
                            "target_entity_id": target_id,
                            "dependency_type": "imports",
                            "confidence": 0.9,
                            "evidence_source": module_name,
                            "parser_source": "python-ast",
                            "created_at": utc_now(),
                            "metadata": {"imported": alias.name, "alias": alias.asname},
                        }
                    )
                    relationships.append(
                        _relationship(
                            project_id=project_id,
                            source_entity_id=module_id,
                            target_entity_id=target_id,
                            relationship_type="imports",
                            confidence=0.9,
                            evidence_source=module_name,
                            scan_id=scan_id,
                            parser_source="python-ast",
                            metadata={"imported": alias.name, "alias": alias.asname},
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imported = alias.asname or alias.name
                    symbol = _entity(
                        prefix="sym",
                        project_id=project_id,
                        scan_id=scan_id,
                        name=imported,
                        kind="imported_name",
                        source_path=module_name,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        content_hash=content_hash,
                        parser_source="python-ast",
                        confidence=0.96,
                        provenance="python-ast",
                        metadata={"imported_from": mod, "alias": alias.asname},
                        parent_id=parent_id,
                    )
                    symbols.append(symbol)
                    target_id = stable_id("dep", project_id, mod, alias.name)
                    dependency_rows.append(
                        {
                            "id": stable_id("dep", project_id, module_id, mod, alias.name, node.lineno),
                            "project_id": project_id,
                            "scan_id": scan_id,
                            "source_entity_id": module_id,
                            "target_entity_id": target_id,
                            "dependency_type": "imports",
                            "confidence": 0.9,
                            "evidence_source": module_name,
                            "parser_source": "python-ast",
                            "created_at": utc_now(),
                            "metadata": {"imported_from": mod, "alias": alias.asname},
                        }
                    )
                    relationships.append(
                        _relationship(
                            project_id=project_id,
                            source_entity_id=module_id,
                            target_entity_id=target_id,
                            relationship_type="imports",
                            confidence=0.9,
                            evidence_source=module_name,
                            scan_id=scan_id,
                            parser_source="python-ast",
                            metadata={"imported_from": mod, "alias": alias.asname},
                        )
                    )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        symbol = _entity(
                            prefix="sym",
                            project_id=project_id,
                            scan_id=scan_id,
                            name=target.id,
                            kind="constant",
                            source_path=module_name,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            content_hash=content_hash,
                            parser_source="python-ast",
                            confidence=0.92,
                            provenance="python-ast",
                            metadata={},
                            parent_id=parent_id,
                        )
                        symbols.append(symbol)
                        relationships.append(
                            _relationship(
                                project_id=project_id,
                                source_entity_id=parent_id,
                                target_entity_id=symbol.id,
                                relationship_type="defines",
                                confidence=0.92,
                                evidence_source=module_name,
                                scan_id=scan_id,
                                parser_source="python-ast",
                                metadata={"constant": target.id},
                            )
                        )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.isupper():
                symbol = _entity(
                    prefix="sym",
                    project_id=project_id,
                    scan_id=scan_id,
                    name=node.target.id,
                    kind="constant",
                    source_path=module_name,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    content_hash=content_hash,
                    parser_source="python-ast",
                    confidence=0.92,
                    provenance="python-ast",
                    metadata={},
                    parent_id=parent_id,
                )
                symbols.append(symbol)
                relationships.append(
                    _relationship(
                        project_id=project_id,
                        source_entity_id=parent_id,
                        target_entity_id=symbol.id,
                        relationship_type="defines",
                        confidence=0.92,
                        evidence_source=module_name,
                        scan_id=scan_id,
                        parser_source="python-ast",
                        metadata={"constant": node.target.id},
                    )
                )
            elif isinstance(node, ast.If):
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"
                    and node.test.comparators
                    and isinstance(node.test.comparators[0], ast.Constant)
                    and node.test.comparators[0].value == "__main__"
                ):
                    symbol = _entity(
                        prefix="sym",
                        project_id=project_id,
                        scan_id=scan_id,
                        name="__main__",
                        kind="cli_entry_point",
                        source_path=module_name,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        content_hash=content_hash,
                        parser_source="python-ast",
                        confidence=0.99,
                        provenance="python-ast",
                        metadata={"trigger": "__name__ == '__main__'"},
                        parent_id=module_id,
                    )
                    symbols.append(symbol)
                    relationships.append(
                        _relationship(
                            project_id=project_id,
                            source_entity_id=module_id,
                            target_entity_id=symbol.id,
                            relationship_type="exposes",
                            confidence=0.99,
                            evidence_source=module_name,
                            scan_id=scan_id,
                            parser_source="python-ast",
                            metadata={"trigger": "__name__ == '__main__'"},
                        )
                    )

    visit_body(tree.body, module_id, "module")
    return symbols, relationships, api_endpoints, dependency_rows


def extract_adr(file_path: Path, text: str, project_id: str, scan_id: str, content_hash: str) -> tuple[list[SemanticEntity], list[dict[str, Any]]]:
    if "adr" not in file_path.name.lower() and "/adr/" not in file_path.as_posix().lower():
        return [], []
    title = file_path.stem
    status = "accepted"
    date = None
    context = ""
    decision = ""
    rationale = ""
    alternatives = ""
    consequences = ""
    current_section: str | None = None
    sections: dict[str, list[str]] = {"context": [], "decision": [], "rationale": [], "alternatives": [], "consequences": []}

    for line in text.splitlines():
        header = re.match(r"^\s*(Status|Date|Title|Supersedes|Superseded-by)\s*:\s*(.+)\s*$", line, re.IGNORECASE)
        if header:
            key = header.group(1).lower()
            value = header.group(2).strip()
            if key == "status":
                status = value.lower()
            elif key == "date":
                date = value
            elif key == "title":
                title = value
            continue
        if line.startswith("## "):
            section_name = line[3:].strip().lower()
            current_section = section_name if section_name in sections else None
            continue
        if current_section:
            sections[current_section].append(line.strip())

    context = "\n".join(sections["context"]).strip()
    decision = "\n".join(sections["decision"]).strip()
    rationale = "\n".join(sections["rationale"]).strip()
    alternatives = "\n".join(sections["alternatives"]).strip()
    consequences = "\n".join(sections["consequences"]).strip()

    entity = _entity(
        prefix="dec",
        project_id=project_id,
        scan_id=scan_id,
        name=title,
        kind="decision",
        status=status,
        source_path=file_path.as_posix(),
        start_line=1,
        end_line=_line_count(text),
        content_hash=content_hash,
        parser_source="adr-markdown",
        confidence=0.92,
        provenance="adr-markdown",
        metadata={
            "date": date,
            "context": context,
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives,
            "consequences": consequences,
        },
    )
    return [entity], [
        {
            "id": stable_id("dec_ev", project_id, file_path.as_posix(), scan_id),
            "decision_id": entity.id,
            "project_id": project_id,
            "scan_id": scan_id,
            "evidence_type": "adr_markdown",
            "entity_id": entity.id,
            "source_path": file_path.as_posix(),
            "start_line": 1,
            "end_line": _line_count(text),
            "content_hash": content_hash,
            "confidence": 0.92,
            "provenance": "adr-markdown",
            "metadata": {
                "context": context,
                "decision": decision,
                "rationale": rationale,
                "alternatives": alternatives,
                "consequences": consequences,
                "date": date,
            },
        }
    ]


FEATURE_PATTERNS = [
    ("Firmware", ("firmware/", "firmware", "platformio.ini")),
    ("Flutter Application", ("flutter_app", "pubspec.yaml", "lib/")),
    ("Device Discovery", ("discovery", "pairing", "espnow", "scan")),
    ("Device Profiles", ("profile", "profiles")),
    ("Climate Sensing", ("sensor", "sensors", "humidity", "temperature", "co2", "light", "sht", "dht", "vl53", "ph")),
    ("Climate Control", ("relay", "pump", "irrigation", "valve", "fan", "automation")),
    ("Diagnostics", ("diagnostic", "logs", "health", "support_bundle")),
    ("API", ("api", "route", "endpoint", "server", "router")),
    ("Testing", ("test", "tests", "spec")),
    ("Releases", ("release", "releases", "changelog")),
    ("Project Control Centre", ("project_control", "control_centre", "control center")),
    ("Repository Intelligence", ("repo_context", "repository_intelligence", "scan", "knowledge graph")),
    ("Hardware Validation", ("hardware_validation", "bench", "calibration", "validation")),
]


def discover_feature_candidates(
    project_id: str,
    scan_id: str,
    findings: list[Finding],
    semantic_entities: list[SemanticEntity],
    decision_entities: list[SemanticEntity],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text_index: list[tuple[str, str]] = []
    for finding in findings:
        text_index.append((finding.source_path.lower(), finding.content_hash))
    paths = [finding.source_path for finding in findings]
    features: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    now = utc_now()

    for name, tokens in FEATURE_PATTERNS:
        matched_paths = [path for path in paths if any(token in path.lower() for token in tokens)]
        if not matched_paths:
            continue
        confidence = min(0.55 + 0.08 * len(matched_paths), 0.98)
        feature_id = stable_id("feat", project_id, name.lower())
        feature = {
            "id": feature_id,
            "project_id": project_id,
            "scan_id": scan_id,
            "name": name,
            "description": f"Deterministically inferred feature area from observed repository evidence for {name.lower()}.",
            "status": "candidate",
            "introduced_version": None,
            "removed_version": None,
            "confidence": confidence,
            "source": "heuristic",
            "created_at": now,
            "updated_at": now,
            "provenance": "path-heuristic",
            "metadata": {"evidence_paths": matched_paths[:20], "evidence_count": len(matched_paths)},
        }
        features.append(feature)
        for path in matched_paths[:20]:
            evidence_rows.append(
                {
                    "id": stable_id("feat_ev", project_id, feature_id, path),
                    "feature_id": feature_id,
                    "project_id": project_id,
                    "scan_id": scan_id,
                    "evidence_type": "path",
                    "entity_id": stable_id("raw", project_id, path),
                    "source_path": path,
                    "start_line": None,
                    "end_line": None,
                    "content_hash": next((finding.content_hash for finding in findings if finding.source_path == path), ""),
                    "confidence": confidence,
                    "provenance": "path-heuristic",
                    "metadata": {"feature_name": name},
                }
            )

    # Always keep candidate detection conservative when no patterns are found.
    if not features:
        features.append(
            {
                "id": stable_id("feat", project_id, "insufficient_evidence"),
                "project_id": project_id,
                "scan_id": scan_id,
                "name": "insufficient_evidence",
                "description": "The current evidence is insufficient to confidently infer a feature.",
                "status": "unknown",
                "introduced_version": None,
                "removed_version": None,
                "confidence": 0.1,
                "source": "heuristic",
                "created_at": now,
                "updated_at": now,
                "provenance": "path-heuristic",
                "metadata": {"evidence_paths": []},
            }
        )
    return features, evidence_rows


def extract_impact_findings(
    project_id: str,
    scan_id: str,
    feature_ids: list[str],
    relation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    now = utc_now()
    for feature_id in feature_ids:
        related = [row for row in relation_rows if row["source_entity_id"] == feature_id or row["target_entity_id"] == feature_id]
        if not related:
            continue
        findings.append(
            {
                "id": stable_id("impact", project_id, feature_id, scan_id),
                "project_id": project_id,
                "scan_id": scan_id,
                "entity_id": feature_id,
                "impact_type": "feature_dependency",
                "severity": "unknown",
                "confidence": min(0.9, 0.5 + 0.05 * len(related)),
                "path_json": json.dumps([row["relationship_type"] for row in related], sort_keys=True),
                "explanation": f"Feature is connected to {len(related)} evidence-backed graph relationships.",
                "provenance": "graph-traversal",
                "created_at": now,
                "metadata": {"related_count": len(related)},
            }
        )
    return findings


def contains_suspicious_instruction(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in INJECTION_MARKERS)


def extract_semantics(
    repo_root: Path,
    project_id: str,
    scan_id: str,
    findings: list[Finding],
) -> dict[str, list[dict[str, Any]]]:
    symbols: list[SemanticEntity] = []
    symbol_locations: list[dict[str, Any]] = []
    relationships: list[Relationship] = []
    dependencies: list[dict[str, Any]] = []
    api_endpoints: list[dict[str, Any]] = []
    configuration_keys: list[dict[str, Any]] = []
    decisions: list[SemanticEntity] = []
    decision_evidence: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    feature_evidence: list[dict[str, Any]] = []

    for finding in findings:
        path = repo_root / finding.source_path
        text = ""
        if path.exists() and path.suffix.lower() in {".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".md", ".txt"}:
            try:
                text = _clean_doc_text(_read_text(path))
            except OSError:
                text = ""
        if finding.source_path.endswith(".py"):
            py_symbols, py_relationships, py_api_endpoints, py_dependencies = extract_python_symbols(
                path.relative_to(repo_root),
                text,
                project_id,
                scan_id,
                finding.content_hash,
            )
            symbols.extend(py_symbols)
            relationships.extend(py_relationships)
            api_endpoints.extend(py_api_endpoints)
            dependencies.extend(py_dependencies)
            for symbol in py_symbols:
                symbol_locations.append(
                    {
                        "id": stable_id("loc", symbol.id),
                        "symbol_id": symbol.id,
                        "project_id": project_id,
                        "scan_id": scan_id,
                        "source_path": symbol.source_path,
                        "start_line": symbol.start_line,
                        "end_line": symbol.end_line,
                        "content_hash": symbol.content_hash,
                        "parser_source": symbol.parser_source,
                        "confidence": symbol.confidence,
                        "provenance": symbol.provenance,
                        "created_at": symbol.created_at,
                        "observed_at": symbol.observed_at,
                        "metadata_json": json.dumps(symbol.metadata, sort_keys=True),
                    }
                )

        if finding.source_path.lower().endswith((".json", ".yaml", ".yml", ".toml", ".ini", "pyproject.toml", "platformio.ini", "pubspec.yaml")):
            for row in extract_configuration_keys(path, scan_id):
                row.update(
                    {
                        "id": stable_id("cfg", project_id, row["source_path"], row["key"], scan_id),
                        "project_id": project_id,
                        "content_hash": finding.content_hash,
                        "confidence": 0.85,
                        "provenance": "deterministic-config-parser",
                        "created_at": utc_now(),
                        "observed_at": utc_now(),
                        "metadata_json": json.dumps({"parser": "config"}, sort_keys=True),
                    }
                )
                configuration_keys.append(row)

        if finding.source_path.lower().endswith(".md") and ("adr" in finding.source_path.lower() or "decision" in finding.source_path.lower()):
            adr_decisions, adr_evidence = extract_adr(path, text, project_id, scan_id, finding.content_hash)
            decisions.extend(adr_decisions)
            decision_evidence.extend(adr_evidence)

    # Wrap raw semantics into feature candidates.
    feature_rows, feature_evidence_rows = discover_feature_candidates(
        project_id, scan_id, findings, symbols, decisions
    )
    features.extend(feature_rows)
    feature_evidence.extend(feature_evidence_rows)

    return {
        "symbols": [symbol.__dict__ for symbol in symbols],
        "symbol_locations": symbol_locations,
        "relationships": [
            {
                "id": rel.id,
                "project_id": rel.project_id,
                "source_entity_id": rel.source_entity_id,
                "target_entity_id": rel.target_entity_id,
                "relationship_type": rel.relationship_type,
                "confidence": rel.confidence,
                "evidence_source": rel.evidence_source,
                "scan_id": rel.scan_id,
                "parser_source": rel.parser_source,
                "created_at": rel.created_at,
                "metadata_json": json.dumps(rel.metadata, sort_keys=True),
            }
            for rel in relationships
        ],
        "dependencies": dependencies,
        "api_endpoints": api_endpoints,
        "configuration_keys": configuration_keys,
        "engineering_decisions": [decision.__dict__ for decision in decisions],
        "decision_evidence": decision_evidence,
        "features": features,
        "feature_evidence": feature_evidence,
        "impact_findings": extract_impact_findings(project_id, scan_id, [feature["id"] for feature in features], [
            {
                "source_entity_id": rel.source_entity_id,
                "target_entity_id": rel.target_entity_id,
                "relationship_type": rel.relationship_type,
            }
            for rel in relationships
        ]),
        "injection_warnings": [
            {
                "source_path": finding.source_path,
                "warning": "instruction-like text observed in repository content",
            }
            for finding in findings
            if contains_suspicious_instruction((repo_root / finding.source_path).read_text(encoding="utf-8", errors="ignore") if (repo_root / finding.source_path).exists() else "")
        ],
    }


def _insert_rows(
    conn,
    table: str,
    rows: list[dict[str, Any]],
    rename_map: dict[str, str] | None = None,
) -> None:
    if not rows:
        return
    table_columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for row in rows:
        prepared = dict(row)
        if rename_map:
            for source, target in rename_map.items():
                if source in prepared and target in table_columns and target not in prepared:
                    value = prepared.pop(source)
                    prepared[target] = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
        filtered = {key: value for key, value in prepared.items() if key in table_columns}
        columns = sorted(filtered.keys())
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        sql = f"INSERT OR REPLACE INTO {table} ({column_list}) VALUES ({placeholders})"
        conn.execute(sql, tuple(filtered.get(column) for column in columns))


def persist_semantics(conn, package: dict[str, list[dict[str, Any]]]) -> None:
    _insert_rows(conn, "symbols", package.get("symbols", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "symbol_locations", package.get("symbol_locations", []))
    _insert_rows(conn, "relationships", package.get("relationships", []))
    _insert_rows(conn, "dependencies", package.get("dependencies", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "api_endpoints", package.get("api_endpoints", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "configuration_keys", package.get("configuration_keys", []))
    decision_rows = []
    for row in package.get("engineering_decisions", []):
        metadata = dict(row.get("metadata", {}))
        decision_rows.append(
            {
                **row,
                "title": row.get("name"),
                "context": metadata.get("context", ""),
                "decision": metadata.get("decision", ""),
                "rationale": metadata.get("rationale", ""),
                "alternatives": metadata.get("alternatives", ""),
                "consequences": metadata.get("consequences", ""),
                "date": metadata.get("date"),
                "metadata_json": json.dumps(metadata, sort_keys=True),
            }
        )
    _insert_rows(conn, "engineering_decisions", decision_rows, {"metadata": "metadata_json", "name": "title"})
    _insert_rows(conn, "decision_evidence", package.get("decision_evidence", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "features", package.get("features", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "feature_evidence", package.get("feature_evidence", []), {"metadata": "metadata_json"})
    _insert_rows(conn, "impact_findings", package.get("impact_findings", []), {"metadata": "metadata_json"})


def entity_counts(package: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {key: len(value) for key, value in package.items() if isinstance(value, list)}


def package_feature_candidates(package: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return package.get("features", [])


def package_symbols(package: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return package.get("symbols", [])


def package_relationships(package: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return package.get("relationships", [])
