"""Knowledge lifecycle, temporal validity and the Knowledge Promotion Gate (Core §45, §52, §60). Pure."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from research_api.contracts.enums import EvidenceStrength, KnowledgeStatus, TemporalProfile
from research_api.contracts.enums import KnowledgeLifecycleStage as K
from research_api.contracts.enums import QualityGateResult as G
from research_api.modules.governance_audit.schemas import GateFinding

STAGES = list(K)
RULE_STAGES = frozenset({K.CANDIDATE_OPERATING_RULE, K.OPERATING_RULE})
TIME_SENSITIVE = frozenset({TemporalProfile.DYNAMIC, TemporalProfile.HIGHLY_VOLATILE})
WEAK = frozenset({EvidenceStrength.UNSUBSTANTIATED, EvidenceStrength.WEAK})


def next_stage(stage: K) -> K | None:
    index = STAGES.index(stage)
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def is_lower(target: K, current: K) -> bool:
    return STAGES.index(target) < STAGES.index(current)


def revalidation_due(
    profile: TemporalProfile, last_verified_at: datetime | None, interval_days: int | None, now: datetime
) -> bool:
    """Knowledge past its revalidation policy must be revalidated before high-impact reuse (FR-TIME-003)."""
    if interval_days is None:
        return profile in TIME_SENSITIVE and last_verified_at is None
    if last_verified_at is None:
        return True
    return last_verified_at + timedelta(days=interval_days) < now


def effective_status(status: KnowledgeStatus, due: bool) -> KnowledgeStatus:
    if due and status is KnowledgeStatus.ACTIVE:
        return KnowledgeStatus.REVALIDATION_REQUIRED
    return status


@dataclass(frozen=True)
class PromotionInput:
    target: K
    status: KnowledgeStatus
    revalidation_due: bool
    basis_entities: int
    contexts: int
    scope: str
    contrary_searched: bool
    contrary_count: int
    confidence: EvidenceStrength
    temporal_profile: TemporalProfile


Add = Callable[[str, G, str], None]


def _stage_requirements(data: PromotionInput, add: Add) -> None:
    if data.basis_entities < 1:
        add("basis.missing", G.BLOCKED, "Knowledge needs at least one evidence basis.")
    if STAGES.index(data.target) >= STAGES.index(K.REPEATED_LOCAL_RESULT) and data.basis_entities < 2:
        add("repetition.insufficient", G.BLOCKED, "A repeated result needs at least two independent bases.")
    if STAGES.index(data.target) >= STAGES.index(K.ACCUMULATED_LOCAL_KNOWLEDGE) and data.contexts < 2:
        add(
            "contexts.single",
            G.NEEDS_HUMAN_DECISION,
            "Accumulated knowledge normally spans more than one context; this has one.",
        )


def _rule_requirements(data: PromotionInput, add: Add) -> None:
    if not data.scope.strip():
        add("scope.missing", G.BLOCKED, "An operating rule must state the scope it applies to.")
    if not data.contrary_searched:
        add("contrary.not_searched", G.BLOCKED, "Contrary evidence must be searched before an operating rule.")
    if data.contrary_count:
        add("contrary.present", G.NEEDS_HUMAN_DECISION, f"{data.contrary_count} contrary item(s) are recorded.")
    if data.confidence in WEAK:
        add("confidence.weak", G.BLOCKED, f"Confidence {data.confidence.value} cannot support an operating rule.")
    if data.temporal_profile is TemporalProfile.HIGHLY_VOLATILE:
        add("temporal.volatile", G.NEEDS_HUMAN_DECISION, "Highly volatile knowledge is being made a rule.")


def evaluate(data: PromotionInput) -> tuple[G, list[GateFinding]]:
    findings: list[GateFinding] = []

    def add(code: str, severity: G, message: str) -> None:
        findings.append(GateFinding(code=code, severity=severity, message=message))

    if data.status is not KnowledgeStatus.ACTIVE:
        add("status.not_active", G.BLOCKED, f"Knowledge that is {data.status.value} cannot be promoted.")
    if data.revalidation_due:
        add("temporal.revalidation_required", G.BLOCKED, "Revalidate this knowledge before promoting it.")
    _stage_requirements(data, add)
    if data.target in RULE_STAGES:
        _rule_requirements(data, add)
    elif data.contrary_count:
        add("contrary.present", G.PASS_WITH_RESERVATIONS, f"{data.contrary_count} contrary item(s) are recorded.")
    elif not data.contrary_searched:
        add("contrary.not_searched", G.PASS_WITH_RESERVATIONS, "Contrary evidence has not been searched yet.")
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
