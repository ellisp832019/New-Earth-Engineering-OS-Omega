from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .ecosystem import analyse_portfolio
from .flight import flight_incidents, flight_regressions
from .genome import latest_project_genome
from .memory import latest_project_memory, memory_gaps

ENGINE_VERSION = "1.3.0"

DECISION_TYPES = {
    "architecture",
    "feature_ownership",
    "reuse",
    "refactor",
    "release_readiness",
    "risk_priority",
    "technical_debt",
    "implementation_choice",
    "dependency_change",
    "standardization",
    "test_priority",
    "documentation_priority",
    "project_priority",
    "engineering_next_action",
}

REVIEW_STATES = {
    "draft",
    "evaluated",
    "review_pending",
    "accepted",
    "rejected",
    "deferred",
    "superseded",
}

STRENGTH_ORDER = ("strong", "moderate", "weak", "insufficient_evidence", "conflicted")

DEFAULT_OPTIONS = {
    "engineering_next_action": ["address_now", "plan", "monitor", "defer"],
    "project_priority": ["focus_now", "plan_next", "monitor", "defer"],
    "release_readiness": ["READY", "READY_WITH_CONDITIONS", "NOT_READY", "INSUFFICIENT_EVIDENCE"],
    "reuse": ["REUSE_NOW", "REVIEW_FIRST", "KEEP_PROJECT_SPECIFIC", "INSUFFICIENT_EVIDENCE"],
    "architecture": ["Option A", "Option B", "Option C", "Defer"],
    "feature_ownership": ["Current project", "Shared platform module", "Other project", "Defer"],
    "refactor": ["refactor_now", "plan_refactor", "monitor", "leave_as_is"],
    "risk_priority": ["mitigate", "investigate", "defer", "accept"],
    "technical_debt": ["address_now", "plan", "monitor", "low_priority"],
    "implementation_choice": ["Option A", "Option B", "Option C", "Defer"],
    "dependency_change": ["change_now", "review_first", "defer", "keep_current"],
    "standardization": ["standardize_now", "review_first", "keep_project_specific", "defer"],
    "test_priority": ["test_now", "plan", "monitor", "defer"],
    "documentation_priority": ["document_now", "plan", "monitor", "defer"],
}

