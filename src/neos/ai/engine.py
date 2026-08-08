from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core import (
    api_inventory,
    build_inventory,
    configuration_inventory,
    context_bundle,
    decision_inventory,
    documentation_inventory,
    feature_inventory,
    git_state_report,
    impact_entity,
    latest_project_memory,
    project_summary,
    symbol_inventory,
    test_inventory,
    trace_entity,
    why_entity,
)
from ..db import connect
from ..flight import flight_incidents, flight_regressions, flight_timeline, latest_project_flight
from ..genome import (
    genome_attention,
    genome_domains,
    genome_risks,
    genome_unknowns,
    latest_project_genome,
)
from ..memory import memory_gaps, memory_timeline
from ..semantic import contains_suspicious_instruction
from .models import (
    AICitation,
    AIContextBundle,
    AIEvidenceItem,
    AIInference,
    AIRecommendation,
    AIRequest,
    AIResponse,
    AISafetyFinding,
    AISettings,
    AIUnknown,
)
from .providers import AIProvider, MockProvider, NullProvider, provider_from_settings
from .store import load_ai_settings, save_ai_conversation_turn, save_ai_request

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
}


def classify_intent(question: str, mode: str | None = None) -> str:
    lowered = question.lower().strip()
    if mode:
        return mode.lower()
    if any(token in lowered for token in ("what should i work on next", "what should i investigate next", "next action", "priority")):
        return "plan"
    if lowered.startswith("why ") or " why " in f" {lowered} ":
        return "why_query"
    if any(token in lowered for token in ("what would break", "what could break", "impact", "break if")):
        return "impact_query"
    if any(token in lowered for token in ("what changed", "since version", "since the previous", "recently changed", "change since")):
        return "change_query"
    if any(token in lowered for token in ("risk", "risks", "should concern", "what should concern me")):
        return "risk_query"
    if any(token in lowered for token in ("test", "tests", "evidence", "validation")):
        return "test_query"
    if any(token in lowered for token in ("documentation", "docs", "readme")):
        return "documentation_query"
    if any(token in lowered for token in ("api", "endpoint", "route")):
        return "api_query"
    if any(token in lowered for token in ("config", "setting", "endpoint", "provider")):
        return "configuration_query"
    if any(token in lowered for token in ("feature", "capability")):
        return "feature_status"
    if any(token in lowered for token in ("timeline", "history", "replay")):
        return "timeline_query"
    if any(token in lowered for token in ("review", "review the evidence", "release readiness")):
        return "review"
    if any(token in lowered for token in ("explain", "architecture", "designed this way")):
        return "architecture_explanation"
    return "project_summary"


