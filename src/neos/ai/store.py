from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..db import connect
from .models import AIConversationTurn, AIRequest, AISettings

GLOBAL_SETTINGS_ID = "global"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _resolve_storage_project_id(db_path: Path, request: AIRequest) -> str:
    conn = connect(db_path)
    candidate_ids = [request.project_id, *request.project_ids]
    for candidate in candidate_ids:
        if not candidate:
            continue
        row = conn.execute("SELECT 1 FROM projects WHERE project_id=?", (candidate,)).fetchone()
        if row is not None:
            conn.close()
            return candidate
    conn.close()
    return request.project_id


def default_ai_settings() -> AISettings:
    return AISettings()


def load_ai_settings(db_path: Path) -> AISettings:
    conn = connect(db_path)
    row = conn.execute("SELECT * FROM ai_settings WHERE settings_id=?", (GLOBAL_SETTINGS_ID,)).fetchone()
    if row is None:
        conn.close()
        return default_ai_settings()
    settings = AISettings.from_dict(
        {
            "provider_id": row["provider_id"],
            "model": row["model"],
            "endpoint": row["endpoint"],
            "api_key_env": row["api_key_env"],
            "timeout_seconds": row["timeout_seconds"],
            "context_budget": row["context_budget"],
            "max_output_tokens": row["max_output_tokens"],
            "streaming": bool(row["streaming"]),
            "temperature": row["temperature"],
            "enabled": bool(row["enabled"]),
        }
    )
    conn.close()
    return settings


def save_ai_settings(db_path: Path, settings: AISettings) -> AISettings:
    conn = connect(db_path)
    now = _now()
    conn.execute(
        """
        INSERT INTO ai_settings(
            settings_id, provider_id, model, endpoint, api_key_env, timeout_seconds,
            context_budget, max_output_tokens, streaming, temperature, enabled,
            created_at, updated_at, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(settings_id) DO UPDATE SET
            provider_id=excluded.provider_id,
            model=excluded.model,
            endpoint=excluded.endpoint,
            api_key_env=excluded.api_key_env,
            timeout_seconds=excluded.timeout_seconds,
            context_budget=excluded.context_budget,
            max_output_tokens=excluded.max_output_tokens,
            streaming=excluded.streaming,
            temperature=excluded.temperature,
            enabled=excluded.enabled,
            updated_at=excluded.updated_at,
            metadata_json=excluded.metadata_json
        """,
        (
            GLOBAL_SETTINGS_ID,
            settings.provider_id,
            settings.model,
            settings.endpoint,
            settings.api_key_env,
            settings.timeout_seconds,
            settings.context_budget,
            settings.max_output_tokens,
            int(settings.streaming),
            settings.temperature,
            int(settings.enabled),
            now,
            now,
            "{}",
        ),
    )
    conn.commit()
    conn.close()
    return settings


def list_ai_providers(db_path: Path) -> list[dict[str, Any]]:
    from .providers import MockProvider, NullProvider, provider_from_settings

    settings = load_ai_settings(db_path)
    providers = [NullProvider(), MockProvider()]
    configured = provider_from_settings(settings)
    if configured is not None and all(item.provider_id != configured.provider_id for item in providers):
        providers.append(configured)
    return [provider.info(settings).to_dict() for provider in providers]


def save_ai_request(db_path: Path, request: AIRequest, response: dict[str, Any]) -> None:
    conn = connect(db_path)
    storage_project_id = _resolve_storage_project_id(db_path, request)
    conn.execute(
        """
        INSERT INTO ai_requests(
            request_id, project_id, conversation_id, question, intent, mode,
            provider_id, model, context_json, response_json, status, latency_ms,
            created_at, completed_at, usage_json, safety_json, tool_audit_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(request_id) DO UPDATE SET
            response_json=excluded.response_json,
            status=excluded.status,
            latency_ms=excluded.latency_ms,
            completed_at=excluded.completed_at,
            usage_json=excluded.usage_json,
            safety_json=excluded.safety_json,
            tool_audit_json=excluded.tool_audit_json
        """,
        (
            request.request_id,
            storage_project_id,
            request.conversation_id,
            request.question,
            request.intent,
            request.mode,
            request.provider_id,
            request.model,
            _safe_json(request.context_snapshot),
            _safe_json(response),
            response.get("status", "unknown"),
            int(response.get("latency_ms", 0) or 0),
            request.created_at,
            response.get("completed_at", _now()),
            _safe_json(response.get("usage", {})),
            _safe_json(response.get("safety", [])),
            _safe_json(response.get("tool_calls", [])),
        ),
    )
    conn.commit()
    conn.close()