DECISION_CRITERIA = {
    "architecture": ["existing architecture consistency", "dependency impact", "reuse", "complexity", "testability", "risk", "decision history", "project constraints"],
    "feature_ownership": ["existing implementation", "architecture fit", "maturity", "reuse demand", "project boundaries", "dependencies", "ownership decisions", "testing", "long-term coupling"],
    "reuse": ["implementation maturity", "test evidence", "documentation", "coupling", "external dependencies", "stability", "target compatibility", "adaptation effort", "cross-project demand", "risk"],
    "refactor": ["coupling", "duplicate engineering", "test gaps", "dependency centrality", "stale interfaces", "technical debt", "change frequency", "incidents"],
    "release_readiness": ["tests", "validation", "known risks", "unknowns", "release evidence", "documentation", "blocking incidents", "regressions"],
    "risk_priority": ["severity", "impact", "likelihood", "unknown surface", "cross-project effect", "freshness", "mitigation effort"],
    "technical_debt": ["impact", "risk", "frequency of change", "dependencies", "release relevance", "unknown surface"],
    "implementation_choice": ["architecture fit", "reuse", "tests", "documentation", "risk", "unknowns"],
    "dependency_change": ["dependency impact", "test coverage", "regression risk", "release relevance", "unknown surface"],
    "standardization": ["portfolio demand", "compatibility", "reuse", "coupling", "maintenance cost", "project boundaries"],
    "test_priority": ["risk", "impact", "change recency", "lack of test evidence", "release relevance", "known regressions", "hardware validation gaps"],
    "documentation_priority": ["release relevance", "feature maturity", "user impact", "test support", "unknown surface"],
    "project_priority": ["release blockers", "risk severity", "high-impact unknowns", "failed tests", "regressions", "stale evidence", "technical debt"],
    "engineering_next_action": ["release blockers", "risk severity", "high-impact unknowns", "failed tests", "regressions", "stale evidence", "technical debt", "reuse opportunities"],
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _stable_id(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _uniq(items: list[str]) -> list[str]:
    return [item for index, item in enumerate(items) if item and item not in items[:index]]


def _score_to_strength(score: float, support: int, oppose: int, unknowns: int, contradictions: int, evidence_count: int) -> str:
    if evidence_count == 0 or support + oppose == 0:
        return "insufficient_evidence"
    if contradictions > 0 and oppose > 0 and support > 0:
        return "conflicted"
    if support >= 4 and oppose == 0 and unknowns <= 1 and score >= 4.0:
        return "strong"
    if support >= 2 and oppose <= 1 and unknowns <= 2 and score >= 1.5:
        return "moderate"
    if support > 0 and support >= oppose:
        return "weak"
    if oppose > support:
        return "conflicted"
    return "insufficient_evidence"


def _coerce_project_ids(project_id: str | None = None, project_ids: list[str] | None = None, scope: str | None = None, all_projects: list[str] | None = None) -> list[str]:
    if project_ids:
        return _uniq([item.strip() for item in project_ids if item and item.strip()])
    if scope == "portfolio":
        return _uniq([item.strip() for item in (all_projects or []) if item and item.strip()])
    if project_id and project_id.strip():
        return [project_id.strip()]
    return _uniq([item.strip() for item in (all_projects or []) if item and item.strip()])


@dataclass(frozen=True)
class DecisionQuestion:
    id: str
    project_id: str
    title: str
    description: str
    decision_type: str
    created_at: str
    status: str
    source: str
    scope: str
    related_entities: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionOption:
    id: str
    question_id: str
    name: str
    description: str
    source: str
    constraints: list[str] = field(default_factory=list)
    affected_entities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionEvidence:
    id: str
    question_id: str
    option_id: str
    evidence_type: str
    entity_id: str
    project_id: str
    source: str
    confidence: float
    supports_or_opposes: str
    weight_category: str
    provenance: str
    age: str = "current"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionAssessment:
    option_id: str
    option_name: str
    score: float
    strength: str
    supporting_factors: list[dict[str, Any]] = field(default_factory=list)
    opposing_factors: list[dict[str, Any]] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecommendationFactor:
    label: str
    detail: str
    weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecommendationRisk:
    label: str
    detail: str
    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecommendationUnknown:
    label: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecommendationAlternative:
    option_id: str
    name: str
    strength: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionRecommendation:
    id: str
    question_id: str
    recommended_option: str
    strength: str
    summary: str
    supporting_factors: list[RecommendationFactor] = field(default_factory=list)
    opposing_factors: list[RecommendationFactor] = field(default_factory=list)
    risks: list[RecommendationRisk] = field(default_factory=list)
    assumptions: list[RecommendationFactor] = field(default_factory=list)
    unknowns: list[RecommendationUnknown] = field(default_factory=list)
    alternatives: list[RecommendationAlternative] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    engine_version: str = ENGINE_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionScenario:
    id: str
    question_id: str
    description: str
    change: str
    affected_entities: list[str] = field(default_factory=list)
    expectations: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionOutcomeExpectation:
    label: str
    expectation: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionReview:
    id: str
    question_id: str
    operator: str
    review_state: str
    selected_option: str
    notes: str
    created_at: str = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionAcceptance:
    id: str
    question_id: str
    operator: str
    decision: str
    notes: str
    selected_option: str
    created_at: str = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _decision_defaults(decision_type: str) -> list[dict[str, str]]:
    names = DEFAULT_OPTIONS.get(decision_type, ["Option A", "Option B", "Option C", "Defer"])
    return [{"name": name, "description": "", "source": "deterministic-default"} for name in names]


def _decision_criteria(decision_type: str) -> list[str]:
    return DECISION_CRITERIA.get(decision_type, DECISION_CRITERIA["engineering_next_action"])


def _default_question(db_path: Path, project_ids: list[str], decision_type: str, title: str, description: str, source: str, scope: str, related_entities: list[str]) -> DecisionQuestion:
    question_id = f"decision-q-{_stable_id(decision_type, title, description, project_ids, scope)}"
    return DecisionQuestion(
        id=question_id,
        project_id=project_ids[0] if project_ids else "portfolio",
        title=title,
        description=description,
        decision_type=decision_type,
        created_at=_utcnow(),
        status="draft",
        source=source,
        scope=scope,
        related_entities=related_entities,
        project_ids=project_ids,
        metadata={"criteria": _decision_criteria(decision_type)},
    )


def _portfolio_profile(db_path: Path, project_ids: list[str]) -> dict[str, Any]:
    analysis = analyse_portfolio(db_path, project_ids=project_ids or None, name="decision-intelligence")
    projects = analysis["projects"]
    return {
        "analysis": analysis,
        "project_count": len(projects),
        "health": analysis["health"],
        "risks": analysis["portfolio_risks"],
        "unknowns": analysis["unknown_surface"],
        "attention": analysis["attention"],
        "reuse_candidates": analysis["reuse_candidates"],
        "duplicate_findings": analysis["duplicate_findings"],
        "dependencies": analysis["cross_project_dependencies"],
        "decision_conflicts": analysis["decision_conflicts"],
        "shared_capabilities": analysis["capability_matrix"]["shared_capabilities"],
        "shared_technologies": analysis["technology_portfolio"]["shared_technologies"],
        "projects_by_id": {project["project_id"]: project for project in projects},
    }


def _evidence_items_for_profile(profile: dict[str, Any], decision_type: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    analysis = profile["analysis"]
    for project in analysis["projects"]:
        items.append(
            {
                "evidence_type": "project_health",
                "entity_id": project["project_id"],
                "project_id": project["project_id"],
                "source": "project_registry",
                "confidence": 0.95,
                "supports": project.get("status") != "archived",
                "supports_or_opposes": "supports" if project.get("status") != "archived" else "opposes",
                "weight_category": "strong",
                "provenance": "project_registry_v2",
                "summary": project.get("summary", ""),
                "metadata": project,
            }
        )
    for item in analysis["attention"][:12]:
        items.append(
            {
                "evidence_type": "attention",
                "entity_id": item["id"],
                "project_id": item.get("project_id", "portfolio") if isinstance(item, dict) else "portfolio",
                "source": "attention",
                "confidence": float(item.get("confidence", 0.7) or 0.7),
                "supports": True,
                "supports_or_opposes": "supports",
                "weight_category": "moderate",
                "provenance": "portfolio_attention",
                "summary": item.get("summary", ""),
                "metadata": item,
            }
        )
    for item in analysis["portfolio_risks"][:12]:
        items.append(
            {
                "evidence_type": "risk",
                "entity_id": item["id"],
                "project_id": item.get("affected_projects", ["portfolio"])[0] if item.get("affected_projects") else "portfolio",
                "source": "portfolio_risks",
                "confidence": float(item.get("confidence", 0.7) or 0.7),
                "supports": False,
                "supports_or_opposes": "opposes",
                "weight_category": "moderate",
                "provenance": "portfolio_risks",
                "summary": item.get("reason", ""),
                "metadata": item,
            }
        )
    for item in analysis["unknown_surface"][:12]:
        items.append(
            {
                "evidence_type": "unknown",
                "entity_id": item["id"],
                "project_id": item["project_id"],
                "source": "unknown_surface",
                "confidence": 0.4,
                "supports": False,
                "supports_or_opposes": "opposes",
                "weight_category": "weak",
                "provenance": "unknown_surface",
                "summary": ", ".join(item.get("unknown_items", [])),
                "metadata": item,
            }
        )
    for item in analysis["reuse_candidates"][:12]:
        items.append(
            {
                "evidence_type": "reuse_candidate",
                "entity_id": item["candidate_id"],
                "project_id": item["source_project"],
                "source": "reuse_candidates",
                "confidence": float(item.get("confidence", 0.8) or 0.8),
                "supports": True,
                "supports_or_opposes": "supports",
                "weight_category": "strong",
                "provenance": "reuse_candidates",
                "summary": item.get("reason", ""),
                "metadata": item,
            }
        )
    for item in analysis["duplicate_findings"][:12]:
        items.append(
            {
                "evidence_type": "duplicate_finding",
                "entity_id": item["id"],
                "project_id": item["project_ids"][0] if item.get("project_ids") else "portfolio",
                "source": "duplicate_findings",
                "confidence": float(item.get("confidence", 0.7) or 0.7),
                "supports": False,
                "supports_or_opposes": "opposes",
                "weight_category": "moderate",
                "provenance": "duplicate_findings",
                "summary": item.get("reason", ""),
                "metadata": item,
            }
        )
    for item in analysis["decision_conflicts"][:12]:
        items.append(
            {
                "evidence_type": "decision_conflict",
                "entity_id": item["id"],
                "project_id": item["project_a"],
                "source": "decision_conflicts",
                "confidence": float(item.get("confidence", 0.5) or 0.5),
                "supports": item.get("conflict_type") == "aligned",
                "supports_or_opposes": "supports" if item.get("conflict_type") == "aligned" else "opposes",
                "weight_category": "moderate",
                "provenance": "decision_conflicts",
                "summary": item.get("reason", ""),
                "metadata": item,
            }
        )
    return items


def _keyword_match(text: str, *keywords: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords if keyword)


def _decision_support(option: DecisionOption, evidence_item: dict[str, Any], decision_type: str, profile: dict[str, Any], question_text: str) -> tuple[bool, float, str]:
    text = " ".join(
        [
            option.name,
            option.description,
            question_text,
            str(evidence_item.get("summary", "")),
            json.dumps(evidence_item.get("metadata", {}), sort_keys=True),
        ]
    ).lower()
    weight = float(evidence_item.get("confidence", 0.5) or 0.5)
    if evidence_item.get("weight_category") == "strong":
        weight *= 1.2
    elif evidence_item.get("weight_category") == "weak":
        weight *= 0.7
    if decision_type == "release_readiness":
        if option.name in {"READY", "READY_WITH_CONDITIONS"}:
            return (
                _keyword_match(text, "test", "documentation", "health", "ready", "coverage") and not _keyword_match(text, "regression", "incident", "unknown", "gap"),
                weight,
                "release gate evidence",
            )
        if option.name == "NOT_READY":
            return (
                _keyword_match(text, "regression", "incident", "unknown", "gap", "missing", "stale", "risk"),
                weight,
                "release blocker evidence",
            )
        return (True, weight * 0.5, "fallback evidence")
    if decision_type == "reuse":
        if option.name == "REUSE_NOW":
            return (
                _keyword_match(text, "reuse", "shared", "stable", "tested", "documentation", "common"),
                weight,
                "reuse evidence",
            )
        if option.name == "KEEP_PROJECT_SPECIFIC":
            return (
                _keyword_match(text, "coupling", "duplicate", "dependency", "project-specific", "integration", "risk"),
                weight,
                "coupling evidence",
            )
        if option.name == "REVIEW_FIRST":
            return (
                _keyword_match(text, "risk", "unknown", "dependency", "coupling", "shared"),
                weight,
                "review evidence",
            )
    if decision_type in {"engineering_next_action", "project_priority"}:
        if option.name in {"address_now", "focus_now"}:
            return (
                _keyword_match(text, "risk", "unknown", "regression", "blocker", "gap", "high"),
                weight,
                "priority evidence",
            )
        if option.name in {"plan", "plan_next"}:
            return (
                _keyword_match(text, "debt", "reuse", "test", "documentation", "attention"),
                weight,
                "planning evidence",
            )
        if option.name in {"monitor", "defer"}:
            return (
                _keyword_match(text, "low", "stable", "current", "fresh"),
                weight,
                "monitor evidence",
            )
    if decision_type == "test_priority":
        if option.name == "test_now":
            return (
                _keyword_match(text, "untested", "regression", "risk", "gap", "critical"),
                weight,
                "test gap evidence",
            )
        if option.name == "defer":
            return (
                _keyword_match(text, "stable", "tested", "documented"),
                weight,
                "low-priority evidence",
            )
    if decision_type == "technical_debt" and option.name == "address_now":
        return (
            _keyword_match(text, "debt", "risk", "coupling", "duplicate", "stale"),
            weight,
            "debt evidence",
        )
    if decision_type == "architecture" and option.name.lower().startswith("option"):
        if "a" in option.name.lower():
            return (_keyword_match(text, "consistent", "existing", "aligned", "low coupling"), weight, "architecture fit")
        if "b" in option.name.lower():
            return (_keyword_match(text, "reuse", "shared", "standard"), weight, "reuse/standardization fit")
        return (_keyword_match(text, "defer", "unknown", "insufficient"), weight * 0.5, "defer evidence")
    if decision_type == "feature_ownership":
        if option.name == "Current project":
            return (_keyword_match(text, "existing implementation", "current", "ownership", "local"), weight, "ownership evidence")
        if option.name == "Shared platform module":
            return (_keyword_match(text, "shared", "reuse", "cross-project", "standard"), weight, "platform evidence")
    if decision_type == "risk_priority":
        if option.name == "mitigate":
            return (_keyword_match(text, "high", "risk", "blocker", "incident"), weight, "mitigation evidence")
        if option.name == "investigate":
            return (_keyword_match(text, "unknown", "gap", "stale", "conflict"), weight, "investigation evidence")
    if decision_type == "refactor" and option.name == "refactor_now":
        return (_keyword_match(text, "duplicate", "coupling", "stale", "risk", "incident"), weight, "refactor evidence")
    if decision_type == "documentation_priority" and option.name == "document_now":
        return (_keyword_match(text, "undocumented", "docs", "missing", "release"), weight, "documentation evidence")
    if decision_type == "dependency_change" and option.name == "change_now":
        return (_keyword_match(text, "dependency", "coupling", "shared", "risk"), weight, "dependency evidence")
    if decision_type == "standardization" and option.name == "standardize_now":
        return (_keyword_match(text, "shared", "reuse", "consistent", "duplicate"), weight, "standardization evidence")
    if decision_type == "implementation_choice" and option.name.lower().startswith("option"):
        return (_keyword_match(text, "existing", "evidence", "fit", "compatible"), weight, "implementation evidence")
    return (_keyword_match(text, option.name, option.description), weight, "generic evidence")


def _assess_options(question: DecisionQuestion, options: list[DecisionOption], evidence_items: list[dict[str, Any]], profile: dict[str, Any]) -> tuple[list[DecisionAssessment], DecisionRecommendation]:
    assessments: list[DecisionAssessment] = []
    question_text = f"{question.title} {question.description}"
    best: DecisionAssessment | None = None
    for option in options:
        supporting: list[dict[str, Any]] = []
        opposing: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        assumptions: list[str] = []
        unknowns: list[str] = []
        evidence_ids: list[str] = []
        score = 0.0
        contradictions = 0
        support_count = 0
        oppose_count = 0
        for item in evidence_items:
            supports, weight, rationale = _decision_support(option, item, question.decision_type, profile, question_text)
            evidence_id = f"evidence-{_stable_id(question.id, option.id, item['evidence_type'], item['entity_id'])}"
            evidence_ids.append(evidence_id)
            if supports:
                support_count += 1
                score += weight
                supporting.append(
                    {
                        "label": item["evidence_type"],
                        "detail": item.get("summary", ""),
                        "weight": round(weight, 3),
                        "source": item.get("source", ""),
                        "entity_id": item.get("entity_id", ""),
                        "project_id": item.get("project_id", ""),
                        "provenance": item.get("provenance", ""),
                        "rationale": rationale,
                    }
                )
            else:
                oppose_count += 1
                score -= weight
                opposing.append(
                    {
                        "label": item["evidence_type"],
                        "detail": item.get("summary", ""),
                        "weight": round(weight, 3),
                        "source": item.get("source", ""),
                        "entity_id": item.get("entity_id", ""),
                        "project_id": item.get("project_id", ""),
                        "provenance": item.get("provenance", ""),
                        "rationale": rationale,
                    }
                )
        if question.decision_type == "release_readiness":
            if profile["health"]["score"] < 50:
                oppose_count += 1
                score -= 1.5
                risks.append({"label": "low_health", "detail": "Overall portfolio health is low.", "severity": "high"})
                unknowns.append("health score is below the safe threshold")
            if profile["project_count"] == 0:
                unknowns.append("no registered projects were found")
        if question.decision_type in {"engineering_next_action", "project_priority"} and profile["risks"]:
            risks.append({"label": "portfolio_risks", "detail": "Open portfolio risks deserve attention.", "severity": "high"})
        if question.decision_type == "reuse" and profile["duplicate_findings"]:
            risks.append({"label": "duplication", "detail": "Potential duplication needs review before reuse.", "severity": "medium"})
            score -= 0.5
        if question.decision_type == "architecture" and profile["decision_conflicts"]:
            contradictions += len(profile["decision_conflicts"])
            score -= 0.5 * len(profile["decision_conflicts"])
        strength = _score_to_strength(score, support_count, oppose_count, len(unknowns), contradictions, len(evidence_items))
        explanation = f"{support_count} supporting signals versus {oppose_count} opposing signals."
        assessment = DecisionAssessment(
            option_id=option.id,
            option_name=option.name,
            score=round(score, 3),
            strength=strength,
            supporting_factors=supporting[:8],
            opposing_factors=opposing[:8],
            risks=risks[:8],
            assumptions=assumptions,
            unknowns=unknowns,
            evidence_ids=evidence_ids[:24],
            explanation=explanation,
        )
        assessments.append(assessment)
        if best is None or assessment.score > best.score:
            best = assessment
    if best is None:
        best = DecisionAssessment(option_id="", option_name="", score=0.0, strength="insufficient_evidence", explanation="No options were available.")
    alternatives = [
        RecommendationAlternative(
            option_id=assessment.option_id,
            name=assessment.option_name,
            strength=assessment.strength,
            summary=assessment.explanation,
        )
        for assessment in assessments
        if assessment.option_id != best.option_id
    ]
    recommendation = DecisionRecommendation(
        id=f"decision-rec-{_stable_id(question.id, best.option_id, best.strength)}",
        question_id=question.id,
        recommended_option=best.option_name,
        strength=best.strength,
        summary=f"Recommended option: {best.option_name}. {best.explanation}".strip(),
        supporting_factors=[RecommendationFactor(label=factor["label"], detail=factor["detail"], weight=factor["weight"]) for factor in best.supporting_factors[:6]],
        opposing_factors=[RecommendationFactor(label=factor["label"], detail=factor["detail"], weight=factor["weight"]) for factor in best.opposing_factors[:6]],
        risks=[RecommendationRisk(label=risk["label"], detail=risk["detail"], severity=risk.get("severity", "medium")) for risk in best.risks[:6]],
        assumptions=[RecommendationFactor(label="assumption", detail=item, weight=0.0) for item in best.assumptions],
        unknowns=[RecommendationUnknown(label="unknown", detail=item) for item in best.unknowns[:6]],
        alternatives=alternatives,
        metadata={"criteria": _decision_criteria(question.decision_type)},
    )
    return assessments, recommendation


def _persist_decision_state(
    db_path: Path,
    question: DecisionQuestion,
    options: list[DecisionOption],
    evidence_items: list[dict[str, Any]],
    recommendation: DecisionRecommendation,
) -> None:
    conn = connect(db_path)
    now = _utcnow()
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_questions(
            id, project_id, title, description, decision_type, status, scope_json,
            source, related_entities_json, created_at, updated_at, engine_version, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            question.id,
            question.project_id,
            question.title,
            question.description,
            question.decision_type,
            "review_pending",
            _json_dumps(question.project_ids or [question.project_id]),
            question.source,
            _json_dumps(question.related_entities),
            question.created_at,
            now,
            ENGINE_VERSION,
            _json_dumps(question.metadata),
        ),
    )
    conn.execute("DELETE FROM decision_options WHERE question_id=?", (question.id,))
    conn.execute("DELETE FROM decision_intelligence_evidence WHERE question_id=?", (question.id,))
    conn.execute("DELETE FROM decision_recommendations WHERE question_id=?", (question.id,))
    for option in options:
        conn.execute(
            """
            INSERT OR REPLACE INTO decision_options(
                id, question_id, name, description, source, constraints_json, affected_entities_json, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                option.id,
                option.question_id,
                option.name,
                option.description,
                option.source,
                _json_dumps(option.constraints),
                _json_dumps(option.affected_entities),
                _json_dumps(option.metadata),
            ),
        )
    for item in evidence_items:
        conn.execute(
            """
            INSERT OR REPLACE INTO decision_intelligence_evidence(
                id, question_id, option_id, evidence_type, entity_id, project_id, source,
                confidence, supports_or_opposes, weight_category, provenance, metadata_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item["id"],
                item["question_id"],
                item["option_id"],
                item["evidence_type"],
                item["entity_id"],
                item["project_id"],
                item["source"],
                item["confidence"],
                item["supports_or_opposes"],
                item["weight_category"],
                item["provenance"],
                _json_dumps(item.get("metadata", {})),
            ),
        )
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_recommendations(
            id, question_id, recommended_option, strength, summary, supporting_factors_json,
            opposing_factors_json, risks_json, assumptions_json, unknowns_json, alternatives_json,
            created_at, engine_version, metadata_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            recommendation.id,
            recommendation.question_id,
            recommendation.recommended_option,
            recommendation.strength,
            recommendation.summary,
            _json_dumps([factor.to_dict() for factor in recommendation.supporting_factors]),
            _json_dumps([factor.to_dict() for factor in recommendation.opposing_factors]),
            _json_dumps([risk.to_dict() for risk in recommendation.risks]),
            _json_dumps([factor.to_dict() for factor in recommendation.assumptions]),
            _json_dumps([unknown.to_dict() for unknown in recommendation.unknowns]),
            _json_dumps([alt.to_dict() for alt in recommendation.alternatives]),
            recommendation.created_at,
            recommendation.engine_version,
            _json_dumps(recommendation.metadata),
        ),
    )
    conn.commit()
    conn.close()


def _load_question_row(row: Any) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "title": row["title"],
        "description": row["description"],
        "decision_type": row["decision_type"],
        "status": row["status"],
        "scope": _json_loads(row["scope_json"], []),
        "source": row["source"],
        "related_entities": _json_loads(row["related_entities_json"], []),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "engine_version": row["engine_version"],
        "metadata": _json_loads(row["metadata_json"], {}),
    }


