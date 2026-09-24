"""Public audit service. Every material state change goes through here (FR-EVENT-001)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import (
    CONTRACT_SCHEMA_VERSION,
    ActorKind,
    ActorRole,
    ApprovalOutcome,
    DecisionStatus,
    MethodologyPathStatus,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.models import (
    ApprovalRecord,
    AuditEventRecord,
    DecisionRecord,
    QualityGateEvaluationRecord,
    ResearchEventRecord,
)
from research_api.modules.governance_audit.policy import PolicyDecision, PolicyViolationError
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    AIRecommendation,
    ApprovalOut,
    AuditEntry,
    AuditEventOut,
    DecisionCreate,
    DecisionOut,
    DecisionResolve,
    GateEvaluationOut,
    GateFinding,
    ResearchEventEntry,
    VersionContext,
)
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError


def _version_columns() -> dict[str, str]:
    settings = get_settings()
    return {
        "core_schema_version": CONTRACT_SCHEMA_VERSION,
        "methodology_version": settings.methodology_version,
        "constitution_version": settings.constitution_version,
    }


def _actor_columns(actor: Actor) -> dict[str, str | None]:
    return {
        "actor_kind": actor.kind.value,
        "actor_id": actor.id,
        "actor_role": actor.role.value if actor.role else None,
    }


def record_audit(session: Session, entry: AuditEntry) -> AuditEventRecord:
    """Append an audit event in the caller's transaction.

    The caller owns the transaction so the audit record commits or rolls back
    atomically with the state change it describes (NFR-REL-003).
    """
    record = AuditEventRecord(
        project_id=entry.project_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        action=entry.action,
        previous_state=entry.previous_state,
        new_state=entry.new_state,
        reason=entry.reason,
        ai_action=entry.ai_action.model_dump(mode="json") if entry.ai_action else None,
        **_actor_columns(entry.actor),
        **_version_columns(),
    )
    session.add(record)
    session.flush()
    return record


def record_research_event(session: Session, entry: ResearchEventEntry) -> ResearchEventRecord:
    """Append a research event in the caller's transaction (Core §56)."""
    record = ResearchEventRecord(
        project_id=entry.project_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        event_type=entry.event_type,
        payload=entry.payload,
        **_actor_columns(entry.actor),
        **_version_columns(),
    )
    session.add(record)
    session.flush()
    return record


def to_out(record: AuditEventRecord) -> AuditEventOut:
    return AuditEventOut(
        id=record.id,
        project_id=record.project_id,
        action=record.action,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        occurred_at=record.occurred_at,
        actor=Actor.model_validate({"kind": record.actor_kind, "id": record.actor_id, "role": record.actor_role}),
        versions=VersionContext(
            core_schema_version=record.core_schema_version,
            methodology_version=record.methodology_version,
            constitution_version=record.constitution_version,
        ),
        previous_state=record.previous_state,
        new_state=record.new_state,
        reason=record.reason,
        ai_action=AIActionRecord.model_validate(record.ai_action) if record.ai_action else None,
    )


def list_audit_events(session: Session, *, project_id: UUID | None = None, limit: int = 100) -> list[AuditEventOut]:
    query = select(AuditEventRecord).order_by(AuditEventRecord.occurred_at.desc()).limit(limit)
    if project_id is not None:
        query = query.where(AuditEventRecord.project_id == project_id)
    return [to_out(r) for r in session.scalars(query)]


# --- Approvals (FR-APPROVAL-001) ---


def record_approval(
    session: Session,
    *,
    project_id: UUID,
    subject_type: str,
    subject_id: UUID,
    actor: Actor,
    outcome: ApprovalOutcome,
    methodology_path: MethodologyPathStatus,
    reason: str | None = None,
    gate_evaluation_id: UUID | None = None,
) -> ApprovalOut:
    """Persist an explicit approval. Callers must have authorized a human-only approval action."""
    if actor.kind is not ActorKind.HUMAN:
        raise ValueError("approvals are human-only (Core §58)")
    record = ApprovalRecord(
        project_id=project_id,
        subject_type=subject_type,
        subject_id=subject_id,
        outcome=outcome.value,
        approver_kind=actor.kind.value,
        approver_id=actor.id,
        approver_role=actor.role.value if actor.role else None,
        reason=reason,
        methodology_path=methodology_path.value,
        gate_evaluation_id=gate_evaluation_id,
    )
    session.add(record)
    session.flush()
    return approval_out(record)


