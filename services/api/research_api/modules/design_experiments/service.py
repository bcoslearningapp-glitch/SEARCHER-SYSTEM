"""Public service for design requirements and design concepts (PRD §32, Core §47-48, §60).

Requirements come before solutions (FR-DESIGN-001/003): a concept can only be
selected once active requirements exist and the Design Readiness Gate allows it.
Requirement text is never edited; a revision appends a version that supersedes
the previous one. Selection and rejection are explicit human decisions; rejected
concepts stay in history with their reusable mechanisms (FR-DESIGN-005/006).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ApprovalOutcome,
    DesignConceptStatus,
    DesignOrigin,
    DesignRequirementStatus,
    EvidenceTargetType,
    HypothesisLifecycleState,
    MethodologyPathStatus,
    ProvenanceKind,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)
from research_api.modules import targets
from research_api.modules.design_experiments import gate as readiness
from research_api.modules.design_experiments.models import ConceptCoverage, DesignConcept, DesignRequirement
from research_api.modules.design_experiments.schemas import (
    ConceptIn,
    ConceptOut,
    CoverageIn,
    CoverageOut,
    RejectIn,
    RequirementIn,
    RequirementOut,
    RequirementRevision,
    SelectIn,
    SelectOut,
    StatusIn,
    TraceIn,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import (
    AIActionRecord,
    AuditEntry,
    GateEvaluationOut,
    ResearchEventEntry,
)
from research_api.modules.hypothesis_lab import lifecycle
from research_api.modules.hypothesis_lab import service as hypotheses
from research_api.modules.operational_constraints import service as operational
from research_api.modules.project_workflow import service as projects
from research_api.modules.reference_governance import service as reference
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

RS = DesignRequirementStatus
CS = DesignConceptStatus
T = EvidenceTargetType.DESIGN_CONCEPT
REQUIREMENT = "DesignRequirement"
CONCEPT = "DesignConcept"
OPEN = frozenset({CS.PROPOSED.value, CS.UNDER_REVIEW.value})
CURRENT = frozenset({RS.PROPOSED.value, RS.ACTIVE.value})


def _provenance(auth: Authorized) -> dict[str, Any]:
    kind = ProvenanceKind.AI_GENERATED if auth.principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    data: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        data["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    return data


def _record(
    session: Session,
    auth: Authorized,
    action: str,
    event: str,
    project_id: UUID,
    entity_type: str,
    entity_id: UUID,
    payload: dict[str, Any],
    *,
    previous: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=auth.actor,
            previous_state=previous,
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
            entity_type=entity_type,
            entity_id=entity_id,
            actor=auth.actor,
            payload=payload,
        ),
    )


# --- requirements (FR-DESIGN-001..003) ---


def _check_traces(session: Session, project_id: UUID, traces: list[TraceIn]) -> list[dict[str, Any]]:
    """Traces to research entities must point at entities of this project."""
    known = {t.value for t in EvidenceTargetType}
    for trace in traces:
        if trace.entity_id is not None and trace.entity_type in known:
            targets.require(session, project_id, EvidenceTargetType(trace.entity_type), trace.entity_id)
    return [t.model_dump(mode="json", exclude_none=True) for t in traces]


def _requirement(session: Session, project_id: UUID, requirement_id: UUID, *, lock: bool = False) -> DesignRequirement:
    row = session.get(DesignRequirement, requirement_id, with_for_update=lock)
    if row is None or row.project_id != project_id:
        raise NotFoundError("design requirement not found")
    return row


def create_requirement(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: RequirementIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> RequirementOut:
    auth = authorized(principal, "design_requirement.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    # AI-proposed requirements wait for a researcher; they cannot silently define the design space.
    status = RS.PROPOSED if principal.kind is ActorKind.AI else RS.ACTIVE
    row = DesignRequirement(
        project_id=project_id,
        series_id=uuid4(),
        version_number=1,
        statement=data.statement,
        priority=data.priority.value,
        traces=_check_traces(session, project_id, data.traces),
        status=status.value,
        provenance=_provenance(auth),
    )
    session.add(row)
    session.flush()
    _record(
        session,
        auth,
        "design_requirement.create",
        "DesignRequirementCreated",
        project_id,
        REQUIREMENT,
        row.id,
        {"statement": row.statement, "priority": row.priority, "status": row.status},
    )
    return RequirementOut.model_validate(row)


def revise_requirement(
    session: Session, principal: Principal, project_id: UUID, requirement_id: UUID, data: RequirementRevision
) -> RequirementOut:
    auth = authorized(principal, "design_requirement.revise")
    projects.require_editable_project(session, project_id)
    old = _requirement(session, project_id, requirement_id, lock=True)
    if old.status not in CURRENT:
        raise ConflictError(f"only the current version can be revised; this one is {old.status}")
    old.status = RS.SUPERSEDED.value
    session.flush()
    row = DesignRequirement(
        project_id=project_id,
        series_id=old.series_id,
        version_number=old.version_number + 1,
        supersedes_id=old.id,
        statement=data.statement,
        priority=data.priority.value,
        traces=_check_traces(session, project_id, data.traces),
        status=RS.ACTIVE.value,
        change_reason=data.change_reason,
        provenance=_provenance(auth),
    )
    session.add(row)
    session.flush()
    _record(
        session,
        auth,
        "design_requirement.revise",
        "DesignRequirementRevised",
        project_id,
        REQUIREMENT,
        row.id,
        {"statement": row.statement, "priority": row.priority, "version": row.version_number},
        previous={"id": str(old.id), "statement": old.statement, "priority": old.priority},
        reason=data.change_reason,
    )
    return RequirementOut.model_validate(row)


def _set_requirement_status(
    session: Session,
    principal: Principal,
    project_id: UUID,
    requirement_id: UUID,
    action: str,
    allowed_from: frozenset[str],
    target: DesignRequirementStatus,
    reason: str | None,
) -> RequirementOut:
    auth = authorized(principal, action)
    projects.require_editable_project(session, project_id)
    row = _requirement(session, project_id, requirement_id, lock=True)
    if row.status not in allowed_from:
        raise ConflictError(f"cannot move a {row.status} requirement to {target.value}")
    previous = row.status
    row.status = target.value
    session.flush()
    _record(
        session,
        auth,
        action,
        "DesignRequirementConfirmed" if target is RS.ACTIVE else "DesignRequirementWithdrawn",
        project_id,
        REQUIREMENT,
        row.id,
        {"status": row.status},
        previous={"status": previous},
        reason=reason,
    )
    return RequirementOut.model_validate(row)


def confirm_requirement(
    session: Session, principal: Principal, project_id: UUID, requirement_id: UUID, reason: str | None = None
) -> RequirementOut:
    return _set_requirement_status(
        session,
        principal,
        project_id,
        requirement_id,
        "design_requirement.confirm",
        frozenset({RS.PROPOSED.value}),
        RS.ACTIVE,
        reason,
    )


def withdraw_requirement(
    session: Session, principal: Principal, project_id: UUID, requirement_id: UUID, reason: str
) -> RequirementOut:
    return _set_requirement_status(
        session, principal, project_id, requirement_id, "design_requirement.withdraw", CURRENT, RS.WITHDRAWN, reason
    )


def list_requirements(session: Session, project_id: UUID, *, include_history: bool = False) -> list[RequirementOut]:
    query = select(DesignRequirement).where(DesignRequirement.project_id == project_id)
    if not include_history:
        query = query.where(DesignRequirement.status.in_(CURRENT))
    rows = session.scalars(query.order_by(DesignRequirement.created_at, DesignRequirement.version_number))
    return [RequirementOut.model_validate(r) for r in rows]


def requirement_history(session: Session, project_id: UUID, requirement_id: UUID) -> list[RequirementOut]:
    series_id = _requirement(session, project_id, requirement_id).series_id
    rows = session.scalars(
        select(DesignRequirement)
        .where(DesignRequirement.series_id == series_id)
        .order_by(DesignRequirement.version_number)
    )
    return [RequirementOut.model_validate(r) for r in rows]


def _current_requirements(session: Session, project_id: UUID) -> dict[UUID, DesignRequirement]:
    rows = session.scalars(
        select(DesignRequirement).where(
            DesignRequirement.project_id == project_id, DesignRequirement.status.in_(CURRENT)
        )
    )
    return {r.series_id: r for r in rows}


# --- concepts (FR-DESIGN-004..006) ---


def _concept(session: Session, project_id: UUID, concept_id: UUID, *, lock: bool = False) -> DesignConcept:
    row = session.get(DesignConcept, concept_id, with_for_update=lock)
    if row is None or row.project_id != project_id:
        raise NotFoundError("design concept not found")
    return row


def _out(session: Session, concept: DesignConcept) -> ConceptOut:
    current = {r.series_id: r.id for r in _current_requirements(session, concept.project_id).values()}
    rows = session.scalars(select(ConceptCoverage).where(ConceptCoverage.concept_id == concept.id))
    coverage = [
        CoverageOut(
            requirement_id=c.requirement_id,
            requirement_series_id=c.requirement_series_id,
            coverage=c.coverage,
            note=c.note,
            stale=current.get(c.requirement_series_id) not in {None, c.requirement_id},
        )
        for c in rows
    ]
    return ConceptOut(
        id=concept.id,
        project_id=concept.project_id,
        title=concept.title,
        description=concept.description,
        origin=DesignOrigin(concept.origin),
        origin_reference=concept.origin_reference,
        status=CS(concept.status),
        hypothesis_ids=[UUID(i) for i in concept.hypothesis_ids],
        mechanism_ids=[UUID(i) for i in concept.mechanism_ids],
        derived_from_concept_ids=[UUID(i) for i in concept.derived_from_concept_ids],
        coverage=coverage,
        rejection=concept.rejection,
        selection=concept.selection,
        provenance=concept.provenance,
        created_at=concept.created_at,
    )


def create_concept(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: ConceptIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> ConceptOut:
    auth = authorized(principal, "design_concept.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    origin = data.origin
    if principal.kind is ActorKind.AI:
        origin = DesignOrigin.AI  # an AI proposal is never recorded as the researcher's idea
    elif origin is DesignOrigin.AI:
        raise RuleViolationError(
            "AI-originated concepts are recorded by the AI with its provenance; use JOINT_SYNTHESIS"
        )
    for hypothesis_id in data.hypothesis_ids:
        targets.require(session, project_id, EvidenceTargetType.HYPOTHESIS, hypothesis_id)
    for mechanism_id in data.mechanism_ids:
        targets.require(session, project_id, EvidenceTargetType.MECHANISM, mechanism_id)
    for concept_id in data.derived_from_concept_ids:
        _concept(session, project_id, concept_id)
    concept = DesignConcept(
        project_id=project_id,
        title=data.title,
        description=data.description,
        origin=origin.value,
        origin_reference=data.origin_reference,
        status=CS.PROPOSED.value,
        hypothesis_ids=[str(i) for i in data.hypothesis_ids],
        mechanism_ids=[str(i) for i in data.mechanism_ids],
        derived_from_concept_ids=[str(i) for i in data.derived_from_concept_ids],
        provenance=_provenance(auth),
    )
    session.add(concept)
    session.flush()
    _record(
        session,
        auth,
        "design_concept.create",
        "DesignConceptProposed",
        project_id,
        CONCEPT,
        concept.id,
        {"title": concept.title, "origin": concept.origin, "derived_from": concept.derived_from_concept_ids},
    )
    return _out(session, concept)


def get_concept(session: Session, project_id: UUID, concept_id: UUID) -> ConceptOut:
    return _out(session, _concept(session, project_id, concept_id))


def list_concepts(session: Session, project_id: UUID) -> list[ConceptOut]:
    rows = session.scalars(
        select(DesignConcept).where(DesignConcept.project_id == project_id).order_by(DesignConcept.created_at)
    )
    return [_out(session, c) for c in rows]


def set_coverage(
    session: Session, principal: Principal, project_id: UUID, concept_id: UUID, data: CoverageIn
) -> ConceptOut:
    """Record how a concept addresses a requirement; the judgment is tied to the version judged."""
    auth = authorized(principal, "design_concept.coverage")
    projects.require_editable_project(session, project_id)
    concept = _concept(session, project_id, concept_id, lock=True)
    if concept.status not in OPEN:
        raise ConflictError(f"coverage can only be recorded on open concepts; this one is {concept.status}")
    requirement = _requirement(session, project_id, data.requirement_id)
    if requirement.status not in CURRENT:
        raise ConflictError("coverage must be judged against the current requirement version")
    row = session.get(ConceptCoverage, (concept.id, requirement.series_id))
    previous = {"coverage": row.coverage, "requirement_id": str(row.requirement_id)} if row else None
    if row is None:
        row = ConceptCoverage(concept_id=concept.id, requirement_series_id=requirement.series_id)
        session.add(row)
    row.requirement_id = requirement.id
    row.coverage = data.coverage.value
    row.note = data.note
    session.flush()
    _record(
        session,
        auth,
        "design_concept.coverage",
        "DesignCoverageRecorded",
        project_id,
        CONCEPT,
        concept.id,
        {"requirement_id": str(requirement.id), "coverage": row.coverage},
        previous=previous,
    )
    return _out(session, concept)


def set_status(
    session: Session, principal: Principal, project_id: UUID, concept_id: UUID, data: StatusIn
) -> ConceptOut:
    action = "design_concept.review" if data.target == CS.UNDER_REVIEW.value else "design_concept.withdraw"
    auth = authorized(principal, action)
    projects.require_editable_project(session, project_id)
    concept = _concept(session, project_id, concept_id, lock=True)
    allowed = {CS.PROPOSED.value} if data.target == CS.UNDER_REVIEW.value else OPEN
    if concept.status not in allowed:
        raise ConflictError(f"cannot move a {concept.status} concept to {data.target}")
    previous = concept.status
    concept.status = data.target
    session.flush()
    _record(
        session,
        auth,
        action,
        "DesignConceptStatusChanged",
        project_id,
        CONCEPT,
        concept.id,
        {"status": concept.status},
        previous={"status": previous},
        reason=data.reason,
    )
    return _out(session, concept)


# --- Design Readiness Gate (Core §60) ---


def _gate_input(session: Session, project_id: UUID, concept: DesignConcept) -> readiness.DesignGateInput:
    project = projects.get_project(session, project_id)
    current = _current_requirements(session, project_id)
    active = [r for r in current.values() if r.status == RS.ACTIVE.value]
    coverage = {
        c.requirement_series_id: readiness.Coverage(c.coverage, c.requirement_id)
        for c in session.scalars(select(ConceptCoverage).where(ConceptCoverage.concept_id == concept.id))
    }
    eligible = {}
    for hypothesis_id in concept.hypothesis_ids:
        state = hypotheses.get_hypothesis(session, project_id, UUID(hypothesis_id)).lifecycle_state
        eligible[UUID(hypothesis_id)] = lifecycle.reaches(state, HypothesisLifecycleState.ELIGIBLE_FOR_DESIGN)
    return readiness.DesignGateInput(
        concept_status=concept.status,
        risk=RiskLevel(project.risk_level),
        requirements=[readiness.Requirement(r.series_id, r.id, r.priority, r.statement) for r in active],
        unconfirmed_requirements=sum(r.status == RS.PROPOSED.value for r in current.values()),
        coverage=coverage,
        hypotheses_eligible=eligible,
        reference_result=reference.reference_standing(session, project_id, T, concept.id).result,
        execution_ready=operational.operational_standing(session, project_id, T, concept.id).execution_ready,
    )


def evaluate_readiness(session: Session, principal: Principal, project_id: UUID, concept_id: UUID) -> GateEvaluationOut:
    authorized(principal, "quality_gate.evaluate")
    concept = _concept(session, project_id, concept_id)
    data = _gate_input(session, project_id, concept)
    result, findings = readiness.evaluate(data)
    return governance.record_gate_evaluation(
        session,
        gate=QualityGateType.DESIGN_READINESS,
        result=result,
        risk_level=data.risk,
        findings=findings,
        project_id=project_id,
        subject_type=CONCEPT,
        subject_id=concept.id,
    )


def latest_readiness(session: Session, project_id: UUID, concept_id: UUID) -> GateEvaluationOut | None:
    _concept(session, project_id, concept_id)
    return governance.latest_gate_evaluation(
        session, gate=QualityGateType.DESIGN_READINESS, subject_type=CONCEPT, subject_id=concept_id
    )


def select_concept(
    session: Session, principal: Principal, project_id: UUID, concept_id: UUID, data: SelectIn
) -> SelectOut:
    """Human selection (FR-DESIGN-006). Other concepts are left as they are: selection is not a ranking."""
    auth = authorized(principal, "design_concept.select")
    projects.require_editable_project(session, project_id)
    concept = _concept(session, project_id, concept_id, lock=True)
    if concept.status not in OPEN:
        raise ConflictError(f"only open concepts can be selected; this one is {concept.status}")
    gate = evaluate_readiness(session, principal, project_id, concept_id)
    if gate.result is QualityGateResult.BLOCKED:
        raise RuleViolationError(
            "Design Readiness Gate is BLOCKED",
            gate_evaluation_id=str(gate.id),
            findings=[f.model_dump(mode="json") for f in gate.findings if f.severity is QualityGateResult.BLOCKED],
        )
    path = MethodologyPathStatus.COMPLIANT
    if gate.result is QualityGateResult.NEEDS_HUMAN_DECISION:
        if not (data.acknowledge_reservations and data.reason):
            raise RuleViolationError(
                "Design Readiness Gate needs a human decision: acknowledge the reservations and give a reason",
                gate_evaluation_id=str(gate.id),
                findings=[f.model_dump(mode="json") for f in gate.findings],
            )
        path = MethodologyPathStatus.OVERRIDDEN_WITH_REASON
    approval = governance.record_approval(
        session,
        project_id=project_id,
        subject_type=CONCEPT,
        subject_id=concept.id,
        actor=auth.actor,
        outcome=ApprovalOutcome.APPROVED,
        methodology_path=path,
        reason=data.reason,
        gate_evaluation_id=gate.id,
    )
    previous = concept.status
    concept.status = CS.SELECTED.value
    concept.selection = {
        "approval_id": str(approval.id),
        "gate_evaluation_id": str(gate.id),
        "gate_result": gate.result.value,
        "methodology_path": path.value,
    }
    session.flush()
    _record(
        session,
        auth,
        "design_concept.select",
        "DesignConceptSelected",
        project_id,
        CONCEPT,
        concept.id,
        {"status": concept.status, "gate": gate.result.value, "methodology_path": path.value},
        previous={"status": previous},
        reason=data.reason,
    )
    return SelectOut(concept=_out(session, concept), gate=gate, approval=approval)


def reject_concept(
    session: Session, principal: Principal, project_id: UUID, concept_id: UUID, data: RejectIn
) -> ConceptOut:
    """Rejection keeps the concept and names mechanisms worth recombining (FR-DESIGN-005)."""
    auth = authorized(principal, "design_concept.reject")
    projects.require_editable_project(session, project_id)
    concept = _concept(session, project_id, concept_id, lock=True)
    if concept.status not in OPEN | {CS.SELECTED.value}:
        raise ConflictError(f"cannot reject a {concept.status} concept")
    reusable = [str(i) for i in data.reusable_mechanism_ids]
    if not set(reusable) <= set(concept.mechanism_ids):
        raise RuleViolationError("reusable mechanisms must be mechanisms of this concept")
    approval = governance.record_approval(
        session,
        project_id=project_id,
        subject_type=CONCEPT,
        subject_id=concept.id,
        actor=auth.actor,
        outcome=ApprovalOutcome.REJECTED,
        methodology_path=MethodologyPathStatus.COMPLIANT,
        reason=data.reason,
    )
    previous = concept.status
    concept.status = CS.REJECTED.value
    concept.rejection = {
        "ground": data.ground.value,
        "reason": data.reason,
        "reusable_mechanism_ids": reusable,
        "approval_id": str(approval.id),
    }
    session.flush()
    _record(
        session,
        auth,
        "design_concept.reject",
        "DesignConceptRejected",
        project_id,
        CONCEPT,
        concept.id,
        {"status": concept.status, "ground": data.ground.value, "reusable_mechanism_ids": reusable},
        previous={"status": previous},
        reason=data.reason,
    )
    return _out(session, concept)


def _concept_exists(session: Session, project_id: UUID, concept_id: UUID) -> bool:
    concept = session.get(DesignConcept, concept_id)
    return concept is not None and concept.project_id == project_id


targets.register(T, _concept_exists)