def evaluate_decision_question(
    db_path: Path,
    title: str,
    description: str,
    decision_type: str,
    *,
    project_id: str | None = None,
    project_ids: list[str] | None = None,
    scope: str = "project",
    source: str = "operator",
    options: list[dict[str, Any]] | None = None,
    constraints: list[str] | None = None,
    related_entities: list[str] | None = None,
) -> dict[str, Any]:
    scope_ids = _coerce_project_ids(project_id, project_ids, scope)
    if decision_type not in DECISION_TYPES:
        decision_type = "engineering_next_action"
    profile = _portfolio_profile(db_path, scope_ids)
    question = _default_question(db_path, scope_ids, decision_type, title, description, source, scope, related_entities or [])
    raw_options = options if options else _decision_defaults(decision_type)
    option_models = [
        DecisionOption(
            id=f"decision-option-{_stable_id(question.id, index, item.get('name', 'option'))}",
            question_id=question.id,
            name=str(item.get("name", f"Option {index + 1}")),
            description=str(item.get("description", "")),
            source=str(item.get("source", source)),
            constraints=[str(value) for value in (item.get("constraints") or constraints or [])],
            affected_entities=[str(value) for value in (item.get("affected_entities") or related_entities or [])],
            metadata={key: value for key, value in item.items() if key not in {"name", "description", "source", "constraints", "affected_entities"}},
        )
        for index, item in enumerate(raw_options)
    ]
    evidence_pool = _evidence_items_for_profile(profile, decision_type)
    assessments, recommendation = _assess_options(question, option_models, evidence_pool, profile)
    recommendation = DecisionRecommendation(
        id=recommendation.id,
        question_id=recommendation.question_id,
        recommended_option=recommendation.recommended_option,
        strength=recommendation.strength,
        summary=recommendation.summary,
        supporting_factors=recommendation.supporting_factors,
        opposing_factors=recommendation.opposing_factors,
        risks=recommendation.risks,
        assumptions=recommendation.assumptions,
        unknowns=recommendation.unknowns,
        alternatives=recommendation.alternatives,
        created_at=recommendation.created_at,
        engine_version=ENGINE_VERSION,
        metadata={**recommendation.metadata, "project_ids": scope_ids, "decision_type": decision_type},
    )
    evidence_rows: list[dict[str, Any]] = []
    for option in option_models:
        for item in evidence_pool[:24]:
            evidence_id = f"evidence-{_stable_id(question.id, option.id, item['evidence_type'], item['entity_id'])}"
            evidence_rows.append(
                {
                    "id": evidence_id,
                    "question_id": question.id,
                    "option_id": option.id,
                    "evidence_type": item["evidence_type"],
                    "entity_id": item["entity_id"],
                    "project_id": item["project_id"],
                    "source": item["source"],
                    "confidence": item["confidence"],
                    "supports_or_opposes": item["supports_or_opposes"],
                    "weight_category": item["weight_category"],
                    "provenance": item["provenance"],
                    "metadata": item.get("metadata", {}),
                }
            )
    _persist_decision_state(db_path, question, option_models, evidence_rows, recommendation)
    return {
        "question": question.to_dict(),
        "criteria": _decision_criteria(decision_type),
        "options": [option.to_dict() for option in option_models],
        "evidence": evidence_rows,
        "assessments": [assessment.to_dict() for assessment in assessments],
        "recommendation": recommendation.to_dict(),
        "profile": {
            "project_count": profile["project_count"],
            "health": profile["health"],
            "risk_count": len(profile["risks"]),
            "unknown_count": len(profile["unknowns"]),
            "attention_count": len(profile["attention"]),
            "reuse_count": len(profile["reuse_candidates"]),
            "duplicate_count": len(profile["duplicate_findings"]),
            "decision_conflict_count": len(profile["decision_conflicts"]),
        },
    }