def _tokens(question: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", question)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def _stale_message(db_path: Path, project_id: str) -> tuple[bool, str]:
    conn = connect(db_path)
    scan = conn.execute(
        "SELECT repo_head, created_at, scan_id FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    project = conn.execute("SELECT repo_path FROM projects WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    if not scan:
        return False, ""
    repo_path = Path(project["repo_path"]) if project else None
    if repo_path is None:
        return False, ""
    try:
        import subprocess

        current = subprocess.check_output(["git", "-C", str(repo_path), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError, ValueError):
        return False, ""
    observed = str(scan["repo_head"] or "").strip()
    if observed and observed != current:
        return True, f"Engineering intelligence is based on commit {observed}; repository is currently at {current}."
    return False, ""


def _rank_score(question_tokens: list[str], text: str, intent: str, recency_rank: int = 0) -> float:
    lowered = text.lower()
    score = 0.0
    for token in question_tokens:
        if token in lowered:
            score += 4.0
        if token in lowered.split():
            score += 1.0
    intent_map = {
        "why_query": ("decision", "why", "memory", "lesson"),
        "impact_query": ("impact", "dependency", "trace", "feature"),
        "change_query": ("flight", "snapshot", "diff", "timeline"),
        "risk_query": ("risk", "unknown", "attention", "gap"),
        "test_query": ("test", "documentation", "api", "symbol"),
        "documentation_query": ("documentation", "readme", "guide"),
        "api_query": ("api", "endpoint", "route"),
        "configuration_query": ("config", "setting", "endpoint", "provider"),
        "feature_status": ("feature", "requirement"),
        "timeline_query": ("timeline", "history", "flight"),
        "plan": ("attention", "risk", "unknown", "gap"),
    }
    for token in intent_map.get(intent, ()):
        if token in lowered:
            score += 3.0
    score += max(0.0, 3.0 - recency_rank * 0.35)
    return score


def _fact_item(
    project_id: str,
    entity_type: str,
    entity_id: str,
    path: str,
    excerpt: str,
    *,
    source_type: str,
    relationship: str = "",
    scan_id: str = "",
    snapshot_id: str = "",
    timestamp: str = "",
    confidence: float = 0.6,
    metadata: dict[str, Any] | None = None,
    suspicious: bool = False,
    stale: bool = False,
    rank_score: float = 0.0,
) -> AIEvidenceItem:
    return AIEvidenceItem(
        entity_id=entity_id,
        entity_type=entity_type,
        project_id=project_id,
        source_type=source_type,
        path=str(path or ""),
        excerpt="" if excerpt is None else str(excerpt),
        relationship=relationship,
        scan_id=scan_id,
        snapshot_id=snapshot_id,
        timestamp=timestamp,
        confidence=confidence,
        rank_score=rank_score,
        stale=stale,
        suspicious_instruction_like_content=suspicious,
        metadata=metadata or {},
    )


def search_evidence(db_path: Path, project_id: str, question: str, intent: str, budget: int = 24) -> list[AIEvidenceItem]:
    tokens = _tokens(question)
    bundle = context_bundle(db_path, project_id, question)
    _stale_result = _stale_message(db_path, project_id)
    conn = connect(db_path)
    scan = conn.execute(
        "SELECT * FROM scans WHERE project_id=? ORDER BY created_at DESC, scan_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    scan_id = scan["scan_id"] if scan else ""
    latest_snapshot = conn.execute(
        "SELECT id FROM flight_snapshots WHERE project_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    snapshot_id = latest_snapshot["id"] if latest_snapshot else ""
    project = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    repo_path = Path(project["repo_path"]) if project else None

    candidates: list[AIEvidenceItem] = []
    seen: set[tuple[str, str, str]] = set()

    def add(item: AIEvidenceItem) -> None:
        key = (item.entity_type, item.entity_id, item.path)
        if key not in seen:
            seen.add(key)
            candidates.append(item)

    summary = project_summary(db_path, project_id)
    add(
        _fact_item(
            project_id,
            "project",
            project_id,
            "project",
            summary.get("summary", summary.get("name", project_id)),
            source_type="project_summary",
            scan_id=scan_id,
            snapshot_id=snapshot_id,
            confidence=0.95,
            metadata={"summary": summary},
        )
    )

    genome = latest_project_genome(db_path, project_id)
    if genome:
        add(
            _fact_item(
                project_id,
                "genome",
                genome.get("project_id", project_id),
                "genome",
                genome.get("summary", {}).get("vision", genome.get("summary", {}).get("project_type", "Project genome")),
                source_type="genome",
                scan_id=scan_id,
                snapshot_id=snapshot_id,
                timestamp=genome.get("created_at", ""),
                confidence=0.9,
                metadata={"genome": genome.get("summary", {})},
            )
        )
        for item in genome_domains(genome).get("items", [])[:8]:
            add(
                _fact_item(
                    project_id,
                    "domain",
                    item.get("id", item.get("name", "")),
                    item.get("name", "domain"),
                    item.get("description", ""),
                    source_type="genome_domain",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=float(item.get("confidence", 0.6) or 0.6),
                    metadata=item,
                )
            )
        for item in genome_risks(genome).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "risk",
                    item.get("id", item.get("title", "")),
                    item.get("title", "risk"),
                    item.get("reason", item.get("description", "")),
                    source_type="genome_risk",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=float(item.get("confidence", 0.5) or 0.5),
                    metadata=item,
                )
            )
        for item in genome_unknowns(genome).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "unknown",
                    item.get("id", item.get("title", "")),
                    item.get("title", "unknown"),
                    item.get("description", item.get("reason", "")),
                    source_type="genome_unknown",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=float(item.get("confidence", 0.4) or 0.4),
                    metadata=item,
                )
            )
        for item in genome_attention(genome).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "attention",
                    item.get("id", item.get("title", "")),
                    item.get("title", "attention"),
                    item.get("reason", item.get("description", "")),
                    source_type="genome_attention",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=float(item.get("confidence", 0.6) or 0.6),
                    metadata=item,
                )
            )

    memory = latest_project_memory(db_path, project_id)
    if memory:
        for item in memory_timeline(memory).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "memory",
                    item.get("id", item.get("title", "")),
                    item.get("source_path", "memory"),
                    item.get("summary", ""),
                    source_type="memory_timeline",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    timestamp=item.get("timestamp", ""),
                    confidence=float(item.get("confidence", 0.6) or 0.6),
                    metadata=item,
                )
            )
        for item in memory_gaps(memory).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "memory_gap",
                    item.get("id", item.get("title", "")),
                    item.get("source_path", "memory"),
                    item.get("reason", item.get("summary", "")),
                    source_type="memory_gap",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=float(item.get("confidence", 0.4) or 0.4),
                    metadata=item,
                )
            )

    flight = latest_project_flight(db_path, project_id)
    if flight:
        for item in flight_timeline(db_path, project_id).get("items", [])[:8]:
            add(
                _fact_item(
                    project_id,
                    "flight_event",
                    item.get("id", item.get("label", "")),
                    item.get("source_ref", item.get("label", "flight")),
                    item.get("summary", ""),
                    source_type="flight_timeline",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    timestamp=item.get("timestamp", ""),
                    confidence=float(item.get("confidence", 0.6) or 0.6),
                    metadata=item,
                )
            )
        for item in flight_regressions(db_path, project_id).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "regression",
                    item.get("id", item.get("summary", "")),
                    item.get("source_ref", "flight"),
                    item.get("summary", ""),
                    source_type="flight_regression",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    timestamp=item.get("timestamp", ""),
                    confidence=float(item.get("confidence", 0.5) or 0.5),
                    metadata=item,
                )
            )
        for item in flight_incidents(db_path, project_id).get("items", [])[:6]:
            add(
                _fact_item(
                    project_id,
                    "incident",
                    item.get("id", item.get("summary", "")),
                    item.get("source", "flight"),
                    item.get("summary", ""),
                    source_type="flight_incident",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    timestamp=item.get("timestamp", ""),
                    confidence=float(item.get("confidence", 0.5) or 0.5),
                    metadata=item,
                )
            )

    for inventory_fn, entity_type, source_type in (
        (feature_inventory, "feature", "feature_inventory"),
        (decision_inventory, "decision", "decision_inventory"),
        (documentation_inventory, "documentation", "documentation_inventory"),
        (test_inventory, "test", "test_inventory"),
        (api_inventory, "api", "api_inventory"),
        (configuration_inventory, "config", "configuration_inventory"),
        (build_inventory, "build", "build_inventory"),
        (symbol_inventory, "symbol", "symbol_inventory"),
    ):
        try:
            payload = inventory_fn(db_path, project_id)
        except (OSError, ValueError, TypeError, sqlite3.Error):
            continue
        for item in payload.get("items", [])[:12]:
            text = item.get("description") or item.get("summary") or item.get("label") or item.get("name") or ""
            path = item.get("source_path") or item.get("path") or item.get("route") or item.get("name") or entity_type
            confidence = float(item.get("confidence", 0.6) or 0.6)
            add(
                _fact_item(
                    project_id,
                    entity_type,
                    item.get("id", item.get("name", path)),
                    path,
                    text,
                    source_type=source_type,
                    scan_id=item.get("scan_id", scan_id),
                    snapshot_id=snapshot_id,
                    timestamp=item.get("created_at", item.get("observed_at", "")),
                    confidence=confidence,
                    metadata=item,
                    suspicious=contains_suspicious_instruction(text),
                )
            )

    if project is not None:
        for payload, entity_type, source_type in (
            (why_entity(db_path, project_id), "why", "why_entity"),
            (impact_entity(db_path, project_id), "impact", "impact_entity"),
            (trace_entity(db_path, project_id), "trace", "trace_entity"),
            (git_state_report(db_path, project_id), "git_state", "git_state_report"),
        ):
            if isinstance(payload, dict):
                excerpt = payload.get("summary") or payload.get("reason") or payload.get("answer") or payload.get("status") or ""
                add(
                    _fact_item(
                        project_id,
                        entity_type,
                        payload.get("entity_id", project_id),
                        payload.get("source_path", entity_type),
                        excerpt,
                        source_type=source_type,
                        scan_id=scan_id,
                        snapshot_id=snapshot_id,
                        confidence=0.8,
                        metadata=payload,
                        suspicious=contains_suspicious_instruction(excerpt),
                    )
                )

    for item in bundle.get("selected_facts", []):
        excerpt = item.get("summary") or item.get("description") or item.get("text") or ""
        path = item.get("evidence_path") or item.get("source_path") or item.get("path") or "evidence"
        add(
            _fact_item(
                project_id,
                item.get("kind", "evidence"),
                item.get("entity_id", path),
                path,
                excerpt,
                source_type="context_bundle",
                scan_id=scan_id,
                snapshot_id=snapshot_id,
                timestamp=item.get("timestamp", ""),
                confidence=float(item.get("confidence", 0.6) or 0.6),
                metadata=item,
                suspicious=contains_suspicious_instruction(excerpt),
            )
        )

    if repo_path is not None and repo_path.exists():
        for warning in bundle.get("warnings", []):
            add(
                _fact_item(
                    project_id,
                    "warning",
                    uuid.uuid4().hex,
                    str(repo_path),
                    warning,
                    source_type="context_warning",
                    scan_id=scan_id,
                    snapshot_id=snapshot_id,
                    confidence=0.3,
                    metadata={"warning": warning},
                    suspicious=True,
                )
            )

    ranked: list[AIEvidenceItem] = []
    for index, item in enumerate(candidates):
        ranked.append(
            AIEvidenceItem(
                entity_id=item.entity_id,
                entity_type=item.entity_type,
                project_id=item.project_id,
                source_type=item.source_type,
                path=item.path,
                excerpt=item.excerpt,
                relationship=item.relationship,
                scan_id=item.scan_id,
                snapshot_id=item.snapshot_id,
                timestamp=item.timestamp,
                confidence=item.confidence,
                rank_score=_rank_score(tokens, f"{item.entity_id} {item.path} {item.excerpt}", intent, index),
                stale=item.stale,
                suspicious_instruction_like_content=item.suspicious_instruction_like_content,
                metadata=item.metadata,
            )
        )
    ranked.sort(key=lambda item: (-item.rank_score, -item.confidence, item.path, item.entity_id))
    conn.close()
    return ranked[: max(1, budget)]


