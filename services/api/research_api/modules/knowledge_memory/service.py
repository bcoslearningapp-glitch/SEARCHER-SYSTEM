"""Local knowledge memory (PRD §28-29, §35; Core §44-45, §52, §60).

Knowledge items keep scope, contexts, evidence basis, contrary evidence, confidence,
time sensitivity and provenance. Promotion is one stage at a time, human-only and
gated. Standing can be downgraded, contested, suspended, reinstated or revalidated.
Every change appends a full version. Knowledge is local and never becomes foundational
reference knowledge. Reuse in another project is an explicit, labelled transferability
judgment and never counts as evidence there.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ApprovalOutcome,
    EvidenceStrength,
    EvidenceTargetType,
    KnowledgeLifecycleStage,
    KnowledgeStatus,
    MethodologyPathStatus,
    ProvenanceKind,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
    TemporalProfile,
    TransferabilityState,
)
from research_api.modules import targets
from research_api.modules.design_experiments import experiment_service as experiments
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    AuditEntry,
    ResearchEventEntry,
)
from research_api.modules.knowledge_memory import rules
from research_api.modules.knowledge_memory.models import KnowledgeItem, KnowledgeReuse, KnowledgeVersion
from research_api.modules.knowledge_memory.schemas import (
    BasisIn,
    KnowledgeIn,
    KnowledgeOut,
    KnowledgeRevision,
    PromoteIn,
    PromoteOut,
    ReuseIn,
    ReuseOut,
    StandingIn,
    VersionOut,
)
from research_api.modules.project_workflow import service as projects
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

K = KnowledgeLifecycleStage
S = KnowledgeStatus
ITEM = "KnowledgeItem"
HIGH_IMPACT = frozenset({RiskLevel.L3_HIGH_IMPACT, RiskLevel.L4_CRITICAL})
CONTENT_FIELDS = (
    "statement",
    "scope",
    "contexts",
    "evidence_basis",
    "contrary_evidence",
    "contrary_evidence_searched",
    "confidence",
    "temporal_profile",
    "valid_from",
    "last_verified_at",
    "revalidation_interval_days",
    "source_version",
)
LABELS = {
    TransferabilityState.DIRECTLY_RELEVANT: "Directly relevant, judged by a researcher; still not evidence here.",
    TransferabilityState.PARTIALLY_TRANSFERABLE: "Partially transferable; check the stated differences.",
    TransferabilityState.ANALOGICAL_ONLY: "Analogy only; never direct evidence.",
    TransferabilityState.NOT_TRANSFERABLE: "Not transferable; kept for the record.",
}


def _record(
    session: Session,
    auth: Authorized,
    action: str,
    event: str,
    project_id: UUID,
    entity_id: UUID,
    payload: dict[str, Any],
    *,
    reason: str | None = None,
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action=action,
            entity_type=ITEM,
            entity_id=entity_id,
            actor=auth.actor,
            new_state=payload,
            reason=reason,
            ai_action=auth.ai_action,
        ),
    )
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event,
            entity_type=ITEM,
            entity_id=entity_id,
            actor=auth.actor,
            payload=payload,
        ),
    )


def _check_basis(session: Session, project_id: UUID, items: list[BasisIn]) -> list[dict[str, Any]]:
    known = {t.value for t in EvidenceTargetType}
    for item in items:
        if item.entity_type in known:
            targets.require(session, project_id, EvidenceTargetType(item.entity_type), item.entity_id)
        elif not experiments.record_exists(session, project_id, item.entity_type, item.entity_id):
            raise NotFoundError(f"{item.entity_type} not found in this project", entity_id=str(item.entity_id))
    return [i.model_dump(mode="json", exclude_none=True) for i in items]


def _independent_bases(session: Session, project_id: UUID, basis: list[dict[str, Any]]) -> set[str]:
    """Records from the same experiment are one basis: repetition means separate experiments."""
    keys = set()
    for b in basis:
        experiment = experiments.record_experiment(session, project_id, b["entity_type"], UUID(b["entity_id"]))
        keys.add(f"experiment:{experiment}" if experiment else f"{b['entity_type']}:{b['entity_id']}")
    return keys


def _snapshot(row: KnowledgeItem) -> dict[str, Any]:
    data = {f: getattr(row, f) for f in CONTENT_FIELDS}
    data["valid_from"] = row.valid_from.isoformat() if row.valid_from else None
    data["last_verified_at"] = row.last_verified_at.isoformat() if row.last_verified_at else None
    return data | {"stage": row.stage, "status": row.status}


def _version(
    session: Session,
    row: KnowledgeItem,
    auth: Authorized,
    change: str,
    reason: str,
    gate_evaluation_id: UUID | None = None,
) -> None:
    row.current_version += 1
    session.add(
        KnowledgeVersion(
            knowledge_item_id=row.id,
            version_number=row.current_version,
            snapshot=_snapshot(row),
            change=change,
            reason=reason,
            gate_evaluation_id=gate_evaluation_id,
            actor=auth.actor.model_dump(mode="json", exclude_none=True),
        )
    )
    session.flush()


def _due(row: KnowledgeItem, now: datetime | None = None) -> bool:
    return rules.revalidation_due(
        TemporalProfile(row.temporal_profile), row.last_verified_at, row.revalidation_interval_days, now or utcnow()
    )


def _out(row: KnowledgeItem) -> KnowledgeOut:
    due = _due(row)
    return KnowledgeOut(
        id=row.id,
        project_id=row.project_id,
        current_version=row.current_version,
        statement=row.statement,
        stage=K(row.stage),
        status=S(row.status),
        effective_status=rules.effective_status(S(row.status), due),
        revalidation_due=due,
        scope=row.scope,
        contexts=row.contexts,
        evidence_basis=[BasisIn.model_validate(b) for b in row.evidence_basis],
        contrary_evidence=[BasisIn.model_validate(b) for b in row.contrary_evidence],
        contrary_evidence_searched=row.contrary_evidence_searched,
        confidence=EvidenceStrength(row.confidence),
        temporal_profile=TemporalProfile(row.temporal_profile),
        valid_from=row.valid_from,
        last_verified_at=row.last_verified_at,
        revalidation_interval_days=row.revalidation_interval_days,
        source_version=row.source_version,
        provenance=row.provenance,
        created_at=row.created_at,
    )


def _load(session: Session, project_id: UUID, item_id: UUID, *, lock: bool = False) -> KnowledgeItem:
    row = session.get(KnowledgeItem, item_id, with_for_update=lock)
    if row is None or row.project_id != project_id:
        raise NotFoundError("knowledge item not found")
    return row


def _apply_content(session: Session, project_id: UUID, row: KnowledgeItem, data: KnowledgeIn) -> None:
    row.statement = data.statement
    row.scope = data.scope
    row.contexts = data.contexts
    row.evidence_basis = _check_basis(session, project_id, data.evidence_basis)
    row.contrary_evidence = _check_basis(session, project_id, data.contrary_evidence)
    row.contrary_evidence_searched = data.contrary_evidence_searched
    row.confidence = data.confidence.value
    row.temporal_profile = data.temporal_profile.value
    row.valid_from = data.valid_from
    row.revalidation_interval_days = data.revalidation_interval_days
    row.source_version = data.source_version


def create_item(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: KnowledgeIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> KnowledgeOut:
    """New knowledge always starts as a PROJECT_FINDING (promotion is never automatic)."""
    auth = authorized(principal, "knowledge.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    kind = ProvenanceKind.AI_GENERATED if principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    provenance: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        provenance["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    row = KnowledgeItem(
        project_id=project_id,
        current_version=0,
        stage=K.PROJECT_FINDING.value,
        status=S.ACTIVE.value,
        last_verified_at=utcnow(),
        provenance=provenance,
    )
    _apply_content(session, project_id, row, data)
    session.add(row)
    session.flush()
    _version(session, row, auth, "CREATED", "Created")
    _record(session, auth, "knowledge.create", "KnowledgeRecorded", project_id, row.id, {"stage": row.stage})
    return _out(row)


def get_item(session: Session, project_id: UUID, item_id: UUID) -> KnowledgeOut:
    return _out(_load(session, project_id, item_id))


def list_items(session: Session, project_id: UUID) -> list[KnowledgeOut]:
    rows = session.scalars(
        select(KnowledgeItem).where(KnowledgeItem.project_id == project_id).order_by(KnowledgeItem.created_at)
    )
    return [_out(r) for r in rows]


def list_versions(session: Session, project_id: UUID, item_id: UUID) -> list[VersionOut]:
    _load(session, project_id, item_id)
    rows = session.scalars(
        select(KnowledgeVersion)
        .where(KnowledgeVersion.knowledge_item_id == item_id)
        .order_by(KnowledgeVersion.version_number)
    )
    return [
        VersionOut(
            version_number=v.version_number,
            change=v.change,
            reason=v.reason,
            stage=K(v.snapshot["stage"]),
            status=S(v.snapshot["status"]),
            gate_evaluation_id=v.gate_evaluation_id,
            actor=Actor.model_validate(v.actor),
            created_at=v.created_at,
        )
        for v in rows
    ]


def revise_item(
    session: Session, principal: Principal, project_id: UUID, item_id: UUID, data: KnowledgeRevision
) -> KnowledgeOut:
    auth = authorized(principal, "knowledge.revise")
    projects.require_editable_project(session, project_id)
    row = _load(session, project_id, item_id, lock=True)
    _apply_content(session, project_id, row, data)
    _version(session, row, auth, "REVISED", data.reason)
    _record(session, auth, "knowledge.revise", "KnowledgeRevised", project_id, row.id, {"version": row.current_version})
    return _out(row)


def promote(session: Session, principal: Principal, project_id: UUID, item_id: UUID, data: PromoteIn) -> PromoteOut:
    """Human promotion, one stage at a time, through the Knowledge Promotion Gate."""
    auth = authorized(principal, "knowledge.promote")
    project = projects.require_editable_project(session, project_id)
    row = _load(session, project_id, item_id, lock=True)
    if rules.next_stage(K(row.stage)) is not data.target:
        raise ConflictError(f"promotion goes one stage at a time; {row.stage} cannot become {data.target.value}")
    bases = _independent_bases(session, project_id, row.evidence_basis)
    result, findings = rules.evaluate(
        rules.PromotionInput(
            target=data.target,
            status=S(row.status),
            revalidation_due=_due(row),
            basis_entities=len(bases),
            contexts=len(set(row.contexts)),
            scope=row.scope,
            contrary_searched=row.contrary_evidence_searched,
            contrary_count=len(row.contrary_evidence),
            confidence=EvidenceStrength(row.confidence),
            temporal_profile=TemporalProfile(row.temporal_profile),
        )
    )
    gate = governance.record_gate_evaluation(
        session,
        gate=QualityGateType.KNOWLEDGE_PROMOTION,
        result=result,
        risk_level=RiskLevel(project.risk_level),
        findings=findings,
        project_id=project_id,
        subject_type=ITEM,
        subject_id=row.id,
    )
    if result is QualityGateResult.BLOCKED:
        raise RuleViolationError(
            "Knowledge Promotion Gate is BLOCKED",
            gate_evaluation_id=str(gate.id),
            findings=[f.model_dump(mode="json") for f in findings if f.severity is QualityGateResult.BLOCKED],
        )
    path = MethodologyPathStatus.COMPLIANT
    if result is QualityGateResult.NEEDS_HUMAN_DECISION:
        if not (data.acknowledge_reservations and data.reason):
            raise RuleViolationError(
                "Knowledge Promotion Gate needs a human decision: acknowledge the reservations and give a reason",
                gate_evaluation_id=str(gate.id),
                findings=[f.model_dump(mode="json") for f in findings],
            )
        path = MethodologyPathStatus.OVERRIDDEN_WITH_REASON
    governance.record_approval(
        session,
        project_id=project_id,
        subject_type=ITEM,
        subject_id=row.id,
        actor=auth.actor,
        outcome=ApprovalOutcome.APPROVED,
        methodology_path=path,
        reason=data.reason,
        gate_evaluation_id=gate.id,
    )
    previous = row.stage
    row.stage = data.target.value
    _version(session, row, auth, "PROMOTED", data.reason or f"Promoted to {row.stage}", gate.id)
    _record(
        session,
        auth,
        "knowledge.promote",
        "KnowledgePromoted",
        project_id,
        row.id,
        {"from": previous, "to": row.stage, "gate": result.value, "path": path.value},
        reason=data.reason,
    )
    return PromoteOut(item=_out(row), gate=gate)


def change_standing(
    session: Session, principal: Principal, project_id: UUID, item_id: UUID, data: StandingIn
) -> KnowledgeOut:
    """Downgrade, contest, suspend, reinstate or revalidate (FR-KNOW-004, FR-TIME-002)."""
    auth = authorized(principal, "knowledge.standing")
    projects.require_editable_project(session, project_id)
    row = _load(session, project_id, item_id, lock=True)
    current = S(row.status)
    if data.action == "DOWNGRADE":
        if data.target_stage is None or not rules.is_lower(data.target_stage, K(row.stage)):
            raise RuleViolationError("a downgrade names a lower lifecycle stage")
        row.stage = data.target_stage.value
        row.status = S.DOWNGRADED.value
    elif data.action == "CONTEST":
        row.status = S.CONTESTED.value
    elif data.action == "SUSPEND":
        row.status = S.SUSPENDED.value
    elif data.action == "REINSTATE":
        if current is S.ACTIVE:
            raise ConflictError("the knowledge is already active")
        row.status = S.ACTIVE.value
    else:  # REVALIDATE
        if current in {S.SUSPENDED, S.CONTESTED}:
            raise ConflictError(f"reinstate {current.value} knowledge before revalidating it")
        row.last_verified_at = utcnow()
        row.status = S.ACTIVE.value
        if data.source_version:
            row.source_version = data.source_version
    _version(session, row, auth, data.action, data.reason)
    _record(
        session,
        auth,
        "knowledge.standing",
        "KnowledgeStandingChanged",
        project_id,
        row.id,
        {"action": data.action, "stage": row.stage, "status": row.status, "previous_status": current.value},
        reason=data.reason,
    )
    return _out(row)


# --- cross-project reuse (FR-TRANS-001..003, FR-TIME-003) ---


def _reuse_out(session: Session, reuse: KnowledgeReuse) -> ReuseOut:
    item = session.get(KnowledgeItem, reuse.knowledge_item_id)
    assert item is not None  # noqa: S101 - FK guarantees it
    out = _out(item)
    transferability = TransferabilityState(reuse.transferability)
    return ReuseOut(
        id=reuse.id,
        knowledge_item_id=reuse.knowledge_item_id,
        knowledge_version=reuse.knowledge_version,
        target_project_id=reuse.target_project_id,
        transferability=transferability,
        rationale=reuse.rationale,
        differences=reuse.differences,
        assessed_by=Actor.model_validate(reuse.assessed_by),
        created_at=reuse.created_at,
        statement=out.statement,
        source_project_id=out.project_id,
        stage=out.stage,
        effective_status=out.effective_status,
        label=LABELS[transferability],
    )


def reuse_item(session: Session, principal: Principal, project_id: UUID, item_id: UUID, data: ReuseIn) -> ReuseOut:
    """Similarity is never automatic transferability: a researcher judges and labels each reuse."""
    auth = authorized(principal, "knowledge.reuse")
    row = _load(session, project_id, item_id)
    if data.target_project_id == project_id:
        raise RuleViolationError("reuse is for another project")
    target = projects.require_editable_project(session, data.target_project_id)
    status = rules.effective_status(S(row.status), _due(row))
    if status is S.SUSPENDED:
        raise RuleViolationError("suspended knowledge cannot be reused")
    if status is S.REVALIDATION_REQUIRED and RiskLevel(target.risk_level) in HIGH_IMPACT:
        raise RuleViolationError("revalidate this knowledge before reusing it in a high-impact project (FR-TIME-003)")
    reuse = KnowledgeReuse(
        knowledge_item_id=row.id,
        knowledge_version=row.current_version,
        target_project_id=target.id,
        transferability=data.transferability.value,
        rationale=data.rationale,
        differences=data.differences,
        assessed_by=auth.actor.model_dump(mode="json", exclude_none=True),
    )
    session.add(reuse)
    session.flush()
    payload = {"reuse_id": str(reuse.id), "transferability": reuse.transferability, "to": str(target.id)}
    _record(session, auth, "knowledge.reuse", "KnowledgeReused", project_id, row.id, payload)
    _record(session, auth, "knowledge.reuse", "KnowledgeImported", target.id, row.id, payload)
    return _reuse_out(session, reuse)


def reused_in(session: Session, project_id: UUID) -> list[ReuseOut]:
    rows = session.scalars(
        select(KnowledgeReuse).where(KnowledgeReuse.target_project_id == project_id).order_by(KnowledgeReuse.created_at)
    )
    return [_reuse_out(session, r) for r in rows]


def revalidation_due(session: Session, project_id: UUID) -> list[KnowledgeOut]:
    """Knowledge of, or reused in, this project whose revalidation policy has lapsed."""
    own = [k for k in list_items(session, project_id) if k.revalidation_due]
    reused_ids = {r.knowledge_item_id for r in reused_in(session, project_id)}
    borrowed = [_out(r) for r in (session.get(KnowledgeItem, i) for i in reused_ids) if r is not None and _due(r)]
    return own + [b for b in borrowed if b.id not in {o.id for o in own}]
