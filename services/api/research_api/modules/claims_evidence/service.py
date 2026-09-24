"""Public service for claims, assumptions and open questions.

Provenance follows the actor: researcher statements are HUMAN_INPUT; AI proposals
are AI_GENERATED with reproducibility metadata, enter as PROPOSED/UNCONFIRMED,
and never become confirmed without a human (Core §19, FR-CLAIM-003).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    AssumptionOrigin,
    AssumptionStatus,
    ClaimType,
    ClaimWorkflowState,
    EvidenceStrength,
    OpenQuestionStatus,
    ProvenanceKind,
    ResearchQuestionType,
    StatementOrigin,
)
from research_api.modules.claims_evidence.models import Assumption, Claim, OpenQuestion
from research_api.modules.claims_evidence.schemas import (
    AssumptionIn,
    AssumptionOut,
    AssumptionReview,
    CaptureIn,
    ClaimIn,
    ClaimOut,
    ClaimUpdate,
    OpenQuestionClose,
    OpenQuestionIn,
    OpenQuestionOut,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.project_workflow import service as projects
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError


def _provenance(auth: Authorized, derived_from: list[UUID] | None = None) -> dict[str, Any]:
    kind = ProvenanceKind.AI_GENERATED if auth.principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    data: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        data["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    if derived_from:
        data["derived_from"] = [str(i) for i in derived_from]
    return data


def _record(
    session: Session,
    auth: Authorized,
    action: str,
    project_id: UUID,
    entity_type: str,
    entity_id: UUID,
    *,
    event: str | None = None,
    previous: dict[str, Any] | None = None,
    new: dict[str, Any] | None = None,
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
            new_state=new,
            reason=reason,
            ai_action=auth.ai_action,
        ),
    )
    if event:
        governance.record_research_event(
            session,
            ResearchEventEntry(
                project_id=project_id,
                event_type=event,
                entity_type=entity_type,
                entity_id=entity_id,
                actor=auth.actor,
                payload=new or {},
            ),
        )


# --- claims ---


def create_claim(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: ClaimIn,
    *,
    ai_action: AIActionRecord | None = None,
    source_note_id: UUID | None = None,
) -> ClaimOut:
    auth = authorized(principal, "claim.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    is_ai = principal.kind is ActorKind.AI
    claim = Claim(
        project_id=project_id,
        statement=data.statement,
        claim_type=data.claim_type.value,
        statement_origin=(StatementOrigin.SYSTEM_INFERRED if is_ai else StatementOrigin.RESEARCHER_STATED).value,
        workflow_state=(ClaimWorkflowState.PROPOSED if is_ai else ClaimWorkflowState.ACTIVE).value,
        # A new claim has no assessed evidence yet; strength comes from evidence, never from assertion.
        epistemic_strength=EvidenceStrength.UNSUBSTANTIATED.value,
        important=data.important,
        provenance=_provenance(auth, [source_note_id] if source_note_id else None),
        source_note_id=source_note_id,
    )
    session.add(claim)
    session.flush()
    _record(
        session,
        auth,
        "claim.create",
        project_id,
        "Claim",
        claim.id,
        event="ClaimCreated",
        new={"claim_type": claim.claim_type, "workflow_state": claim.workflow_state},
    )
    return ClaimOut.model_validate(claim)


def _claim(session: Session, project_id: UUID, claim_id: UUID, *, lock: bool = False) -> Claim:
    claim = session.get(Claim, claim_id, with_for_update=lock)
    if claim is None or claim.project_id != project_id:
        raise NotFoundError("claim not found")
    return claim


def get_claim(session: Session, project_id: UUID, claim_id: UUID) -> ClaimOut:
    return ClaimOut.model_validate(_claim(session, project_id, claim_id))


def list_claims(session: Session, project_id: UUID) -> list[ClaimOut]:
    rows = session.scalars(select(Claim).where(Claim.project_id == project_id).order_by(Claim.created_at))
    return [ClaimOut.model_validate(c) for c in rows]


def update_claim(
    session: Session, principal: Principal, project_id: UUID, claim_id: UUID, data: ClaimUpdate
) -> ClaimOut:
    auth = authorized(principal, "claim.update")
    projects.require_editable_project(session, project_id)
    claim = _claim(session, project_id, claim_id, lock=True)
    changes = data.model_dump(exclude_none=True, exclude={"reason"}, mode="json")
    previous = {k: getattr(claim, k) for k in changes}
    for key, value in changes.items():
        setattr(claim, key, value)
    if changes:
        _record(
            session,
            auth,
            "claim.update",
            project_id,
            "Claim",
            claim.id,
            previous=previous,
            new=changes,
            reason=data.reason,
        )
    session.flush()
    return ClaimOut.model_validate(claim)


def set_claim_strength(session: Session, project_id: UUID, claim_id: UUID, strength: EvidenceStrength) -> None:
    """Called by the evidence assessment flow only; strength follows assessed evidence (Core §34)."""
    _claim(session, project_id, claim_id, lock=True).epistemic_strength = strength.value


# --- assumptions ---


def create_assumption(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: AssumptionIn,
    *,
    ai_action: AIActionRecord | None = None,
    source_note_id: UUID | None = None,
) -> AssumptionOut:
    auth = authorized(principal, "assumption.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    if data.claim_id is not None:
        _claim(session, project_id, data.claim_id)
    is_ai = principal.kind is ActorKind.AI
    assumption = Assumption(
        project_id=project_id,
        statement=data.statement,
        origin=(AssumptionOrigin.SYSTEM_INFERRED.value if is_ai else data.origin),
        criticality=data.criticality.value,
        status=(AssumptionStatus.UNCONFIRMED if is_ai else AssumptionStatus.CONFIRMED).value,
        claim_id=data.claim_id,
        provenance=_provenance(auth, [source_note_id] if source_note_id else None),
        source_note_id=source_note_id,
    )
    session.add(assumption)
    session.flush()
    _record(
        session,
        auth,
        "assumption.create",
        project_id,
        "Assumption",
        assumption.id,
        event="AssumptionRecorded",
        new={"origin": assumption.origin, "criticality": assumption.criticality, "status": assumption.status},
    )
    return AssumptionOut.model_validate(assumption)


def review_assumption(
    session: Session, principal: Principal, project_id: UUID, assumption_id: UUID, data: AssumptionReview
) -> AssumptionOut:
    """Human confirmation, rejection or reclassification of an assumption (FR-CLAIM-003)."""
    auth = authorized(principal, "assumption.review")
    projects.require_editable_project(session, project_id)
    assumption = session.get(Assumption, assumption_id, with_for_update=True)
    if assumption is None or assumption.project_id != project_id:
        raise NotFoundError("assumption not found")
    if assumption.status != AssumptionStatus.UNCONFIRMED.value:
        raise ConflictError(f"assumption is already {assumption.status}")
    previous = {"status": assumption.status, "origin": assumption.origin, "criticality": assumption.criticality}
    if data.status == "RECLASSIFIED":
        if data.reclassify_as is None:
            raise RuleViolationError("reclassification requires the new origin")
        assumption.origin = data.reclassify_as
    assumption.status = data.status
    if data.criticality is not None:
        assumption.criticality = data.criticality.value
    assumption.review_note = data.note
    _record(
        session,
        auth,
        "assumption.review",
        project_id,
        "Assumption",
        assumption.id,
        event="AssumptionReviewed",
        previous=previous,
        new={"status": assumption.status, "origin": assumption.origin, "criticality": assumption.criticality},
        reason=data.note,
    )
    session.flush()
    return AssumptionOut.model_validate(assumption)


def list_assumptions(session: Session, project_id: UUID) -> list[AssumptionOut]:
    rows = session.scalars(
        select(Assumption).where(Assumption.project_id == project_id).order_by(Assumption.created_at)
    )
    return [AssumptionOut.model_validate(a) for a in rows]


# --- open questions ---


def create_question(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: OpenQuestionIn,
    *,
    source_note_id: UUID | None = None,
) -> OpenQuestionOut:
    auth = authorized(principal, "open_question.create")
    projects.require_editable_project(session, project_id)
    question = OpenQuestion(
        project_id=project_id,
        question=data.question,
        question_type=data.question_type.value,
        status=OpenQuestionStatus.OPEN.value,
        source_note_id=source_note_id,
    )
    session.add(question)
    session.flush()
    _record(
        session,
        auth,
        "open_question.create",
        project_id,
        "OpenQuestion",
        question.id,
        event="OpenQuestionRaised",
        new={"question_type": question.question_type},
    )
    return OpenQuestionOut.model_validate(question)


def close_question(
    session: Session, principal: Principal, project_id: UUID, question_id: UUID, data: OpenQuestionClose
) -> OpenQuestionOut:
    """'We do not know' is a valid conclusion (Core §46, §74.22)."""
    auth = authorized(principal, "open_question.close")
    question = session.get(OpenQuestion, question_id, with_for_update=True)
    if question is None or question.project_id != project_id:
        raise NotFoundError("open question not found")
    if question.status != OpenQuestionStatus.OPEN.value:
        raise ConflictError(f"question is already {question.status}")
    question.status = data.status
    question.conclusion = data.conclusion.value
    _record(
        session,
        auth,
        "open_question.close",
        project_id,
        "OpenQuestion",
        question.id,
        event="OpenQuestionClosed",
        previous={"status": OpenQuestionStatus.OPEN.value},
        new={"status": question.status, "conclusion": question.conclusion},
    )
    session.flush()
    return OpenQuestionOut.model_validate(question)


def list_questions(session: Session, project_id: UUID) -> list[OpenQuestionOut]:
    rows = session.scalars(
        select(OpenQuestion).where(OpenQuestion.project_id == project_id).order_by(OpenQuestion.created_at)
    )
    return [OpenQuestionOut.model_validate(q) for q in rows]


# --- capture from scratch notes (FR-CLAIM-005) ---


def capture_note(
    session: Session, principal: Principal, project_id: UUID, note_id: UUID, data: CaptureIn
) -> ClaimOut | AssumptionOut | OpenQuestionOut:
    note = projects.get_note(session, project_id, note_id)
    if note.captured_as is not None:
        raise ConflictError(f"note was already captured as {note.captured_as}")
    result: ClaimOut | AssumptionOut | OpenQuestionOut
    if data.as_ == "claim":
        result = create_claim(
            session,
            principal,
            project_id,
            ClaimIn(statement=note.body, claim_type=data.claim_type or ClaimType.OBSERVATION),
            source_note_id=note.id,
        )
    elif data.as_ == "assumption":
        result = create_assumption(
            session,
            principal,
            project_id,
            AssumptionIn(statement=note.body, criticality=data.criticality),
            source_note_id=note.id,
        )
    else:
        result = create_question(
            session,
            principal,
            project_id,
            OpenQuestionIn(question=note.body, question_type=data.question_type or ResearchQuestionType.EMPIRICAL),
            source_note_id=note.id,
        )
    projects.mark_note_captured(session, principal, project_id, note_id, target=data.as_, entity_id=result.id)
    return result