def _citations_for_items(items: list[AIEvidenceItem]) -> list[AICitation]:
    citations: list[AICitation] = []
    for index, item in enumerate(items, start=1):
        citations.append(
            AICitation(
                citation_id=f"cite-{index}",
                entity_id=item.entity_id,
                source_type=item.source_type,
                path=item.path,
                relationship=item.relationship,
                scan_id=item.scan_id,
                snapshot_id=item.snapshot_id,
                timestamp=item.timestamp,
                confidence=item.confidence,
                excerpt=item.excerpt,
                title=item.entity_type,
            )
        )
    return citations


def _derive_facts(items: list[AIEvidenceItem]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for item in items[:8]:
        facts.append(
            {
                "kind": "derived_fact",
                "entity_id": item.entity_id,
                "entity_type": item.entity_type,
                "path": item.path,
                "excerpt": item.excerpt,
                "source_type": item.source_type,
                "confidence": item.confidence,
            }
        )
    return facts


def _infer(question: str, intent: str, evidence: list[AIEvidenceItem]) -> list[AIInference]:
    if not evidence:
        return [AIInference(text="No bounded canonical evidence was found.", basis="evidence retrieval")]
    top = evidence[0]
    question_lower = question.lower()
    if intent == "why_query":
        return [AIInference(text=f"The likely rationale is connected to {top.path}.", basis=top.entity_type)]
    if intent == "impact_query":
        return [AIInference(text=f"Changing {top.path} could affect dependent surfaces linked in the evidence graph.", basis=top.entity_type)]
    if intent == "change_query":
        return [AIInference(text=f"Observed changes are concentrated around {top.path}.", basis=top.source_type)]
    if intent == "risk_query":
        return [AIInference(text=f"The strongest current concern is the evidence gap around {top.path}.", basis=top.entity_type)]
    if intent == "plan":
        return [AIInference(text="The next work should follow the highest-attention evidence and remaining unknowns.", basis="attention/risk/unknown evidence")]
    if "what should i work on next" in question_lower:
        return [AIInference(text="Prioritize attention items, open risks, and unresolved memory gaps.", basis="priority workflow")]
    return [AIInference(text=f"The answer should stay bounded to the strongest evidence around {top.path}.", basis=top.entity_type)]


def _recommend(question: str, intent: str, evidence: list[AIEvidenceItem]) -> list[AIRecommendation]:
    if not evidence:
        return [AIRecommendation(text="Collect more canonical evidence before answering.", priority="high", basis="no evidence")]
    top = evidence[0]
    if intent == "plan":
        return [
            AIRecommendation(text=f"Investigate {top.path} first.", priority="high", basis=top.entity_type),
            AIRecommendation(text="Check the latest scan and flight evidence for stale or missing coverage.", priority="medium", basis="freshness"),
        ]
    if intent in {"why_query", "impact_query"}:
        return [AIRecommendation(text=f"Inspect the evidence behind {top.path} before changing it.", priority="high", basis=top.entity_type)]
    return [AIRecommendation(text="Use the citation panel to verify the exact source evidence before acting.", priority="medium", basis="citation workflow")]


def _unknowns(question: str, evidence: list[AIEvidenceItem], context: AIContextBundle) -> list[AIUnknown]:
    unknowns: list[AIUnknown] = []
    if context.stale_scan:
        unknowns.append(AIUnknown(text=context.stale_message, basis="stale evidence"))
    if not evidence:
        unknowns.append(AIUnknown(text="No bounded canonical evidence was found for this question.", basis="retrieval"))
    else:
        unknowns.append(AIUnknown(text=f"Evidence is strongest around {evidence[0].path}, but not all dependencies may be covered.", basis=evidence[0].entity_type))
    if "?" in question and "unknown" in question.lower():
        unknowns.append(AIUnknown(text="The question is explicitly asking about missing information, so uncertainty should stay visible.", basis="question wording"))
    return unknowns[:4]


def _context_summary(question: str, evidence: list[AIEvidenceItem], context: AIContextBundle) -> dict[str, Any]:
    return {
        "question": question,
        "intent": context.intent,
        "mode": context.mode,
        "project_id": context.project_id,
        "evidence_count": len(evidence),
        "token_estimate": context.token_estimate,
        "truncated": context.truncated,
        "stale_scan": context.stale_scan,
        "stale_message": context.stale_message,
        "sources": context.context_sources,
        "warnings": context.warnings,
        "limitations": context.limitations,
    }


def build_context_bundle(
    db_path: Path,
    project_id: str,
    question: str,
    *,
    conversation: dict[str, Any] | None = None,
    mode: str | None = None,
    context_budget: int = 24,
) -> AIContextBundle:
    intent = classify_intent(question, mode)
    request_id = uuid.uuid4().hex
    created_at = datetime.now(UTC).isoformat()
    raw_bundle = context_bundle(db_path, project_id, question)
    settings = load_ai_settings(db_path)
    evidence = search_evidence(db_path, project_id, question, intent, budget=context_budget)
    citations = _citations_for_items(evidence)
    stale, stale_message = _stale_message(db_path, project_id)
    warnings = list(raw_bundle.get("warnings", []))
    limitations = list(raw_bundle.get("limitations", []))
    context_sources = list(raw_bundle.get("evidence_paths", []))
    if conversation and conversation.get("turns"):
        last_turn = conversation["turns"][-1]
        warnings.append(f"Follow-up context includes previous conversation turn {last_turn.get('turn_id', '')}.")

    selected_facts = [
        {
            "kind": item.entity_type,
            "entity_id": item.entity_id,
            "evidence_path": item.path,
            "summary": item.excerpt,
            "confidence": item.confidence,
            "source_type": item.source_type,
            "rank_score": item.rank_score,
        }
        for item in evidence
    ]
    derived_facts = _derive_facts(evidence)
    evidence_text = " ".join(str(item.excerpt) for item in evidence)
    token_estimate = max(1, len(question.split()) + len(evidence_text.split()) + len(json.dumps(raw_bundle)) // 8)
    context_stub = AIContextBundle(
        request_id=request_id,
        project_id=project_id,
        question=question,
        intent=intent,
        mode=mode or intent,
        created_at=created_at,
        context_budget=settings.context_budget if settings.context_budget else context_budget,
        evidence_items=[],
        selected_facts=[],
        derived_facts=[],
        inferences=[],
        recommendations=[],
        unknowns=[],
        warnings=warnings,
        limitations=limitations,
        context_sources=context_sources,
        citations=[],
        stale_scan=stale,
        stale_message=stale_message,
        truncated=False,
        token_estimate=token_estimate,
    )
    bundle = AIContextBundle(
        request_id=request_id,
        project_id=project_id,
        question=question,
        intent=intent,
        mode=mode or intent,
        created_at=created_at,
        context_budget=settings.context_budget if settings.context_budget else context_budget,
        evidence_items=evidence,
        selected_facts=selected_facts,
        derived_facts=derived_facts,
        inferences=_infer(question, intent, evidence),
        recommendations=_recommend(question, intent, evidence),
        unknowns=_unknowns(question, evidence, context_stub),
        warnings=warnings,
        limitations=limitations,
        context_sources=context_sources,
        citations=citations,
        stale_scan=stale,
        stale_message=stale_message,
        truncated=token_estimate > (settings.context_budget or context_budget) * 70,
        token_estimate=token_estimate,
        tool_calls=[],
        safety_findings=[
            AISafetyFinding(
                code="suspicious_instruction_like_content",
                level="warning",
                message="Repository content containing instruction-like language was treated as untrusted evidence.",
            )
        ]
        if any(item.suspicious_instruction_like_content for item in evidence)
        else [],
    )
    return bundle


class AIEngine:
    def __init__(self, db_path: Path, provider: AIProvider | None = None, settings: AISettings | None = None):
        self.db_path = db_path
        self.settings = settings or load_ai_settings(db_path)
        self.provider = provider or provider_from_settings(self.settings) or MockProvider()

    def provider_info(self) -> dict[str, Any]:
        return self.provider.info(self.settings).to_dict()

    def provider_health(self) -> dict[str, Any]:
        return self.provider.health().to_dict()

    def settings_payload(self) -> dict[str, Any]:
        return self.settings.to_dict()

    def save_settings(self, settings: AISettings) -> dict[str, Any]:
        from .store import save_ai_settings

        self.settings = save_ai_settings(self.db_path, settings)
        self.provider = provider_from_settings(self.settings) or MockProvider()
        return self.settings.to_dict()

    def list_conversations(self, project_id: str | None = None) -> list[dict[str, Any]]:
        from .store import list_ai_conversations

        return list_ai_conversations(self.db_path, project_id=project_id)

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        from .store import get_ai_conversation

        return get_ai_conversation(self.db_path, conversation_id)

    def query(
        self,
        project_id: str,
        question: str,
        *,
        conversation_id: str | None = None,
        mode: str | None = None,
        title: str | None = None,
    ) -> AIResponse:
        request_id = uuid.uuid4().hex
        intent = classify_intent(question, mode)
        bundle = build_context_bundle(self.db_path, project_id, question, conversation=self.get_conversation(conversation_id) if conversation_id else None, mode=mode, context_budget=self.settings.context_budget)
        request = AIRequest(
            request_id=request_id,
            project_id=project_id,
            question=question,
            intent=intent,
            mode=mode or intent,
            conversation_id=conversation_id,
            provider_id=self.provider.provider_id,
            model=self.settings.model,
            created_at=bundle.created_at,
            context_snapshot=bundle.to_dict(),
            tool_permission="read",
            tool_calls=[],
        )
        if isinstance(self.provider, NullProvider):
            response = AIResponse(
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                project_id=request.project_id,
                question=request.question,
                intent=request.intent,
                mode=request.mode,
                provider=self.provider.provider_id,
                model=self.settings.model,
                created_at=request.created_at,
                completed_at=bundle.created_at,
                status="provider_not_configured",
                answer="AI provider not configured. The evidence context is available for review, but generation is disabled.",
                facts=bundle.selected_facts,
                derived_facts=bundle.derived_facts,
                inferences=bundle.inferences,
                recommendations=bundle.recommendations,
                unknowns=[AIUnknown(text="AI provider not configured.", basis="settings")],
                citations=bundle.citations,
                context_snapshot=bundle.to_dict(),
                latency_ms=0,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0},
                safety=bundle.safety_findings,
                tool_calls=[],
                confidence="unknown",
            )
        else:
            response = self.provider.generate(request, bundle)
        save_ai_request(self.db_path, request, response.to_dict())
        turn = save_ai_conversation_turn(self.db_path, request, response.to_dict(), title=title)
        if response.conversation_id is None:
            response = replace(response, conversation_id=turn.conversation_id)
        if request.conversation_id is None:
            request = replace(request, conversation_id=turn.conversation_id)
        save_ai_request(self.db_path, request, response.to_dict())
        return response

    def context_bundle(self, project_id: str, question: str, *, mode: str | None = None) -> AIContextBundle:
        return build_context_bundle(self.db_path, project_id, question, mode=mode, context_budget=self.settings.context_budget)

    def list_requests(self, conversation_id: str | None = None) -> list[dict[str, Any]]:
        from .store import list_ai_requests

        return list_ai_requests(self.db_path, conversation_id=conversation_id)

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        from .store import get_ai_request

        return get_ai_request(self.db_path, request_id)

    def list_citations(self, request_id: str) -> list[dict[str, Any]]:
        from .store import list_ai_request_citations

        return list_ai_request_citations(self.db_path, request_id)