def save_ai_conversation_turn(db_path: Path, request: AIRequest, response: dict[str, Any], title: str | None = None) -> AIConversationTurn:
    conn = connect(db_path)
    conversation_id = request.conversation_id or uuid.uuid4().hex
    now = response.get("completed_at", _now())
    storage_project_id = _resolve_storage_project_id(db_path, request)
    if request.conversation_id is None:
        conn.execute(
            """
            INSERT INTO ai_conversations(conversation_id, project_id, title, provider_id, model, status, created_at, updated_at, metadata_json)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                updated_at=excluded.updated_at,
                title=COALESCE(NULLIF(excluded.title, ''), ai_conversations.title),
                provider_id=excluded.provider_id,
                model=excluded.model
            """,
            (
                conversation_id,
                storage_project_id,
                title or request.question[:80],
                request.provider_id,
                request.model,
                "active",
                request.created_at,
                now,
                "{}",
            ),
        )
    else:
        conn.execute(
            """
            UPDATE ai_conversations
            SET title=COALESCE(NULLIF(?, ''), title),
                provider_id=?,
                model=?,
                updated_at=?,
                status='active'
            WHERE conversation_id=?
            """,
            (title or request.question[:80], request.provider_id, request.model, now, conversation_id),
        )
    turn = AIConversationTurn(
        turn_id=uuid.uuid4().hex,
        request_id=request.request_id,
        conversation_id=conversation_id,
        # Persist under a real project id when the request is portfolio-scoped.
        # The response still keeps the original request.project_id for caller visibility.
        project_id=storage_project_id,
        question=request.question,
        response=response,
        context_snapshot=request.context_snapshot,
        citations=response.get("citations", []),
        provider_id=request.provider_id,
        model=request.model,
        intent=request.intent,
        mode=request.mode,
        status=response.get("status", "unknown"),
        created_at=request.created_at,
        completed_at=now,
        usage=response.get("usage", {}),
        safety=response.get("safety", []),
    )
    conn.execute(
        """
        INSERT INTO ai_conversation_turns(
            turn_id, conversation_id, project_id, request_id, question, response_json,
            context_json, citations_json, provider_id, model, intent, mode,
            status, created_at, completed_at, usage_json, safety_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            turn.turn_id,
            turn.conversation_id,
            turn.project_id,
            turn.request_id,
            turn.question,
            _safe_json(turn.response),
            _safe_json(turn.context_snapshot),
            _safe_json(turn.citations),
            turn.provider_id,
            turn.model,
            turn.intent,
            turn.mode,
            turn.status,
            turn.created_at,
            turn.completed_at,
            _safe_json(turn.usage),
            _safe_json(turn.safety),
        ),
    )
    for citation in response.get("citations", []):
        conn.execute(
            """
            INSERT INTO ai_request_citations(
                citation_id, request_id, conversation_id, project_id, entity_id, source_type,
                path, relationship, scan_id, snapshot_id, timestamp, confidence, excerpt,
                title, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(citation.get("citation_id") or uuid.uuid4().hex),
                request.request_id,
                turn.conversation_id,
                storage_project_id,
                str(citation.get("entity_id") or ""),
                str(citation.get("source_type") or ""),
                str(citation.get("path") or ""),
                str(citation.get("relationship") or ""),
                str(citation.get("scan_id") or ""),
                str(citation.get("snapshot_id") or ""),
                str(citation.get("timestamp") or ""),
                float(citation.get("confidence", 0.0) or 0.0),
                str(citation.get("excerpt") or ""),
                str(citation.get("title") or ""),
                _safe_json(citation),
            ),
        )
    conn.commit()
    conn.close()
    return turn