def get_next_actions(db_path: Path, *, project_ids: list[str] | None = None) -> dict[str, Any]:
    profile = _portfolio_profile(db_path, project_ids or [])
    question = "What should I work on next?"
    result = evaluate_decision_question(
        db_path,
        "Engineering next action",
        question,
        "engineering_next_action",
        project_ids=project_ids,
        scope="portfolio",
        source="deterministic-priority-engine",
    )
    items = []
    for assessment in result["assessments"]:
        items.append(
            {
                "what": assessment["option_name"],
                "why": assessment["explanation"],
                "urgency": assessment["strength"],
                "impact": "high" if assessment["strength"] in {"strong", "moderate"} else "medium",
                "evidence": assessment["supporting_factors"][:5],
                "constraints": DECISION_CRITERIA["engineering_next_action"],
                "suggested_next_action": assessment["option_name"],
                "unknowns": assessment["unknowns"],
                "score": assessment["score"],
            }
        )
    items.sort(key=lambda item: (-item["score"], STRENGTH_ORDER.index(item["urgency"]) if item["urgency"] in STRENGTH_ORDER else len(STRENGTH_ORDER)))
    return {
        "question": question,
        "scope": _coerce_project_ids(project_ids=project_ids, scope="portfolio", all_projects=[project["project_id"] for project in profile["analysis"]["projects"]]),
        "items": items,
        "profile": {"health": profile["health"], "risks": len(profile["risks"]), "unknowns": len(profile["unknowns"]), "attention": len(profile["attention"])},
    }


