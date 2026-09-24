"""Public service for projects, Research State, scratch notes and Problem Frames.

Every mutation: authorize via the Policy Engine -> validate domain rules ->
change state -> append audit + research events, all in the caller's
transaction so nothing is partially applied (NFR-REL-003).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import (
    CONTRACT_SCHEMA_VERSION,
    ActorKind,
    ApprovalOutcome,
    DecisionStatus,
    MethodologyPathStatus,
    ProblemFrameStatus,
    ProjectStatus,
    ProvenanceKind,
    QualityGateResult,
    QualityGateType,
    ResearchMode,
    RiskLevel,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal, system_principal
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    ApprovalOut,
    AuditEntry,
    GateEvaluationOut,
    ResearchEventEntry,
    VersionContext,
)
from research_api.modules.project_workflow import framing_gate, lifecycle
from research_api.modules.project_workflow.models import (
    ProblemFrameVersion,
    Project,
    ProjectClosure,
    ResearchState,
    ScratchNote,
)
from research_api.modules.project_workflow.schemas import (
    CloseRequest,
    ClosureOut,
    ForkRequest,
    NoteCaptureTarget,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ProblemFrameApproveIn,
    ProblemFrameContent,
    ProblemFrameOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    ReopenRequest,
    ResearchStateOut,
    ResearchStateUpdate,
)
from research_api.platform.db import utcnow
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

PROJECT = "Project"
FRAME = "ProblemFrameVersion"


# --- helpers ---


def _audit(
    session: Session,
    auth: Authorized,
    action: str,
    project_id: UUID,
    *,
    entity_type: str = PROJECT,
    entity_id: UUID | None = None,
    previous: dict[str, Any] | None = None,
    new: dict[str, Any] | None = None,
    reason: str | None = None,
    actor: Actor | None = None,
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id or project_id,
            actor=actor or auth.actor,
            previous_state=previous,
            new_state=new,
            reason=reason,
            ai_action=auth.ai_action,
        ),
    )


def _event(
    session: Session,
    actor: Actor,
    event_type: str,
    project_id: UUID,
    *,
    entity_type: str = PROJECT,
    entity_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id or project_id,
            actor=actor,
            payload=payload or {},
        ),
    )


def _load(session: Session, project_id: UUID, *, lock: bool = False) -> Project:
    project = session.get(Project, project_id, with_for_update=lock)
    if project is None:
        raise NotFoundError("project not found", project_id=str(project_id))
    return project


def _require_editable(project: Project) -> None:
    if ProjectStatus(project.status) not in lifecycle.EDITABLE:
        raise ConflictError(
            f"project is {project.status}; research content cannot be changed in this status",
            status=project.status,
        )


def project_out(project: Project) -> ProjectOut:
    return ProjectOut.model_validate(
        {
            "id": project.id,
            "title": project.title,
            "initial_input": project.initial_input,
            "input_type": project.input_type,
            "sensitivity": project.sensitivity,
            "risk_level": project.risk_level,
            "status": project.status,
            "research_mode": project.research_mode,
            "primary_language": project.primary_language,
            "forked_from_project_id": project.forked_from_project_id,
            "versions": VersionContext(
                core_schema_version=project.core_schema_version,
                methodology_version=project.methodology_version,
                constitution_version=project.constitution_version,
            ),
            "owner": {"kind": project.owner_kind, "id": project.owner_id, "role": project.owner_role},
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
    )


# --- projects ---


def create_project(session: Session, principal: Principal, data: ProjectCreate) -> ProjectOut:
    auth = authorized(principal, "project.create")
    settings = get_settings()
    project = Project(
        title=data.title,
        initial_input=data.initial_input,
        input_type=data.input_type.value,
        sensitivity=data.sensitivity.value,
        risk_level=data.risk_level.value,
        status=ProjectStatus.DRAFT.value,
        research_mode=ResearchMode.EXPLORATION.value,
        primary_language=data.primary_language.value,
        core_schema_version=CONTRACT_SCHEMA_VERSION,
        methodology_version=settings.methodology_version,
        constitution_version=settings.constitution_version,
        owner_kind=auth.actor.kind.value,
        owner_id=auth.actor.id,
        owner_role=auth.actor.role.value if auth.actor.role else None,
    )
    session.add(project)
    session.flush()
    session.add(
        ResearchState(
            project_id=project.id,
            established_findings=[],
            unresolved_items=[],
            active_hypothesis_ids=[],
            reservations=[],
            blockers=[],
            # Raw input is not a complete problem model (Core §10); clarification comes first.
            next_action="Clarify the initial input and draft a Problem Frame.",
            next_action_reason="Raw input must not be treated as a complete problem definition (Core §10-11).",
        )
    )
    _audit(session, auth, "project.create", project.id, new={"status": project.status, "title": project.title})
    _event(session, auth.actor, "ProjectCreated", project.id, payload={"input_type": project.input_type})
    session.flush()
    return project_out(project)


def get_project(session: Session, project_id: UUID) -> ProjectOut:
    return project_out(_load(session, project_id))


def list_projects(session: Session) -> list[ProjectOut]:
    return [project_out(p) for p in session.scalars(select(Project).order_by(Project.updated_at.desc()))]


def update_project(session: Session, principal: Principal, project_id: UUID, data: ProjectUpdate) -> ProjectOut:
    auth = authorized(principal, "project.update")
    project = _load(session, project_id, lock=True)
    changes = data.model_dump(exclude_none=True, exclude={"reason"}, mode="json")
    previous = {k: getattr(project, k) for k in changes}
    for key, value in changes.items():
        setattr(project, key, value)
    if changes:
        _audit(session, auth, "project.update", project.id, previous=previous, new=changes, reason=data.reason)
    session.flush()
    return project_out(project)


def _has_approved_frame(session: Session, project_id: UUID) -> bool:
    return (
        session.scalar(
            select(func.count())
            .select_from(ProblemFrameVersion)
            .where(
                ProblemFrameVersion.project_id == project_id,
                ProblemFrameVersion.status == ProblemFrameStatus.APPROVED.value,
            )
        )
        or 0
    ) > 0


def _apply_transition(
    session: Session,
    auth: Authorized,
    project: Project,
    target: ProjectStatus,
    *,
    reason: str | None,
    via: str = "project.transition",
    actor: Actor | None = None,
) -> None:
    current = ProjectStatus(project.status)
    if not lifecycle.can_transition(current, target):
        raise ConflictError(f"illegal project transition {current} -> {target}", current=current, target=target)
    dedicated = lifecycle.DEDICATED.get((current, target))
    if dedicated and dedicated != via:
        raise ConflictError(f"{current} -> {target} requires the dedicated '{dedicated}' action")
    if target in lifecycle.REQUIRES_APPROVED_FRAME and not _has_approved_frame(session, project.id):
        raise RuleViolationError(
            "active research requires an explicitly approved baseline Problem Frame (Core §12)",
            gate=QualityGateType.FRAMING.value,
        )
    project.status = target.value
    _audit(
        session,
        auth,
        via,
        project.id,
        previous={"status": current.value},
        new={"status": target.value},
        reason=reason,
        actor=actor,
    )
    _event(
        session,
        actor or auth.actor,
        "ProjectStatusChanged",
        project.id,
        payload={"from": current.value, "to": target.value},
    )


def transition_project(
    session: Session, principal: Principal, project_id: UUID, target: ProjectStatus, reason: str | None
) -> ProjectOut:
    auth = authorized(principal, "project.transition")
    project = _load(session, project_id, lock=True)
    _apply_transition(session, auth, project, target, reason=reason)
    session.flush()
    return project_out(project)


def set_mode(
    session: Session, principal: Principal, project_id: UUID, mode: ResearchMode, reason: str | None
) -> ProjectOut:
    auth = authorized(principal, "project.set_mode")
    project = _load(session, project_id, lock=True)
    _require_editable(project)
    previous = project.research_mode
    project.research_mode = mode.value
    _audit(
        session,
        auth,
        "project.set_mode",
        project.id,
        previous={"mode": previous},
        new={"mode": mode.value},
        reason=reason,
    )
    _event(session, auth.actor, "ResearchModeChanged", project.id, payload={"from": previous, "to": mode.value})
    session.flush()
    return project_out(project)


def fork_project(session: Session, principal: Principal, project_id: UUID, data: ForkRequest) -> ProjectOut:
    """Fork with lineage (FR-PROJ-004). The source project is untouched."""
    auth = authorized(principal, "project.fork")
    source = _load(session, project_id)
    settings = get_settings()
    fork = Project(
        title=data.title,
        initial_input=source.initial_input,
        input_type=source.input_type,
        sensitivity=source.sensitivity,
        risk_level=source.risk_level,
        status=ProjectStatus.DRAFT.value,
        research_mode=ResearchMode.EXPLORATION.value,
        primary_language=source.primary_language,
        forked_from_project_id=source.id,
        core_schema_version=CONTRACT_SCHEMA_VERSION,
        methodology_version=settings.methodology_version,
        constitution_version=settings.constitution_version,
        owner_kind=auth.actor.kind.value,
        owner_id=auth.actor.id,
        owner_role=auth.actor.role.value if auth.actor.role else None,
    )
    session.add(fork)
    session.flush()
    state = _state(session, source.id)
    session.add(
        ResearchState(
            project_id=fork.id,
            current_question=state.current_question,
            established_findings=list(state.established_findings),
            unresolved_items=list(state.unresolved_items),
            active_hypothesis_ids=[],
            reservations=list(state.reservations),
            blockers=list(state.blockers),
            next_action="Review inherited state and draft this fork's Problem Frame.",
            next_action_reason=f"Forked from project {source.id}; framing must be approved for the fork itself.",
        )
    )
    _audit(session, auth, "project.fork", fork.id, new={"forked_from": str(source.id)}, reason=data.reason)
    _event(session, auth.actor, "ProjectForked", fork.id, payload={"forked_from": str(source.id)})
    session.flush()
    return project_out(fork)


def close_project(session: Session, principal: Principal, project_id: UUID, data: CloseRequest) -> ClosureOut:
    """The system proposes readiness; only a human closes (FR-CLOSE-003)."""
    auth = authorized(principal, "project.close")
    project = _load(session, project_id, lock=True)
    closure = ProjectClosure(
        project_id=project.id,
        closure_type=data.closure_type.value,
        record=data.model_dump(mode="json"),
        closed_by_id=auth.actor.id,
    )
    _apply_transition(session, auth, project, ProjectStatus.CLOSED, reason=data.confidence_scope, via="project.close")
    session.add(closure)
    session.flush()
    _event(
        session,
        auth.actor,
        "ProjectClosed",
        project.id,
        payload={"closure_type": closure.closure_type, "closure_id": str(closure.id)},
    )
    return ClosureOut.model_validate(closure)


def reopen_project(session: Session, principal: Principal, project_id: UUID, data: ReopenRequest) -> ProjectOut:
    """Reopen with an explicit trigger; the prior closure record is preserved (FR-REOPEN-001)."""
    auth = authorized(principal, "project.reopen")
    project = _load(session, project_id, lock=True)
    _apply_transition(session, auth, project, ProjectStatus.REOPENED, reason=data.trigger, via="project.reopen")
    closure = session.scalars(
        select(ProjectClosure)
        .where(ProjectClosure.project_id == project.id, ProjectClosure.reopened_at.is_(None))
        .order_by(ProjectClosure.closed_at.desc())
    ).first()
    if closure is not None:
        closure.reopened_at = utcnow()
        closure.reopen_trigger = data.trigger
    state = _state(session, project.id)
    state.unresolved_items = [*state.unresolved_items, f"Reopen trigger: {data.trigger}"]
    state.next_action = "Assess how the reopen trigger affects prior conclusions."
    state.next_action_reason = "Project reopened; earlier conclusions may need revision (Core §67, §75)."
    _event(session, auth.actor, "ProjectReopened", project.id, payload={"trigger": data.trigger})
    session.flush()
    return project_out(project)


def list_closures(session: Session, project_id: UUID) -> list[ClosureOut]:
    _load(session, project_id)
    rows = session.scalars(
        select(ProjectClosure).where(ProjectClosure.project_id == project_id).order_by(ProjectClosure.closed_at)
    )
    return [ClosureOut.model_validate(r) for r in rows]


# --- Research State (FR-STATE-001/002) ---


def _state(session: Session, project_id: UUID) -> ResearchState:
    state = session.get(ResearchState, project_id)
    if state is None:
        raise NotFoundError("research state not found", project_id=str(project_id))
    return state


def get_research_state(session: Session, project_id: UUID) -> ResearchStateOut:
    project = _load(session, project_id)
    state = _state(session, project_id)
    pending = governance.list_decisions(session, project_id, status=DecisionStatus.OPEN)
    return ResearchStateOut(
        project_id=project.id,
        current_question=state.current_question,
        current_mode=ResearchMode(project.research_mode),
        established_findings=state.established_findings,
        unresolved_items=state.unresolved_items,
        active_hypothesis_ids=[UUID(h) for h in state.active_hypothesis_ids],
        reservations=state.reservations,
        blockers=state.blockers,
        pending_decision_ids=[d.id for d in pending],
        next_action=state.next_action,
        next_action_reason=state.next_action_reason,
        updated_at=state.updated_at,
    )


def update_research_state(
    session: Session, principal: Principal, project_id: UUID, data: ResearchStateUpdate
) -> ResearchStateOut:
    auth = authorized(principal, "research_state.update")
    _require_editable(_load(session, project_id, lock=True))
    state = _state(session, project_id)
    changes = data.model_dump(exclude_unset=True)
    previous = {k: getattr(state, k) for k in changes}
    for key, value in changes.items():
        setattr(state, key, value)
    if changes:
        _audit(
            session,
            auth,
            "research_state.update",
            project_id,
            entity_type="ResearchState",
            previous=previous,
            new=changes,
        )
    session.flush()
    return get_research_state(session, project_id)


# --- Scratch notes (FR-SCRATCH-001..003) ---


def create_note(session: Session, principal: Principal, project_id: UUID, data: NoteCreate) -> NoteOut:
    auth = authorized(principal, "note.create")
    _load(session, project_id)
    note = ScratchNote(project_id=project_id, body=data.body, author_id=auth.actor.id)
    session.add(note)
    session.flush()
    return NoteOut.model_validate(note)


def _note(session: Session, project_id: UUID, note_id: UUID) -> ScratchNote:
    note = session.get(ScratchNote, note_id, with_for_update=True)
    if note is None or note.project_id != project_id:
        raise NotFoundError("note not found")
    return note


def update_note(session: Session, principal: Principal, project_id: UUID, note_id: UUID, data: NoteUpdate) -> NoteOut:
    authorized(principal, "note.update")
    note = _note(session, project_id, note_id)
    note.body = data.body
    session.flush()
    return NoteOut.model_validate(note)


def list_notes(session: Session, project_id: UUID) -> list[NoteOut]:
    rows = session.scalars(
        select(ScratchNote).where(ScratchNote.project_id == project_id).order_by(ScratchNote.created_at.desc())
    )
    return [NoteOut.model_validate(n) for n in rows]


def capture_note(
    session: Session, principal: Principal, project_id: UUID, note_id: UUID, target: NoteCaptureTarget
) -> NoteOut:
    """Explicit capture copies the note text into formal Research State (FR-SCRATCH-002)."""
    auth = authorized(principal, "note.capture")
    _require_editable(_load(session, project_id, lock=True))
    note = _note(session, project_id, note_id)
    state = _state(session, project_id)
    if target.target == "current_question":
        previous: Any = state.current_question
        state.current_question = note.body
    elif target.target == "unresolved_item":
        previous = list(state.unresolved_items)
        state.unresolved_items = [*state.unresolved_items, note.body]
    else:
        previous = list(state.established_findings)
        state.established_findings = [*state.established_findings, note.body]
    note.captured_as = target.target
    note.captured_at = utcnow()
    _audit(
        session,
        auth,
        "note.capture",
        project_id,
        entity_type="ScratchNote",
        entity_id=note.id,
        previous={target.target: previous},
        new={target.target: note.body},
    )
    session.flush()
    return NoteOut.model_validate(note)


def mark_note_captured(
    session: Session, principal: Principal, project_id: UUID, note_id: UUID, *, target: str, entity_id: UUID
) -> NoteOut:
    """Record that another module captured a note into a formal entity (FR-SCRATCH-002).

    The note text is copied by the capturing module; the note itself is only marked.
    """
    auth = authorized(principal, "note.capture")
    _require_editable(_load(session, project_id, lock=True))
    note = _note(session, project_id, note_id)
    if note.captured_as is not None:
        raise ConflictError(f"note was already captured as {note.captured_as}")
    note.captured_as = target
    note.captured_at = utcnow()
    _audit(
        session,
        auth,
        "note.capture",
        project_id,
        entity_type="ScratchNote",
        entity_id=note.id,
        new={"captured_as": target, "entity_id": str(entity_id)},
    )
    session.flush()
    return NoteOut.model_validate(note)


def get_note(session: Session, project_id: UUID, note_id: UUID) -> NoteOut:
    return NoteOut.model_validate(_note(session, project_id, note_id))


def require_editable_project(session: Session, project_id: UUID) -> ProjectOut:
    """Public guard for other modules: the project exists and accepts research changes."""
    project = _load(session, project_id)
    _require_editable(project)
    return project_out(project)


# --- Problem Frame (FR-FRAME-005..007) ---


def frame_out(version: ProblemFrameVersion) -> ProblemFrameOut:
    return ProblemFrameOut(
        id=version.id,
        project_id=version.project_id,
        version_number=version.version_number,
        status=ProblemFrameStatus(version.status),
        content=ProblemFrameContent.model_validate(version.content),
        provenance=version.provenance,
        approval_id=version.approval_id,
        supersedes_version_id=version.supersedes_version_id,
        created_at=version.created_at,
        updated_at=version.updated_at,
        approved_at=version.approved_at,
    )


def _frame(session: Session, project_id: UUID, version_id: UUID, *, lock: bool = False) -> ProblemFrameVersion:
    version = session.get(ProblemFrameVersion, version_id, with_for_update=lock)
    if version is None or version.project_id != project_id:
        raise NotFoundError("problem frame version not found")
    return version


def _current(session: Session, project_id: UUID, status: ProblemFrameStatus) -> ProblemFrameVersion | None:
    return session.scalars(
        select(ProblemFrameVersion).where(
            ProblemFrameVersion.project_id == project_id, ProblemFrameVersion.status == status.value
        )
    ).first()


def save_draft(
    session: Session,
    principal: Principal,
    project_id: UUID,
    content: ProblemFrameContent,
    *,
    ai_action: AIActionRecord | None = None,
) -> ProblemFrameOut:
    """Create or revise the single open draft. Approved versions are never edited (FR-FRAME-007)."""
    auth = authorized(principal, "problem_frame.draft", ai_action=ai_action)
    project = _load(session, project_id, lock=True)
    _require_editable(project)
    provenance: dict[str, Any] = {
        "kind": (ProvenanceKind.AI_GENERATED if principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT).value,
        "actor": auth.actor.model_dump(mode="json", exclude_none=True),
    }
    if ai_action is not None:
        provenance["ai_action"] = ai_action.model_dump(mode="json", exclude_none=True)

    draft = _current(session, project_id, ProblemFrameStatus.DRAFT)
    new_content = content.model_dump(mode="json")
    if draft is not None:
        previous = draft.content
        draft.content = new_content
        draft.provenance = provenance
        _audit(
            session,
            auth,
            "problem_frame.draft",
            project_id,
            entity_type=FRAME,
            entity_id=draft.id,
            previous=previous,
            new=new_content,
        )
    else:
        approved = _current(session, project_id, ProblemFrameStatus.APPROVED)
        latest = session.scalar(
            select(func.max(ProblemFrameVersion.version_number)).where(ProblemFrameVersion.project_id == project_id)
        )
        draft = ProblemFrameVersion(
            project_id=project_id,
            version_number=(latest or 0) + 1,
            status=ProblemFrameStatus.DRAFT.value,
            content=new_content,
            provenance=provenance,
            supersedes_version_id=approved.id if approved else None,
        )
        session.add(draft)
        session.flush()
        _audit(
            session,
            auth,
            "problem_frame.draft",
            project_id,
            entity_type=FRAME,
            entity_id=draft.id,
            new=new_content,
        )
        _event(
            session,
            auth.actor,
            "ProblemFrameDrafted",
            project_id,
            entity_type=FRAME,
            entity_id=draft.id,
            payload={"version_number": draft.version_number, "provenance": provenance["kind"]},
        )

    if ProjectStatus(project.status) is ProjectStatus.DRAFT:
        _apply_transition(
            session,
            authorized(principal if principal.kind is ActorKind.HUMAN else _system(), "project.transition"),
            project,
            ProjectStatus.FRAMING,
            reason="Framing started with the first Problem Frame draft.",
        )
    session.flush()
    return frame_out(draft)


def _system() -> Principal:
    return system_principal("project_workflow")


def list_frames(session: Session, project_id: UUID) -> list[ProblemFrameOut]:
    _load(session, project_id)
    rows = session.scalars(
        select(ProblemFrameVersion)
        .where(ProblemFrameVersion.project_id == project_id)
        .order_by(ProblemFrameVersion.version_number.desc())
    )
    return [frame_out(v) for v in rows]


def get_frame(session: Session, project_id: UUID, version_id: UUID) -> ProblemFrameOut:
    return frame_out(_frame(session, project_id, version_id))


def evaluate_framing_gate(
    session: Session, principal: Principal, project_id: UUID, version_id: UUID
) -> GateEvaluationOut:
    authorized(principal, "quality_gate.evaluate")
    project = _load(session, project_id)
    version = _frame(session, project_id, version_id)
    result, findings = framing_gate.evaluate(
        ProblemFrameContent.model_validate(version.content), RiskLevel(project.risk_level)
    )
    return governance.record_gate_evaluation(
        session,
        gate=QualityGateType.FRAMING,
        result=result,
        risk_level=RiskLevel(project.risk_level),
        findings=findings,
        project_id=project_id,
        subject_type=FRAME,
        subject_id=version.id,
    )


def approve_frame(
    session: Session, principal: Principal, project_id: UUID, version_id: UUID, data: ProblemFrameApproveIn
) -> ApprovalOut:
    """Explicit human approval of a Problem Frame draft (FR-FRAME-006, FR-APPROVAL-001).

    Runs the Framing Gate: BLOCKED cannot be approved; NEEDS_HUMAN_DECISION
    requires an explicit acknowledgement with a reason, recorded as an override.
    """
    auth = authorized(principal, "problem_frame.approve")
    project = _load(session, project_id, lock=True)
    _require_editable(project)
    version = _frame(session, project_id, version_id, lock=True)
    if version.status != ProblemFrameStatus.DRAFT.value:
        raise ConflictError(f"only DRAFT versions can be approved; this one is {version.status}")

    gate = evaluate_framing_gate(session, principal, project_id, version_id)
    if gate.result is QualityGateResult.BLOCKED:
        raise RuleViolationError(
            "Framing Gate is BLOCKED; complete the Problem Frame before approval",
            gate_evaluation_id=str(gate.id),
            findings=[f.model_dump(mode="json") for f in gate.findings if f.severity is QualityGateResult.BLOCKED],
        )
    path = MethodologyPathStatus.COMPLIANT
    if gate.result is QualityGateResult.NEEDS_HUMAN_DECISION:
        if not (data.acknowledge_reservations and data.reason):
            raise RuleViolationError(
                "Framing Gate needs a human decision: acknowledge the reservations and give a reason",
                gate_evaluation_id=str(gate.id),
                findings=[f.model_dump(mode="json") for f in gate.findings],
            )
        path = MethodologyPathStatus.OVERRIDDEN_WITH_REASON

    actor = auth.actor
    approval = governance.record_approval(
        session,
        project_id=project_id,
        subject_type=FRAME,
        subject_id=version.id,
        actor=actor,
        outcome=ApprovalOutcome.APPROVED,
        methodology_path=path,
        reason=data.reason,
        gate_evaluation_id=gate.id,
    )
    previous_approved = _current(session, project_id, ProblemFrameStatus.APPROVED)
    if previous_approved is not None:
        previous_approved.status = ProblemFrameStatus.SUPERSEDED.value
        session.flush()
        _event(
            session,
            actor,
            "ProblemFrameSuperseded",
            project_id,
            entity_type=FRAME,
            entity_id=previous_approved.id,
            payload={"superseded_by": str(version.id)},
        )
    version.status = ProblemFrameStatus.APPROVED.value
    version.approval_id = approval.id
    version.approved_at = approval.created_at
    session.flush()
    _audit(
        session,
        auth,
        "problem_frame.approve",
        project_id,
        entity_type=FRAME,
        entity_id=version.id,
        previous={"status": ProblemFrameStatus.DRAFT.value},
        new={"status": version.status, "approval_id": str(approval.id), "methodology_path": path.value},
        reason=data.reason,
    )
    _event(
        session,
        actor,
        "ProblemFrameApproved",
        project_id,
        entity_type=FRAME,
        entity_id=version.id,
        payload={
            "version_number": version.version_number,
            "gate_result": gate.result.value,
            "methodology_path": path.value,
        },
    )

    if ProjectStatus(project.status) in {ProjectStatus.DRAFT, ProjectStatus.FRAMING, ProjectStatus.REOPENED}:
        if ProjectStatus(project.status) is ProjectStatus.DRAFT:
            _apply_transition(
                session,
                authorized(principal, "project.transition"),
                project,
                ProjectStatus.FRAMING,
                reason="Problem Frame approved.",
            )
        _apply_transition(
            session,
            authorized(principal, "project.transition"),
            project,
            ProjectStatus.ACTIVE_RESEARCH,
            reason="Baseline Problem Frame approved.",
        )

    content = ProblemFrameContent.model_validate(version.content)
    state = _state(session, project_id)
    if not state.current_question and content.research_questions:
        state.current_question = content.research_questions[0]
    state.unresolved_items = list(dict.fromkeys([*state.unresolved_items, *content.unknowns]))
    state.next_action = "Formulate claims and hypotheses, and identify the sources they need."
    state.next_action_reason = f"Problem Frame v{version.version_number} approved as baseline."
    session.flush()
    return approval
