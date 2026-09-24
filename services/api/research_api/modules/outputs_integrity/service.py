"""Output composition, versioning and approval (PRD §37, FR-OUT-001/004).

An output is composed from canonical project state into traced blocks. Each change,
whether a recomposition or an edit, appends a DRAFT version, and earlier versions are
never overwritten. Exact quotes are checked against their sources whenever a version is
written. Approval is human-only.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ApprovalOutcome,
    EvidenceTargetType,
    LanguageCode,
    MethodologyPathStatus,
    OutputBlockKind,
    OutputType,
    OutputVersionStatus,
    ProvenanceKind,
)
from research_api.modules import targets
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import Actor, AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.outputs_integrity import composer, quotes
from research_api.modules.outputs_integrity.models import Output, OutputVersion
from research_api.modules.outputs_integrity.schemas import (
    SUBJECT_TYPES,
    ApproveIn,
    ApproveOut,
    Block,
    OutputIn,
    OutputOut,
    ReviseIn,
    SettingsIn,
    VersionOut,
)
from research_api.modules.project_workflow import service as projects
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

S = OutputVersionStatus
ENTITY = "Output"


def _record(
    session: Session, auth: Authorized, action: str, event: str, output: Output, payload: dict[str, Any], **kw: Any
) -> None:
    governance.record_audit(
        session,
        AuditEntry(
            project_id=output.project_id,
            action=action,
            entity_type=ENTITY,
            entity_id=output.id,
            actor=auth.actor,
            new_state=payload,
            reason=kw.get("reason"),
            ai_action=auth.ai_action,
        ),
    )
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=output.project_id,
            event_type=event,
            entity_type=ENTITY,
            entity_id=output.id,
            actor=auth.actor,
            payload=payload,
        ),
    )


def _version_out(v: OutputVersion) -> VersionOut:
    return VersionOut(
        id=v.id,
        output_id=v.output_id,
        version_number=v.version_number,
        status=S(v.status),
        blocks=[Block.model_validate(b) for b in v.blocks],
        change_reason=v.change_reason,
        approval_id=v.approval_id,
        created_by=Actor.model_validate(v.created_by),
        created_at=v.created_at,
    )


def _latest(session: Session, output: Output) -> OutputVersion:
    return session.scalars(
        select(OutputVersion).where(
            OutputVersion.output_id == output.id, OutputVersion.version_number == output.current_version
        )
    ).one()


def _out(session: Session, output: Output) -> OutputOut:
    return OutputOut(
        id=output.id,
        project_id=output.project_id,
        output_type=OutputType(output.output_type),
        title=output.title,
        language=output.language,
        mode=output.mode,
        subject_type=output.subject_type,
        subject_id=output.subject_id,
        current_version=output.current_version,
        provenance=output.provenance,
        created_at=output.created_at,
        latest=_version_out(_latest(session, output)),
    )


def _load(session: Session, project_id: UUID, output_id: UUID, *, lock: bool = False) -> Output:
    output = session.get(Output, output_id, with_for_update=lock)
    if output is None or output.project_id != project_id:
        raise NotFoundError("output not found")
    return output


def _check_quotes(session: Session, project_id: UUID, blocks: list[Block]) -> None:
    problems = []
    for index, block in enumerate(blocks):
        if block.kind is OutputBlockKind.QUOTE and block.quote is not None:
            reason = quotes.mismatch(session, project_id, block.quote)
            if reason is None and block.text != block.quote.text:
                reason = "the block text differs from its protected quote"
            if reason:
                problems.append({"block": index, "reason": reason})
    if problems:
        raise RuleViolationError("exact quotes must match their sources (FR-OUT-003)", problems=problems)


def _append(
    session: Session, output: Output, auth: Authorized, blocks: list[Block], reason: str | None
) -> OutputVersion:
    """A new DRAFT version; any earlier pending draft is superseded (approved versions stay approved)."""
    for draft in session.scalars(
        select(OutputVersion).where(OutputVersion.output_id == output.id, OutputVersion.status == S.DRAFT.value)
    ):
        draft.status = S.SUPERSEDED.value
    session.flush()
    output.current_version += 1
    version = OutputVersion(
        output_id=output.id,
        version_number=output.current_version,
        status=S.DRAFT.value,
        blocks=[b.model_dump(mode="json", exclude_none=True) for b in blocks],
        change_reason=reason,
        created_by=auth.actor.model_dump(mode="json", exclude_none=True),
    )
    session.add(version)
    session.flush()
    return version


def create_output(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: OutputIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> OutputOut:
    auth = authorized(principal, "output.create", ai_action=ai_action)
    projects.get_project(session, project_id)
    subject_type = SUBJECT_TYPES.get(data.output_type)
    blocks = composer.compose(session, project_id, data.output_type, data.language, data.subject_id)
    kind = ProvenanceKind.AI_GENERATED if principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    provenance: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        provenance["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    output = Output(
        project_id=project_id,
        output_type=data.output_type.value,
        title=data.title,
        language=data.language.value,
        mode=data.mode.value,
        subject_type=subject_type,
        subject_id=data.subject_id,
        current_version=0,
        provenance=provenance,
    )
    session.add(output)
    session.flush()
    _append(session, output, auth, blocks, "Composed from project state")
    _record(
        session, auth, "output.create", "OutputComposed", output, {"type": output.output_type, "blocks": len(blocks)}
    )
    return _out(session, output)


def recompose(session: Session, principal: Principal, project_id: UUID, output_id: UUID) -> OutputOut:
    """Refresh from the current project state as a new draft; nothing earlier is overwritten."""
    auth = authorized(principal, "output.create")
    output = _load(session, project_id, output_id, lock=True)
    blocks = composer.compose(
        session, project_id, OutputType(output.output_type), LanguageCode(output.language), output.subject_id
    )
    _append(session, output, auth, blocks, "Recomposed from project state")
    _record(session, auth, "output.recompose", "OutputComposed", output, {"version": output.current_version})
    return _out(session, output)


def revise(
    session: Session,
    principal: Principal,
    project_id: UUID,
    output_id: UUID,
    data: ReviseIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> OutputOut:
    """Edited blocks become a new draft. Quotes must still match their sources, and traces must exist."""
    auth = authorized(principal, "output.revise", ai_action=ai_action)
    output = _load(session, project_id, output_id, lock=True)
    _check_quotes(session, project_id, data.blocks)
    _append(session, output, auth, data.blocks, data.change_reason)
    _record(
        session,
        auth,
        "output.revise",
        "OutputRevised",
        output,
        {"version": output.current_version},
        reason=data.change_reason,
    )
    return _out(session, output)


def update_settings(
    session: Session, principal: Principal, project_id: UUID, output_id: UUID, data: SettingsIn
) -> OutputOut:
    auth = authorized(principal, "output.settings")
    output = _load(session, project_id, output_id, lock=True)
    if data.title:
        output.title = data.title
    if data.mode:
        output.mode = data.mode.value
    session.flush()
    _record(
        session, auth, "output.settings", "OutputSettingsChanged", output, {"title": output.title, "mode": output.mode}
    )
    return _out(session, output)


def approve(
    session: Session, principal: Principal, project_id: UUID, output_id: UUID, version_id: UUID, data: ApproveIn
) -> ApproveOut:
    """Human approval of the current draft; the previously approved version is superseded."""
    auth = authorized(principal, "output.approve")
    output = _load(session, project_id, output_id, lock=True)
    version = session.get(OutputVersion, version_id, with_for_update=True)
    if version is None or version.output_id != output.id:
        raise NotFoundError("output version not found")
    if version.status != S.DRAFT.value or version.version_number != output.current_version:
        raise ConflictError("only the latest draft can be approved")
    blocks = [Block.model_validate(b) for b in version.blocks]
    _check_quotes(session, project_id, blocks)
    missing = _missing_traces(session, project_id, blocks)
    if missing:
        raise RuleViolationError("some statements trace to entities that no longer exist", missing=missing)
    approval = governance.record_approval(
        session,
        project_id=project_id,
        subject_type="OutputVersion",
        subject_id=version.id,
        actor=auth.actor,
        outcome=ApprovalOutcome.APPROVED,
        methodology_path=MethodologyPathStatus.COMPLIANT,
        reason=data.reason,
    )
    for previous in session.scalars(
        select(OutputVersion).where(OutputVersion.output_id == output.id, OutputVersion.status == S.APPROVED.value)
    ):
        previous.status = S.SUPERSEDED.value
    session.flush()
    version.status = S.APPROVED.value
    version.approval_id = approval.id
    session.flush()
    _record(
        session,
        auth,
        "output.approve",
        "OutputApproved",
        output,
        {"version": version.version_number},
        reason=data.reason,
    )
    return ApproveOut(version=_version_out(version), approval=approval)


_TARGETS = {
    "Claim": EvidenceTargetType.CLAIM,
    "Hypothesis": EvidenceTargetType.HYPOTHESIS,
    "Mechanism": EvidenceTargetType.MECHANISM,
    "DesignConcept": EvidenceTargetType.DESIGN_CONCEPT,
    "DesignHypothesis": EvidenceTargetType.DESIGN_HYPOTHESIS,
}


def _missing_traces(session: Session, project_id: UUID, blocks: list[Block]) -> list[dict[str, str]]:
    """Traces to registered research targets must resolve in this project."""
    missing = []
    for block in blocks:
        for trace in block.trace:
            target = _TARGETS.get(trace.entity_type)
            if target is None:
                continue
            try:
                targets.require(session, project_id, target, trace.entity_id)
            except NotFoundError:
                missing.append({"entity_type": trace.entity_type, "entity_id": str(trace.entity_id)})
    return missing


def get_output(session: Session, project_id: UUID, output_id: UUID) -> OutputOut:
    return _out(session, _load(session, project_id, output_id))


def list_outputs(session: Session, project_id: UUID) -> list[OutputOut]:
    rows = session.scalars(select(Output).where(Output.project_id == project_id).order_by(Output.created_at))
    return [_out(session, o) for o in rows]


def list_versions(session: Session, project_id: UUID, output_id: UUID) -> list[VersionOut]:
    _load(session, project_id, output_id)
    rows = session.scalars(
        select(OutputVersion).where(OutputVersion.output_id == output_id).order_by(OutputVersion.version_number)
    )
    return [_version_out(v) for v in rows]