def get_release_readiness(db_path: Path, project_id: str) -> dict[str, Any]:
    conn = connect(db_path)
    project = conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    if not project:
        return {
            "project_id": project_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "blocking_criteria": ["project not registered"],
            "passed_criteria": [],
            "warnings": [],
            "unknowns": ["project not registered"],
            "evidence": [],
            "recommendation": {},
        }
    genome = latest_project_genome(db_path, project_id)
    memory = latest_project_memory(db_path, project_id)
    regressions = flight_regressions(db_path, project_id).get("items", [])
    incidents = flight_incidents(db_path, project_id).get("items", [])
    unknowns = []
    evidence = []
    passed = []
    blockers = []
    if genome:
        if genome.get("testing", {}).get("summary", {}).get("score", 0) >= 70:
            passed.append("tests")
        else:
            blockers.append("tests")
        if genome.get("documentation", {}).get("summary", {}).get("score", 0) >= 60:
            passed.append("documentation")
        else:
            blockers.append("documentation")
        if genome.get("quality", {}).get("traceability", {}).get("score", 0) >= 60:
            passed.append("traceability")
        else:
            unknowns.append("traceability is weak")
        evidence.append({"label": "genome_health", "value": genome.get("health", {}), "source": "project_genome"})
    if memory:
        evidence.append({"label": "memory_health", "value": memory.get("summary", {}), "source": "project_memory"})
        gaps = memory_gaps(memory)
        if gaps.get("items"):
            unknowns.append(f"{gaps['count']} memory gap(s) still need closure")
            evidence.append({"label": "memory_gaps", "value": gaps, "source": "memory_gaps"})
    if regressions:
        blockers.append("regressions")
        evidence.append({"label": "regressions", "value": regressions[:5], "source": "flight_regressions"})
    if incidents:
        blockers.append("incidents")
        evidence.append({"label": "incidents", "value": incidents[:5], "source": "flight_incidents"})
    if not genome:
        unknowns.append("project genome is missing")
        blockers.append("genome")
    readiness_status = "READY"
    if blockers:
        readiness_status = "NOT_READY"
    elif unknowns:
        readiness_status = "READY_WITH_CONDITIONS"
    if not genome and not memory and not regressions and not incidents:
        readiness_status = "INSUFFICIENT_EVIDENCE"
    return {
        "project_id": project_id,
        "status": readiness_status,
        "blocking_criteria": _uniq(blockers),
        "passed_criteria": _uniq(passed),
        "warnings": unknowns[:10],
        "unknowns": unknowns[:10],
        "evidence": evidence,
        "recommendation": {
            "decision_type": "release_readiness",
            "recommended_option": readiness_status,
            "strength": "strong" if readiness_status == "READY" else "moderate" if readiness_status == "READY_WITH_CONDITIONS" else "weak" if readiness_status == "NOT_READY" else "insufficient_evidence",
            "summary": f"Release readiness for {project_id} is {readiness_status}.",
        },
    }


