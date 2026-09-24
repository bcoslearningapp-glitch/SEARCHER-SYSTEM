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
    ActorRole,
    AssumptionOrigin,
    AssumptionStatus,
    ClaimType,
    ClaimWorkflowState,
    EvidenceRole,
    EvidenceStatus,
    EvidenceStrength,
    EvidenceTargetType,
    LineageRelation,
    OpenQuestionStatus,
    ProvenanceKind,
    ResearchOutcomeKind,
    ResearchQuestionType,
    ResearchTrack,
    StatementOrigin,
)
from research_api.modules import targets
from research_api.modules.claims_evidence import aggregation
from research_api.modules.claims_evidence.models import (
    Assumption,
    Claim,
    Evidence,
    OpenQuestion,
    ResearchTrackRun,
    SourceLineage,
)
from research_api.modules.claims_evidence.schemas import (
    AssessmentIn,
    AssumptionIn,
    AssumptionOut,
    AssumptionReview,
    CaptureIn,
    ClaimIn,
    ClaimOut,
    ClaimUpdate,
    EvidenceIn,
    EvidenceMap,
    EvidenceOut,
    LineageIn,
    LineageOut,
    OpenQuestionClose,
    OpenQuestionIn,
    OpenQuestionOut,
    TrackRunIn,
    TrackRunOut,
    TrackStatus,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal, system_principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.project_workflow import service as projects
from research_api.modules.sources_library import service as sources
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


# --- evidence (Core §32-36, FR-EVID-001..006, FR-LINEAGE-001..004) ---

COMPLETED_OUTCOMES = frozenset({ResearchOutcomeKind.RESULTS_FOUND, ResearchOutcomeKind.NO_RELEVANT_EVIDENCE_FOUND})
COUNTER_TRACKS = (ResearchTrack.CHALLENGE, ResearchTrack.ALTERNATIVE_EXPLANATION)


def propose_evidence(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: EvidenceIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> EvidenceOut:
    """Record an evidence candidate. It must point at a source excerpt (Core §32, §36)."""
    auth = authorized(principal, "evidence.propose", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    targets.require(session, project_id, data.target_type, data.target_id)
    excerpt = sources.get_excerpt(session, data.excerpt_id)
    if excerpt.provenance.get("kind") == ProvenanceKind.AI_GENERATED.value:
        raise RuleViolationError("AI-generated text cannot be evidence (Core §36)")
    item = Evidence(
        project_id=project_id,
        target_type=data.target_type.value,
        target_id=data.target_id,
        role=data.role.value,
        status=EvidenceStatus.CANDIDATE.value,
        finding=data.finding,
        excerpt_id=excerpt.id,
        track=data.track.value if data.track else None,
        provenance=_provenance(auth, [excerpt.id]),
    )
    session.add(item)
    session.flush()
    _record(
        session,
        auth,
        "evidence.propose",
        project_id,
        "Evidence",
        item.id,
        event="EvidenceCandidateAdded",
        new={"target_type": item.target_type, "target_id": str(item.target_id), "role": item.role},
    )
    return EvidenceOut.model_validate(item)


def assess_evidence(
    session: Session, principal: Principal, project_id: UUID, evidence_id: UUID, data: AssessmentIn
) -> EvidenceOut:
    """Human acceptance or rejection. Accepted evidence updates its target's standing."""
    auth = authorized(principal, "evidence.assess")
    projects.require_editable_project(session, project_id)
    item = session.get(Evidence, evidence_id, with_for_update=True)
    if item is None or item.project_id != project_id:
        raise NotFoundError("evidence not found")
    if item.status != EvidenceStatus.CANDIDATE.value:
        raise ConflictError(f"evidence is already {item.status}; add new evidence instead of rewriting")
    if data.decision == "ACCEPT":
        if data.strength is None:
            raise RuleViolationError("accepting evidence requires a qualitative strength (FR-EVID-005)")
        item.assessment = data.model_dump(mode="json", exclude_none=True, exclude={"decision", "reason"})
        item.status = EvidenceStatus.ACCEPTED.value
    else:
        item.status = EvidenceStatus.REJECTED.value
    item.assessed_by_id = auth.actor.id
    event = "EvidenceAdded" if item.status == EvidenceStatus.ACCEPTED.value else "EvidenceRejected"
    if item.status == EvidenceStatus.ACCEPTED.value and item.role == EvidenceRole.CONTRADICTS.value:
        event = "ContradictoryEvidenceDetected"
    _record(
        session,
        auth,
        "evidence.assess",
        project_id,
        "Evidence",
        item.id,
        event=event,
        previous={"status": EvidenceStatus.CANDIDATE.value},
        new={"status": item.status, "assessment": item.assessment},
        reason=data.reason,
    )
    session.flush()
    if item.status == EvidenceStatus.ACCEPTED.value:
        targets.evidence_changed(session, project_id, EvidenceTargetType(item.target_type), item.target_id)
    return EvidenceOut.model_validate(item)


def _accepted(session: Session, target_type: EvidenceTargetType, target_id: UUID) -> list[Evidence]:
    return list(
        session.scalars(
            select(Evidence).where(
                Evidence.target_type == target_type.value,
                Evidence.target_id == target_id,
                Evidence.status == EvidenceStatus.ACCEPTED.value,
            )
        )
    )


def _lineage(session: Session) -> list[aggregation.Lineage]:
    return [
        aggregation.Lineage(edge.from_work_id, LineageRelation(edge.relation), edge.to_work_id)
        for edge in session.scalars(select(SourceLineage))
    ]


def summarize_target(session: Session, target_type: EvidenceTargetType, target_id: UUID) -> aggregation.Summary:
    """Public: evidence summary used by other modules (e.g. hypothesis epistemic updates)."""
    items = _accepted(session, target_type, target_id)
    works = sources.work_ids_for_excerpts(session, [i.excerpt_id for i in items])
    accepted = [
        aggregation.AcceptedEvidence(
            role=EvidenceRole(i.role), strength=EvidenceStrength(i.assessment["strength"]), work_id=works[i.excerpt_id]
        )
        for i in items
        if i.assessment
    ]
    return aggregation.summarize(accepted, _lineage(session))


def track_statuses(session: Session, target_type: EvidenceTargetType, target_id: UUID) -> list[TrackStatus]:
    runs = list(
        session.scalars(
            select(ResearchTrackRun)
            .where(ResearchTrackRun.target_type == target_type.value, ResearchTrackRun.target_id == target_id)
            .order_by(ResearchTrackRun.created_at)
        )
    )
    statuses = []
    for track in ResearchTrack:
        track_runs = [r for r in runs if r.track == track.value]
        completed = any(ResearchOutcomeKind(r.outcome) in COMPLETED_OUTCOMES for r in track_runs)
        last = ResearchOutcomeKind(track_runs[-1].outcome) if track_runs else None
        statuses.append(
            TrackStatus(
                track=track,
                searched=completed,
                last_outcome=last,
                execution_failed=last is ResearchOutcomeKind.RESEARCH_EXECUTION_FAILURE,
            )
        )
    return statuses


def counter_evidence_complete(session: Session, target_type: EvidenceTargetType, target_id: UUID) -> bool:
    statuses = {s.track: s for s in track_statuses(session, target_type, target_id)}
    return all(statuses[t].searched for t in COUNTER_TRACKS)


def evidence_map(session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID) -> EvidenceMap:
    targets.require(session, project_id, target_type, target_id)
    rows = list(
        session.scalars(
            select(Evidence)
            .where(Evidence.target_type == target_type.value, Evidence.target_id == target_id)
            .order_by(Evidence.created_at)
        )
    )
    by_role: dict[str, list[EvidenceOut]] = {role.value: [] for role in EvidenceRole}
    for row in rows:
        if row.status == EvidenceStatus.ACCEPTED.value:
            by_role[row.role].append(EvidenceOut.model_validate(row))
    summary = summarize_target(session, target_type, target_id)
    tracks = track_statuses(session, target_type, target_id)
    return EvidenceMap(
        target_type=target_type,
        target_id=target_id,
        by_role=by_role,
        candidates=[EvidenceOut.model_validate(r) for r in rows if r.status == EvidenceStatus.CANDIDATE.value],
        support_origins=summary.support_origins,
        contra_origins=summary.contra_origins,
        shared_origin_groups=summary.shared_origin_groups,
        meaningful_conflict=summary.meaningful_conflict,
        suggested_strength=aggregation.suggested_claim_strength(summary),
        tracks=tracks,
        counter_evidence_search_complete=all(t.searched for t in tracks if t.track in COUNTER_TRACKS),
    )


def add_lineage(session: Session, principal: Principal, data: LineageIn) -> LineageOut:
    auth = authorized(principal, "source.lineage")
    sources.require_work(session, data.from_work_id)
    sources.require_work(session, data.to_work_id)
    if data.from_work_id == data.to_work_id:
        raise RuleViolationError("a work cannot depend on itself")
    exists = session.scalars(
        select(SourceLineage).where(
            SourceLineage.from_work_id == data.from_work_id,
            SourceLineage.relation == data.relation.value,
            SourceLineage.to_work_id == data.to_work_id,
        )
    ).first()
    if exists is not None:
        return LineageOut.model_validate(exists)
    edge = SourceLineage(
        from_work_id=data.from_work_id,
        relation=data.relation.value,
        to_work_id=data.to_work_id,
        note=data.note,
        created_by_id=auth.actor.id,
    )
    session.add(edge)
    session.flush()
    governance.record_audit(
        session,
        AuditEntry(
            action="source.lineage",
            entity_type="SourceLineage",
            entity_id=edge.id,
            actor=auth.actor,
            new_state=data.model_dump(mode="json"),
            ai_action=auth.ai_action,
        ),
    )
    return LineageOut.model_validate(edge)


def list_lineage(session: Session, work_id: UUID | None = None) -> list[LineageOut]:
    query = select(SourceLineage)
    if work_id is not None:
        query = query.where((SourceLineage.from_work_id == work_id) | (SourceLineage.to_work_id == work_id))
    return [LineageOut.model_validate(e) for e in session.scalars(query.order_by(SourceLineage.created_at))]


def record_track_run(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: TrackRunIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> TrackRunOut:
    """Record what was searched and the bounded outcome (FR-WEB-005, FR-BIAS-002)."""
    auth = authorized(principal, "research_track.record", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    targets.require(session, project_id, data.target_type, data.target_id)
    run = ResearchTrackRun(
        project_id=project_id,
        target_type=data.target_type.value,
        target_id=data.target_id,
        track=data.track.value,
        outcome=data.outcome.value,
        scope=data.scope,
        queries=data.queries,
        performed_by_id=auth.actor.id,
    )
    session.add(run)
    session.flush()
    _record(
        session,
        auth,
        "research_track.record",
        project_id,
        "ResearchTrackRun",
        run.id,
        event="ResearchTrackRecorded",
        new={"track": run.track, "outcome": run.outcome, "scope": run.scope},
    )
    return TrackRunOut.model_validate(run)


# --- target registration ---


def _claim_exists(session: Session, project_id: UUID, claim_id: UUID) -> bool:
    claim = session.get(Claim, claim_id)
    return claim is not None and claim.project_id == project_id


def _claim_evidence_changed(session: Session, project_id: UUID, claim_id: UUID) -> None:
    """Claim strength follows accepted evidence, up or down (Core §34, §20 'new knowledge downgrades')."""
    summary = summarize_target(session, EvidenceTargetType.CLAIM, claim_id)
    claim = _claim(session, project_id, claim_id, lock=True)
    suggested = aggregation.suggested_claim_strength(summary)
    if claim.epistemic_strength != suggested.value:
        previous = claim.epistemic_strength
        claim.epistemic_strength = suggested.value
        governance.record_research_event(
            session,
            ResearchEventEntry(
                project_id=project_id,
                event_type="ClaimStrengthChanged",
                entity_type="Claim",
                entity_id=claim.id,
                actor=system_principal("claims_evidence").as_actor(ActorRole.SYSTEM),
                payload={"from": previous, "to": suggested.value, "support_origins": summary.support_origins},
            ),
        )


targets.register(EvidenceTargetType.CLAIM, _claim_exists, _claim_evidence_changed)


def count_candidates(session: Session, project_id: UUID) -> int:
    """Evidence candidates still awaiting human assessment (read by the Project Closure Gate)."""
    rows = session.scalars(
        select(Evidence.id).where(Evidence.project_id == project_id, Evidence.status == EvidenceStatus.CANDIDATE.value)
    )
    return len(list(rows))
