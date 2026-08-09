from __future__ import annotations

from pathlib import Path
from typing import Any

from ..service.models import ServiceConfig
from .engine import AIEngine
from .models import AISettings
from .store import create_ai_conversation, list_ai_providers, load_ai_settings, save_ai_settings


def _engine(db_path: Path) -> AIEngine:
    return AIEngine(db_path)


def _handle_settings_get(db_path: Path) -> dict[str, Any]:
    settings = load_ai_settings(db_path)
    engine = _engine(db_path)
    return {
        "settings": settings.to_dict(),
        "provider": engine.provider_info(),
        "provider_health": engine.provider_health(),
    }


def _handle_settings_post(db_path: Path, body: dict[str, Any]) -> dict[str, Any]:
    current = load_ai_settings(db_path)
    payload = current.to_dict() | {
        key: body.get(key, current.to_dict().get(key))
        for key in ("provider_id", "model", "endpoint", "api_key_env", "timeout_seconds", "context_budget", "max_output_tokens", "streaming", "temperature", "enabled")
    }
    settings = AISettings.from_dict(payload)
    save_ai_settings(db_path, settings)
    return _handle_settings_get(db_path)


def handle_ai_get(path: str, query: dict[str, list[str]], db_path: Path, config: ServiceConfig) -> tuple[int, dict[str, Any]]:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if segments == ["ai", "providers"]:
        settings = load_ai_settings(db_path)
        return 200, {"providers": list_ai_providers(db_path), "settings": settings.to_dict()}
    if segments == ["ai", "providers", "health"]:
        engine = _engine(db_path)
        return 200, {"provider": engine.provider_info(), "health": engine.provider_health(), "settings": engine.settings_payload()}
    if segments == ["ai", "settings"]:
        return 200, _handle_settings_get(db_path)
    if segments == ["ai", "conversations"]:
        project_id = query.get("project_id", [None])[0]
        return 200, {"conversations": _engine(db_path).list_conversations(project_id=project_id), "project_id": project_id}
    if len(segments) == 3 and segments[0] == "ai" and segments[1] == "conversations":
        conversation = _engine(db_path).get_conversation(segments[2])
        if conversation is None:
            return 404, {"error": "not_found"}
        return 200, conversation
    if len(segments) == 3 and segments[0] == "ai" and segments[1] == "requests" and segments[2]:
        request = _engine(db_path).get_request(segments[2])
        if request is None:
            return 404, {"error": "not_found"}
        return 200, request
    if len(segments) == 4 and segments[0] == "ai" and segments[1] == "requests" and segments[3] == "citations":
        citations = _engine(db_path).list_citations(segments[2])
        return 200, {"request_id": segments[2], "citations": citations, "count": len(citations)}
    return 404, {"error": "not_found"}


def handle_ai_post(path: str, query: dict[str, list[str]], body: dict[str, Any], db_path: Path, config: ServiceConfig) -> tuple[int, dict[str, Any]]:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    engine = _engine(db_path)
    if segments == ["ai", "settings"]:
        return 200, _handle_settings_post(db_path, body)
    if segments == ["ai", "query"] or segments == ["ai", "stream"]:
        project_id = str(body.get("project_id") or query.get("project_id", [""])[0] or "").strip()
        raw_project_ids = body.get("project_ids")
        if raw_project_ids is None:
            raw_project_ids = query.get("project_ids", [])
        project_ids = [str(item).strip() for item in raw_project_ids if str(item).strip()] if isinstance(raw_project_ids, list) else []
        question = str(body.get("question") or "").strip()
        if not question:
            return 400, {"error": "missing_project_or_question"}
        if not project_id:
            project_id = "portfolio" if len(project_ids) > 1 else (project_ids[0] if project_ids else "")
        if not project_id:
            return 400, {"error": "missing_project_or_question"}
        conversation_id = body.get("conversation_id")
        if conversation_id is not None:
            conversation_id = str(conversation_id).strip() or None
        mode = body.get("mode")
        response = engine.query(
            project_id,
            question,
            project_ids=project_ids or None,
            conversation_id=conversation_id,
            mode=str(mode).strip() if isinstance(mode, str) and mode.strip() else None,
            title=str(body.get("title")).strip() if isinstance(body.get("title"), str) and str(body.get("title")).strip() else None,
        )
        return 200, response.to_dict()
    if segments == ["ai", "conversations"]:
        project_id = str(body.get("project_id") or "").strip()
        title = str(body.get("title") or "New AI Conversation").strip()
        if not project_id:
            return 400, {"error": "missing_project_id"}
        conversation = create_ai_conversation(db_path, project_id, title, provider_id=engine.provider.provider_id, model=engine.settings.model)
        return 200, {"conversation": conversation}
    if len(segments) == 4 and segments[0] == "ai" and segments[1] == "conversations" and segments[3] == "messages":
        conversation_id = segments[2]
        conversation_data = engine.get_conversation(conversation_id)
        if conversation_data is None:
            return 404, {"error": "not_found"}
        project_id = str(conversation_data.get("project_id") or body.get("project_id") or "").strip()
        question = str(body.get("question") or "").strip()
        if not project_id or not question:
            return 400, {"error": "missing_project_or_question"}
        response = engine.query(project_id, question, conversation_id=conversation_id, mode=str(body.get("mode")).strip() if isinstance(body.get("mode"), str) and str(body.get("mode")).strip() else None)
        return 200, response.to_dict()
    return 404, {"error": "not_found"}
