from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _to_dict(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dict(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class AIModelCapability:
    name: str
    supported: bool
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIProviderInfo:
    provider_id: str
    name: str
    kind: str
    configured: bool
    local: bool
    endpoint: str = ""
    model: str = ""
    healthy: bool = False
    latency_ms: int | None = None
    capabilities: list[AIModelCapability] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIEvidenceItem:
    entity_id: str
    entity_type: str
    project_id: str
    source_type: str
    path: str
    excerpt: str
    relationship: str = ""
    scan_id: str = ""
    snapshot_id: str = ""
    timestamp: str = ""
    confidence: float = 0.0
    rank_score: float = 0.0
    stale: bool = False
    suspicious_instruction_like_content: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AICitation:
    citation_id: str
    entity_id: str
    source_type: str
    path: str
    relationship: str = ""
    scan_id: str = ""
    snapshot_id: str = ""
    timestamp: str = ""
    confidence: float = 0.0
    excerpt: str = ""
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIInference:
    text: str
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIUnknown:
    text: str
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIRecommendation:
    text: str
    priority: str = "medium"
    basis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIUsageRecord:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AISafetyFinding:
    code: str
    level: str
    message: str
    evidence_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIMessage:
    role: str
    content: str
    created_at: str = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIContextBundle:
    request_id: str
    project_id: str
    question: str
    intent: str
    mode: str
    created_at: str
    context_budget: int
    evidence_items: list[AIEvidenceItem] = field(default_factory=list)
    selected_facts: list[dict[str, Any]] = field(default_factory=list)
    derived_facts: list[dict[str, Any]] = field(default_factory=list)
    inferences: list[AIInference] = field(default_factory=list)
    recommendations: list[AIRecommendation] = field(default_factory=list)
    unknowns: list[AIUnknown] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    context_sources: list[str] = field(default_factory=list)
    citations: list[AICitation] = field(default_factory=list)
    stale_scan: bool = False
    stale_message: str = ""
    truncated: bool = False
    token_estimate: int = 0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    safety_findings: list[AISafetyFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AISettings:
    provider_id: str = "mock"
    model: str = "mock-engineer-v1"
    endpoint: str = ""
    api_key_env: str = "NEOS_AI_API_KEY"
    timeout_seconds: int = 30
    context_budget: int = 24
    max_output_tokens: int = 1200
    streaming: bool = False
    temperature: float = 0.2
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AISettings:
        return cls(
            provider_id=str(data.get("provider_id", "mock") or "mock"),
            model=str(data.get("model", "mock-engineer-v1") or "mock-engineer-v1"),
            endpoint=str(data.get("endpoint", "") or ""),
            api_key_env=str(data.get("api_key_env", "NEOS_AI_API_KEY") or "NEOS_AI_API_KEY"),
            timeout_seconds=int(data.get("timeout_seconds", 30) or 30),
            context_budget=int(data.get("context_budget", 24) or 24),
            max_output_tokens=int(data.get("max_output_tokens", 1200) or 1200),
            streaming=bool(data.get("streaming", False)),
            temperature=float(data.get("temperature", 0.2) or 0.2),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(frozen=True)
class AIRequest:
    request_id: str
    project_id: str
    question: str
    intent: str
    mode: str
    conversation_id: str | None
    provider_id: str
    model: str
    created_at: str = field(default_factory=_utcnow)
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    tool_permission: str = "read"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIResponse:
    request_id: str
    conversation_id: str | None
    project_id: str
    question: str
    intent: str
    mode: str
    provider: str
    model: str
    created_at: str
    completed_at: str
    status: str
    answer: str
    facts: list[dict[str, Any]] = field(default_factory=list)
    derived_facts: list[dict[str, Any]] = field(default_factory=list)
    inferences: list[AIInference] = field(default_factory=list)
    recommendations: list[AIRecommendation] = field(default_factory=list)
    unknowns: list[AIUnknown] = field(default_factory=list)
    citations: list[AICitation] = field(default_factory=list)
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    usage: dict[str, Any] = field(default_factory=dict)
    safety: list[AISafetyFinding] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    confidence: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIConversationTurn:
    turn_id: str
    request_id: str
    conversation_id: str
    project_id: str
    question: str
    response: dict[str, Any]
    context_snapshot: dict[str, Any]
    citations: list[dict[str, Any]]
    provider_id: str
    model: str
    intent: str
    mode: str
    status: str
    created_at: str
    completed_at: str
    usage: dict[str, Any] = field(default_factory=dict)
    safety: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))


@dataclass(frozen=True)
class AIConversation:
    conversation_id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str
    provider_id: str = ""
    model: str = ""
    status: str = "active"
    turns: list[AIConversationTurn] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(asdict(self))