def create_ai_conversation(db_path: Path, project_id: str, title: str, provider_id: str = "", model: str = "") -> dict[str, Any]:
    conn = connect(db_path)
    conversation_id = uuid.uuid4().hex
    now = _now()
    conn.execute(
        """
        INSERT INTO ai_conversations(
            conversation_id, project_id, title, provider_id, model, status, created_at, updated_at, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            conversation_id,
            project_id,
            title,
            provider_id,
            model,
            "active",
            now,
            now,
            "{}",
        ),
    )
    conn.commit()
    conn.close()
    return {
        "conversation_id": conversation_id,
        "project_id": project_id,
        "title": title,
        "provider_id": provider_id,
        "model": model,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "turn_count": 0,
        "turns": [],
    }


def list_ai_conversations(db_path: Path, project_id: str | None = None) -> list[dict[str, Any]]:
    conn = connect(db_path)
    if project_id:
        rows = conn.execute(
            """
            SELECT conversation_id, project_id, title, provider_id, model, status, created_at, updated_at
            FROM ai_conversations
            WHERE project_id=?
            ORDER BY updated_at DESC, created_at DESC, conversation_id DESC
            """,
            (project_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT conversation_id, project_id, title, provider_id, model, status, created_at, updated_at
            FROM ai_conversations
            ORDER BY updated_at DESC, created_at DESC, conversation_id DESC
            """
        ).fetchall()
    conversations: list[dict[str, Any]] = []
    for row in rows:
        turns = conn.execute(
            """
            SELECT turn_id, request_id, conversation_id, project_id, question, response_json,
                   context_json, citations_json, provider_id, model, intent, mode, status,
                   created_at, completed_at, usage_json, safety_json
            FROM ai_conversation_turns
            WHERE conversation_id=?
            ORDER BY created_at ASC, turn_id ASC
            """,
            (row["conversation_id"],),
        ).fetchall()
        conversations.append(
            {
                "conversation_id": row["conversation_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "provider_id": row["provider_id"],
                "model": row["model"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "turn_count": len(turns),
                "turns": [dict(turn) | {"response_json": json.loads(turn["response_json"]) if turn["response_json"] else {}} for turn in turns],
            }
        )
    conn.close()
    return conversations


def get_ai_conversation(db_path: Path, conversation_id: str) -> dict[str, Any] | None:
    conn = connect(db_path)
    row = conn.execute(
        """
        SELECT conversation_id, project_id, title, provider_id, model, status, created_at, updated_at
        FROM ai_conversations
        WHERE conversation_id=?
        """,
        (conversation_id,),
    ).fetchone()
    if row is None:
        conn.close()
        return None
    turns = conn.execute(
        """
        SELECT turn_id, request_id, conversation_id, project_id, question, response_json,
               context_json, citations_json, provider_id, model, intent, mode, status,
               created_at, completed_at, usage_json, safety_json
        FROM ai_conversation_turns
        WHERE conversation_id=?
        ORDER BY created_at ASC, turn_id ASC
        """,
        (conversation_id,),
    ).fetchall()
    conn.close()
    return {
        "conversation_id": row["conversation_id"],
        "project_id": row["project_id"],
        "title": row["title"],
        "provider_id": row["provider_id"],
        "model": row["model"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "turn_count": len(turns),
        "turns": [dict(turn) | {"response_json": json.loads(turn["response_json"]) if turn["response_json"] else {}} for turn in turns],
    }


def get_ai_request(db_path: Path, request_id: str) -> dict[str, Any] | None:
    conn = connect(db_path)
    row = conn.execute("SELECT * FROM ai_requests WHERE request_id=?", (request_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_ai_requests(db_path: Path, conversation_id: str | None = None) -> list[dict[str, Any]]:
    conn = connect(db_path)
    if conversation_id:
        rows = conn.execute(
            "SELECT * FROM ai_requests WHERE conversation_id=? ORDER BY created_at DESC, request_id DESC",
            (conversation_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM ai_requests ORDER BY created_at DESC, request_id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_ai_request_citations(db_path: Path, request_id: str) -> list[dict[str, Any]]:
    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT * FROM ai_request_citations
        WHERE request_id=?
        ORDER BY confidence DESC, citation_id ASC
        """,
        (request_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