def review_reuse_candidate(db_path: Path, *, project_ids: list[str] | None = None) -> dict[str, Any]:
    profile = _portfolio_profile(db_path, project_ids or [])
    candidate = profile["analysis"]["reuse_candidates"][0] if profile["analysis"]["reuse_candidates"] else None
    if candidate is None:
        return {"status": "INSUFFICIENT_EVIDENCE", "candidates": [], "recommendation": {}}
    question = "Should this become a shared module?"
    result = evaluate_decision_question(
        db_path,
        "Reuse decision",
        question,
        "reuse",
        project_ids=project_ids,
        scope="portfolio",
        source="deterministic-reuse-review",
        options=[
            {"name": "REUSE_NOW", "description": candidate["reason"]},
            {"name": "REVIEW_FIRST", "description": "Inspect coupling and adaptation effort."},
            {"name": "KEEP_PROJECT_SPECIFIC", "description": "Keep the capability local to the source project."},
            {"name": "INSUFFICIENT_EVIDENCE", "description": "Collect more evidence before deciding."},
        ],
    )
    return {
        "status": result["recommendation"]["recommended_option"],
        "candidates": profile["analysis"]["reuse_candidates"][:10],
        "question": result["question"],
        "criteria": result["criteria"],
        "recommendation": result["recommendation"],
        "assessments": result["assessments"],
    }


