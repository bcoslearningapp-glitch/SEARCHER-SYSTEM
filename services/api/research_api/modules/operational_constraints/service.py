"""Public service for operational constraints (Core §5, PRD §5.3, Scenario F).

Operational constraints describe whether execution is allowed *now*. They never
change a reference judgment, and a reference judgment never changes them.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import EvidenceTargetType, OperationalConstraintState, QualityGateResult
from research_api.modules import targets
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AuditEntry, ResearchEventEntry
from research_api.modules.operational_constraints.models import OperationalConstraint
from research_api.modules.operational_constraints.schemas import (
    ConstraintIn,
    ConstraintOut,
    OperationalStanding,
    ResolveIn,
    TargetStanding,
)
from research_api.modules.project_workflow import service as projects
from research_api.modules.reference_governance import service as reference
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError

S = OperationalConstraintState
EXECUTION_BLOCKING = frozenset({S.BLOCKS_CURRENT_EXECUTION, S.REQUIRES_EXTERNAL_APPROVAL})


def add_constraint(session: Session, principal: Principal, project_id: UUID, data: ConstraintIn) -> ConstraintOut:
    auth = authorized(principal, "operational.constraint_add")
    projects.require_editable_project(session, project_id)
    targets.require(session, project_id, data.target_type, data.target_id)
    constraint = OperationalConstraint(project_id=project_id, **data.model_dump(mode="json"))
    session.add(constraint)
    session.flush()
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="operational.constraint_add",
            entity_type="OperationalConstraint",
            entity_id=constraint.id,
            actor=auth.actor,
            new_state={"kind": constraint.kind, "state": constraint.state},
            ai_action=auth.ai_action,
        ),
    )
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type="OperationalConstraintRecorded",
            entity_type="OperationalConstraint",
            entity_id=constraint.id,
            actor=auth.actor,
            payload={
                "state": constraint.state,
                "target_type": constraint.target_type,
                "target_id": str(constraint.target_id),
            },
        ),
    )
    return ConstraintOut.model_validate(constraint)


def resolve_constraint(
    session: Session, principal: Principal, project_id: UUID, constraint_id: UUID, data: ResolveIn
) -> ConstraintOut:
    auth = authorized(principal, "operational.constraint_resolve")
    constraint = session.get(OperationalConstraint, constraint_id, with_for_update=True)
    if constraint is None or constraint.project_id != project_id:
        raise NotFoundError("constraint not found")
    if constraint.resolved_at is not None:
        raise ConflictError("constraint is already resolved")
    constraint.resolved_at = utcnow()
    constraint.resolution = data.resolution
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="operational.constraint_resolve",
            entity_type="OperationalConstraint",
            entity_id=constraint.id,
            actor=auth.actor,
            new_state={"resolved": True},
            reason=data.resolution,
        ),
    )
    session.flush()
    return ConstraintOut.model_validate(constraint)


def operational_standing(
    session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID
) -> OperationalStanding:
    rows = [
        ConstraintOut.model_validate(c)
        for c in session.scalars(
            select(OperationalConstraint)
            .where(
                OperationalConstraint.project_id == project_id,
                OperationalConstraint.target_type == target_type.value,
                OperationalConstraint.target_id == target_id,
            )
            .order_by(OperationalConstraint.created_at)
        )
    ]
    blocking = [c for c in rows if c.resolved_at is None and c.state in EXECUTION_BLOCKING]
    return OperationalStanding(constraints=rows, execution_ready=not blocking, blocking=blocking)


def target_standing(
    session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID
) -> TargetStanding:
    targets.require(session, project_id, target_type, target_id)
    ref = reference.reference_standing(session, project_id, target_type, target_id)
    ops = operational_standing(session, project_id, target_type, target_id)
    reference_ok = ref.result in {QualityGateResult.PASS, QualityGateResult.PASS_WITH_RESERVATIONS}
    if reference_ok and not ops.execution_ready:
        summary = (
            "Reference-consistent as judged, but current operational rules prevent execution now; "
            "research can continue and a lawful alternative or external change is required."
        )
    elif not reference_ok and ops.execution_ready:
        summary = (
            "Operationally permitted, but the reference review does not currently allow adoption; "
            "operational permission does not make it acceptable."
        )
    elif not reference_ok:
        summary = "Not adoptable under the reference review, and execution is also operationally constrained."
    else:
        summary = "No reference or operational obstacle recorded."
    return TargetStanding(target_type=target_type, target_id=target_id, reference=ref, operational=ops, summary=summary)