def approval_out(record: ApprovalRecord) -> ApprovalOut:
    return ApprovalOut(
        id=record.id,
        project_id=record.project_id,
        subject_type=record.subject_type,
        subject_id=record.subject_id,
        outcome=ApprovalOutcome(record.outcome),
        approved_by=Actor.model_validate(
            {"kind": record.approver_kind, "id": record.approver_id, "role": record.approver_role}
        ),
        reason=record.reason,
        methodology_path=MethodologyPathStatus(record.methodology_path),
        gate_evaluation_id=record.gate_evaluation_id,
        created_at=record.created_at,
    )


def get_approval(session: Session, approval_id: UUID) -> ApprovalOut | None:
    record = session.get(ApprovalRecord, approval_id)
    return approval_out(record) if record else None


# --- Quality gates (Core §60) ---


def record_gate_evaluation(
    session: Session,
    *,
    gate: QualityGateType,
    result: QualityGateResult,
    risk_level: RiskLevel,
    findings: list[GateFinding],
    project_id: UUID | None = None,
    subject_type: str | None = None,
    subject_id: UUID | None = None,
) -> GateEvaluationOut:
    record = QualityGateEvaluationRecord(
        project_id=project_id,
        gate=gate.value,
        subject_type=subject_type,
        subject_id=subject_id,
        result=result.value,
        risk_level=risk_level.value,
        findings=[f.model_dump(mode="json") for f in findings],
        methodology_version=get_settings().methodology_version,
    )
    session.add(record)
    session.flush()
    return gate_out(record)


def gate_out(record: QualityGateEvaluationRecord) -> GateEvaluationOut:
    return GateEvaluationOut(
        id=record.id,
        project_id=record.project_id,
        gate=QualityGateType(record.gate),
        subject_type=record.subject_type,
        subject_id=record.subject_id,
        result=QualityGateResult(record.result),
        risk_level=RiskLevel(record.risk_level),
        findings=[GateFinding.model_validate(f) for f in record.findings],
        evaluated_at=record.evaluated_at,
        methodology_version=record.methodology_version,
    )


def latest_gate_evaluation(
    session: Session, *, gate: QualityGateType, subject_type: str, subject_id: UUID
) -> GateEvaluationOut | None:
    record = session.scalars(
        select(QualityGateEvaluationRecord)
        .where(
            QualityGateEvaluationRecord.gate == gate.value,
            QualityGateEvaluationRecord.subject_type == subject_type,
            QualityGateEvaluationRecord.subject_id == subject_id,
        )
        .order_by(QualityGateEvaluationRecord.evaluated_at.desc())
        .limit(1)
    ).first()
    return gate_out(record) if record else None


# --- Decisions (FR-DEC-001/002, FR-DEGRADED-001..004) ---


def decision_out(record: DecisionRecord) -> DecisionOut:
    decided_by = (
        Actor.model_validate(
            {"kind": record.decided_by_kind, "id": record.decided_by_id, "role": record.decided_by_role}
        )
        if record.decided_by_kind
        else None
    )
    return DecisionOut(
        id=record.id,
        project_id=record.project_id,
        question=record.question,
        options=record.options,
        ai_recommendation=AIRecommendation.model_validate(record.ai_recommendation)
        if record.ai_recommendation
        else None,
        rationale=record.rationale,
        required_role=ActorRole(record.required_role),
        blocking=record.blocking,
        status=DecisionStatus(record.status),
        subject_type=record.subject_type,
        subject_id=record.subject_id,
        final_decision=record.final_decision,
        human_justification=record.human_justification,
        methodology_path=MethodologyPathStatus(record.methodology_path) if record.methodology_path else None,
        decided_by=decided_by,
        decided_at=record.decided_at,
        created_at=record.created_at,
    )


def create_decision(session: Session, principal: Principal, project_id: UUID, data: DecisionCreate) -> DecisionOut:
    auth = authorized(principal, "decision.create")
    record = DecisionRecord(
        project_id=project_id,
        question=data.question,
        options=data.options,
        rationale=data.rationale,
        required_role=data.required_role.value,
        blocking=data.blocking,
        status=DecisionStatus.OPEN.value,
        subject_type=data.subject_type,
        subject_id=data.subject_id,
        created_by_kind=auth.actor.kind.value,
        created_by_id=auth.actor.id,
    )
    session.add(record)
    session.flush()
    record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="decision.create",
            entity_type="Decision",
            entity_id=record.id,
            actor=auth.actor,
            new_state={"status": record.status, "question": record.question, "blocking": record.blocking},
            ai_action=auth.ai_action,
        ),
    )
    return decision_out(record)