def review_architecture_options(
    db_path: Path,
    question_text: str,
    options: list[dict[str, Any]],
    *,
    project_ids: list[str] | None = None,
) -> dict[str, Any]:
    result = evaluate_decision_question(
        db_path,
        "Architecture review",
        question_text,
        "architecture",
        project_ids=project_ids,
        scope="portfolio" if project_ids else "project",
        source="deterministic-architecture-review",
        options=options,
    )
    return {
        "question": result["question"],
        "criteria": result["criteria"],
        "options": result["options"],
        "assessments": result["assessments"],
        "recommendation": result["recommendation"],
    }


def run_scenario_analysis(
    db_path: Path,
    scenario: dict[str, Any],
    *,
    project_ids: list[str] | None = None,
) -> dict[str, Any]:
    title = str(scenario.get("title") or scenario.get("name") or "Scenario analysis")
    change = str(scenario.get("change") or scenario.get("description") or "")
    affected_entities = [str(item) for item in scenario.get("affected_entities", []) if str(item).strip()]
    scope_ids = _coerce_project_ids(project_ids=project_ids, scope="portfolio" if project_ids else "project")
    profile = _portfolio_profile(db_path, scope_ids)
    impact = []
    for entity in affected_entities[:8]:
        impact.append(
            {
                "entity_id": entity,
                "expected_effect": "review required",
                "evidence": [entity, change],
            }
        )
    if not impact and profile["analysis"]["projects"]:
        impact.append(
            {
                "entity_id": profile["analysis"]["projects"][0]["project_id"],
                "expected_effect": "review required",
                "evidence": [change or title],
            }
        )
    return {
        "scenario": {
            "id": f"scenario-{_stable_id(title, change, scope_ids)}",
            "title": title,
            "change": change,
            "project_ids": scope_ids,
            "affected_entities": affected_entities,
        },
        "expected_affected_areas": impact,
        "known_required_changes": [item["entity_id"] for item in impact],
        "possible_impacts": [item["expected_effect"] for item in impact],
        "unknown_impacts": profile["unknowns"][:8],
        "evidence_gaps": profile["attention"][:8],
    }


def decision_history(db_path: Path, *, project_ids: list[str] | None = None) -> dict[str, Any]:
    conn = connect(db_path)
    if project_ids:
        placeholders = ", ".join(["?"] * len(project_ids))
        question_rows = conn.execute(
            f"SELECT * FROM decision_questions WHERE project_id IN ({placeholders}) ORDER BY created_at DESC, id DESC",
            tuple(project_ids),
        ).fetchall()
    else:
        question_rows = conn.execute("SELECT * FROM decision_questions ORDER BY created_at DESC, id DESC").fetchall()
    question_items = []
    for row in question_rows:
        q = _load_question_row(row)
        recommendation = conn.execute(
            "SELECT * FROM decision_recommendations WHERE question_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (q["id"],),
        ).fetchone()
        review = conn.execute(
            "SELECT * FROM decision_reviews WHERE question_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (q["id"],),
        ).fetchone()
        question_items.append(
            {
                "question": q,
                "recommendation": dict(recommendation) if recommendation else {},
                "review": dict(review) if review else {},
            }
        )
    conn.close()
    return {"count": len(question_items), "items": question_items}


def _update_question_status(db_path: Path, question_id: str, status: str) -> dict[str, Any]:
    if status not in REVIEW_STATES:
        raise ValueError(f"Unsupported decision state: {status}")
    conn = connect(db_path)
    question = conn.execute("SELECT * FROM decision_questions WHERE id=?", (question_id,)).fetchone()
    if question is None:
        conn.close()
        raise ValueError(f"Unknown decision question: {question_id}")
    conn.execute("UPDATE decision_questions SET status=?, updated_at=? WHERE id=?", (status, _utcnow(), question_id))
    conn.commit()
    updated = conn.execute("SELECT * FROM decision_questions WHERE id=?", (question_id,)).fetchone()
    conn.close()
    return {"question": _load_question_row(updated)}


def accept_decision(db_path: Path, question_id: str, *, operator: str = "operator", selected_option: str = "", notes: str = "") -> dict[str, Any]:
    now = _utcnow()
    conn = connect(db_path)
    question = conn.execute("SELECT * FROM decision_questions WHERE id=?", (question_id,)).fetchone()
    if question is None:
        conn.close()
        raise ValueError(f"Unknown decision question: {question_id}")
    conn.execute("UPDATE decision_questions SET status='accepted', updated_at=? WHERE id=?", (now, question_id))
    review_id = f"review-{_stable_id(question_id, operator, 'accepted')}"
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_reviews(id, question_id, operator, review_state, selected_option, notes, created_at, metadata_json)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (review_id, question_id, operator, "accepted", selected_option, notes, now, _json_dumps({"status": "accepted"})),
    )
    outcome_id = f"outcome-{_stable_id(question_id, 'accepted')}"
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_outcomes(id, question_id, outcome_state, observed_result, created_at, metadata_json)
        VALUES(?,?,?,?,?,?)
        """,
        (outcome_id, question_id, "accepted", selected_option, now, _json_dumps({"notes": notes})),
    )
    conn.commit()
    conn.close()
    return {"question_id": question_id, "status": "accepted", "selected_option": selected_option, "notes": notes}


def reject_decision(db_path: Path, question_id: str, *, operator: str = "operator", selected_option: str = "", notes: str = "") -> dict[str, Any]:
    now = _utcnow()
    conn = connect(db_path)
    question = conn.execute("SELECT * FROM decision_questions WHERE id=?", (question_id,)).fetchone()
    if question is None:
        conn.close()
        raise ValueError(f"Unknown decision question: {question_id}")
    conn.execute("UPDATE decision_questions SET status='rejected', updated_at=? WHERE id=?", (now, question_id))
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_reviews(id, question_id, operator, review_state, selected_option, notes, created_at, metadata_json)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (f"review-{_stable_id(question_id, operator, 'rejected')}", question_id, operator, "rejected", selected_option, notes, now, _json_dumps({"status": "rejected"})),
    )
    conn.commit()
    conn.close()
    return {"question_id": question_id, "status": "rejected", "selected_option": selected_option, "notes": notes}


def defer_decision(db_path: Path, question_id: str, *, operator: str = "operator", selected_option: str = "", notes: str = "") -> dict[str, Any]:
    now = _utcnow()
    conn = connect(db_path)
    question = conn.execute("SELECT * FROM decision_questions WHERE id=?", (question_id,)).fetchone()
    if question is None:
        conn.close()
        raise ValueError(f"Unknown decision question: {question_id}")
    conn.execute("UPDATE decision_questions SET status='deferred', updated_at=? WHERE id=?", (now, question_id))
    conn.execute(
        """
        INSERT OR REPLACE INTO decision_reviews(id, question_id, operator, review_state, selected_option, notes, created_at, metadata_json)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (f"review-{_stable_id(question_id, operator, 'deferred')}", question_id, operator, "deferred", selected_option, notes, now, _json_dumps({"status": "deferred"})),
    )
    conn.commit()
    conn.close()
    return {"question_id": question_id, "status": "deferred", "selected_option": selected_option, "notes": notes}


def compare_options(db_path: Path, question: str, decision_type: str, options: list[dict[str, Any]], *, project_ids: list[str] | None = None) -> dict[str, Any]:
    return evaluate_decision_question(
        db_path,
        "Option comparison",
        question,
        decision_type,
        project_ids=project_ids,
        scope="portfolio" if project_ids else "project",
        source="deterministic-option-comparison",
        options=options,
    )