def _open_decision(session: Session, project_id: UUID, decision_id: UUID) -> DecisionRecord:
    record = session.get(DecisionRecord, decision_id, with_for_update=True)
    if record is None or record.project_id != project_id:
        raise NotFoundError("decision not found")
    if record.status != DecisionStatus.OPEN.value:
        raise ConflictError(f"decision is already {record.status}; decisions are not rewritten")
    return record


def recommend_decision(
    session: Session,
    principal: Principal,
    project_id: UUID,
    decision_id: UUID,
    recommendation: AIRecommendation,
) -> DecisionOut:
    """Attach an AI recommendation. It never resolves the decision (FR-DEC-002)."""
    auth = authorized(principal, "decision.recommend", ai_action=recommendation.ai_action)
    record = _open_decision(session, project_id, decision_id)
    if recommendation.option not in record.options:
        raise RuleViolationError("recommended option is not one of the decision options")
    record.ai_recommendation = recommendation.model_dump(mode="json")
    record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="decision.recommend",
            entity_type="Decision",
            entity_id=record.id,
            actor=auth.actor,
            new_state={"ai_recommendation": record.ai_recommendation["option"]},
            ai_action=auth.ai_action,
        ),
    )
    return decision_out(record)


def resolve_decision(
    session: Session, principal: Principal, project_id: UUID, decision_id: UUID, data: DecisionResolve
) -> DecisionOut:
    authorized(principal, "decision.resolve")
    record = _open_decision(session, project_id, decision_id)
    required = ActorRole(record.required_role)
    if required not in principal.roles:
        raise PolicyViolationError(
            PolicyDecision("decision.resolve", False, False, False, None, f"decision requires role {required}")
        )
    if data.final_decision not in record.options:
        raise RuleViolationError("final decision must be one of the recorded options")
    path = MethodologyPathStatus.COMPLIANT
    justification = data.human_justification
    if data.incomplete_evidence:
        if not data.unverified or not data.risks or not data.later_review:
            raise RuleViolationError(
                "Degraded Decision Mode requires listing what is unverified, the risks, and the later review"
            )
        path = MethodologyPathStatus.DECISION_UNDER_INCOMPLETE_EVIDENCE
    actor = principal.as_actor(required)
    record.status = DecisionStatus.DECIDED.value
    record.final_decision = data.final_decision
    record.human_justification = justification
    record.methodology_path = path.value
    record.decided_by_kind = actor.kind.value
    record.decided_by_id = actor.id
    record.decided_by_role = actor.role.value if actor.role else None
    record.decided_at = utcnow()
    degraded = (
        {"unverified": data.unverified, "risks": data.risks, "later_review": data.later_review}
        if data.incomplete_evidence
        else None
    )
    record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="decision.resolve",
            entity_type="Decision",
            entity_id=record.id,
            actor=actor,
            previous_state={"status": DecisionStatus.OPEN.value},
            new_state={"status": record.status, "final_decision": data.final_decision, "degraded": degraded},
            reason=justification,
        ),
    )
    record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type="DecisionMade",
            entity_type="Decision",
            entity_id=record.id,
            actor=actor,
            payload={"methodology_path": path.value, "degraded": degraded},
        ),
    )
    return decision_out(record)


def withdraw_decision(
    session: Session, principal: Principal, project_id: UUID, decision_id: UUID, reason: str
) -> DecisionOut:
    auth = authorized(principal, "decision.withdraw")
    record = _open_decision(session, project_id, decision_id)
    record.status = DecisionStatus.WITHDRAWN.value
    record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="decision.withdraw",
            entity_type="Decision",
            entity_id=record.id,
            actor=auth.actor,
            previous_state={"status": DecisionStatus.OPEN.value},
            new_state={"status": record.status},
            reason=reason,
        ),
    )
    return decision_out(record)


def get_decision(session: Session, project_id: UUID, decision_id: UUID) -> DecisionOut:
    record = session.get(DecisionRecord, decision_id)
    if record is None or record.project_id != project_id:
        raise NotFoundError("decision not found")
    return decision_out(record)


def list_decisions(session: Session, project_id: UUID, *, status: DecisionStatus | None = None) -> list[DecisionOut]:
    query = select(DecisionRecord).where(DecisionRecord.project_id == project_id)
    if status is not None:
        query = query.where(DecisionRecord.status == status.value)
    return [decision_out(r) for r in session.scalars(query.order_by(DecisionRecord.created_at))]
