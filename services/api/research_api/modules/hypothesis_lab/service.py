"""Public service for hypotheses and mechanisms (Core §20-22, FR-HYP-001..006, FR-MECH-001..003).

Every material change appends an immutable HypothesisVersion. Accepted evidence
can downgrade a hypothesis automatically; upgrades need a human assessment.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ActorKind,
    ActorRole,
    EvidenceTargetType,
    HypothesisEpistemicState,
    HypothesisLifecycleState,
    MechanismStatus,
    ProvenanceKind,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)
from research_api.modules import targets
from research_api.modules.claims_evidence import aggregation
from research_api.modules.claims_evidence import service as evidence
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal, system_principal
from research_api.modules.governance_audit.schemas import Actor, AIActionRecord, AuditEntry, ResearchEventEntry
from research_api.modules.hypothesis_lab import lifecycle
from research_api.modules.hypothesis_lab.models import (
    Hypothesis,
    HypothesisCompetition,
    HypothesisMechanism,
    HypothesisVersion,
    Mechanism,
)
from research_api.modules.hypothesis_lab.schemas import (
    AssessIn,
    CompeteIn,
    HypothesisContent,
    HypothesisIn,
    HypothesisOut,
    MechanismIn,
    MechanismOut,
    MechanismUpdate,
    ReviseIn,
    TransitionIn,
    TransitionOut,
    VersionOut,
)
from research_api.modules.project_workflow import service as projects
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

H = HypothesisEpistemicState
T = EvidenceTargetType.HYPOTHESIS


def _provenance(auth: Authorized) -> dict[str, Any]:
    kind = ProvenanceKind.AI_GENERATED if auth.principal.kind is ActorKind.AI else ProvenanceKind.HUMAN_INPUT
    data: dict[str, Any] = {"kind": kind.value, "actor": auth.actor.model_dump(mode="json", exclude_none=True)}
    if auth.ai_action is not None:
        data["ai_action"] = auth.ai_action.model_dump(mode="json", exclude_none=True)
    return data


def _audit(
    session: Session,
    auth: Authorized | None,
    actor: Actor,
    action: str,
    project_id: UUID,
    entity_type: str,
    entity_id: UUID,
    *,
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
            actor=actor,
            previous_state=previous,
            new_state=new,
            reason=reason,
            ai_action=auth.ai_action if auth else None,
        ),
    )


def _event(
    session: Session,
    actor: Actor,
    event_type: str,
    project_id: UUID,
    entity_type: str,
    entity_id: UUID,
    payload: dict[str, Any],
) -> None:
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            payload=payload,
        ),
    )


def _snapshot(session: Session, hypothesis: Hypothesis, content: dict[str, Any], reason: str, actor: Actor) -> None:
    hypothesis.current_version += 1
    session.add(
        HypothesisVersion(
            hypothesis_id=hypothesis.id,
            version_number=hypothesis.current_version,
            content=content,
            lifecycle_state=hypothesis.lifecycle_state,
            epistemic_state=hypothesis.epistemic_state,
            change_reason=reason,
            actor_kind=actor.kind.value,
            actor_id=actor.id,
            actor_role=actor.role.value if actor.role else None,
        )
    )
    session.flush()


def _latest_content(session: Session, hypothesis: Hypothesis) -> dict[str, Any]:
    version = session.scalars(
        select(HypothesisVersion).where(
            HypothesisVersion.hypothesis_id == hypothesis.id,
            HypothesisVersion.version_number == hypothesis.current_version,
        )
    ).one()
    return dict(version.content)


def _load(session: Session, project_id: UUID, hypothesis_id: UUID, *, lock: bool = False) -> Hypothesis:
    hypothesis = session.get(Hypothesis, hypothesis_id, with_for_update=lock)
    if hypothesis is None or hypothesis.project_id != project_id:
        raise NotFoundError("hypothesis not found")
    return hypothesis


def _out(session: Session, hypothesis: Hypothesis) -> HypothesisOut:
    competing = session.scalars(
        select(HypothesisCompetition).where(
            or_(
                HypothesisCompetition.hypothesis_a_id == hypothesis.id,
                HypothesisCompetition.hypothesis_b_id == hypothesis.id,
            )
        )
    )
    others = [c.hypothesis_b_id if c.hypothesis_a_id == hypothesis.id else c.hypothesis_a_id for c in competing]
    mechanisms = session.scalars(
        select(HypothesisMechanism.mechanism_id).where(HypothesisMechanism.hypothesis_id == hypothesis.id)
    )
    summary = evidence.summarize_target(session, T, hypothesis.id)
    return HypothesisOut(
        id=hypothesis.id,
        project_id=hypothesis.project_id,
        current_version=hypothesis.current_version,
        lifecycle_state=HypothesisLifecycleState(hypothesis.lifecycle_state),
        epistemic_state=H(hypothesis.epistemic_state),
        content=HypothesisContent.model_validate(_latest_content(session, hypothesis)),
        competing_hypothesis_ids=others,
        mechanism_ids=list(mechanisms),
        suggested_epistemic_state=aggregation.suggested_hypothesis_state(summary),
        counter_evidence_search_complete=evidence.counter_evidence_complete(session, T, hypothesis.id),
        provenance=hypothesis.provenance,
        created_at=hypothesis.created_at,
    )


# --- hypotheses ---


def create_hypothesis(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: HypothesisIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> HypothesisOut:
    auth = authorized(principal, "hypothesis.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    if lifecycle.reaches(data.lifecycle_state, HypothesisLifecycleState.FORMULATED_HYPOTHESIS):
        raise RuleViolationError("new hypotheses start as SIGNAL or IDEA; formulate them through the Hypothesis Gate")
    hypothesis = Hypothesis(
        project_id=project_id,
        current_version=0,
        lifecycle_state=data.lifecycle_state.value,
        epistemic_state=H.UNRESOLVED.value,
        provenance=_provenance(auth),
    )
    session.add(hypothesis)
    session.flush()
    _snapshot(session, hypothesis, data.content.model_dump(mode="json"), "Created", auth.actor)
    _audit(
        session,
        auth,
        auth.actor,
        "hypothesis.create",
        project_id,
        "Hypothesis",
        hypothesis.id,
        new={"lifecycle_state": hypothesis.lifecycle_state},
    )
    _event(
        session,
        auth.actor,
        "HypothesisCreated",
        project_id,
        "Hypothesis",
        hypothesis.id,
        {"statement": data.content.statement, "provenance": hypothesis.provenance["kind"]},
    )
    return _out(session, hypothesis)


def get_hypothesis(session: Session, project_id: UUID, hypothesis_id: UUID) -> HypothesisOut:
    return _out(session, _load(session, project_id, hypothesis_id))


def list_hypotheses(session: Session, project_id: UUID) -> list[HypothesisOut]:
    rows = session.scalars(
        select(Hypothesis).where(Hypothesis.project_id == project_id).order_by(Hypothesis.created_at)
    )
    return [_out(session, h) for h in rows]


def list_versions(session: Session, project_id: UUID, hypothesis_id: UUID) -> list[VersionOut]:
    _load(session, project_id, hypothesis_id)
    rows = session.scalars(
        select(HypothesisVersion)
        .where(HypothesisVersion.hypothesis_id == hypothesis_id)
        .order_by(HypothesisVersion.version_number)
    )
    return [
        VersionOut(
            id=v.id,
            hypothesis_id=v.hypothesis_id,
            version_number=v.version_number,
            content=HypothesisContent.model_validate(v.content),
            lifecycle_state=HypothesisLifecycleState(v.lifecycle_state),
            epistemic_state=H(v.epistemic_state),
            change_reason=v.change_reason,
            created_at=v.created_at,
            actor=Actor.model_validate({"kind": v.actor_kind, "id": v.actor_id, "role": v.actor_role}),
        )
        for v in rows
    ]


def revise(
    session: Session, principal: Principal, project_id: UUID, hypothesis_id: UUID, data: ReviseIn
) -> HypothesisOut:
    auth = authorized(principal, "hypothesis.revise")
    projects.require_editable_project(session, project_id)
    hypothesis = _load(session, project_id, hypothesis_id, lock=True)
    previous = _latest_content(session, hypothesis)
    new = data.content.model_dump(mode="json")
    if previous == new:
        raise ConflictError("content is unchanged")
    _snapshot(session, hypothesis, new, data.change_reason, auth.actor)
    _audit(
        session,
        auth,
        auth.actor,
        "hypothesis.revise",
        project_id,
        "Hypothesis",
        hypothesis.id,
        previous=previous,
        new=new,
        reason=data.change_reason,
    )
    _event(
        session,
        auth.actor,
        "HypothesisRevised",
        project_id,
        "Hypothesis",
        hypothesis.id,
        {"version": hypothesis.current_version},
    )
    return _out(session, hypothesis)


def transition(
    session: Session, principal: Principal, project_id: UUID, hypothesis_id: UUID, data: TransitionIn
) -> TransitionOut:
    auth = authorized(principal, "hypothesis.transition")
    project = projects.require_editable_project(session, project_id)
    hypothesis = _load(session, project_id, hypothesis_id, lock=True)
    current = HypothesisLifecycleState(hypothesis.lifecycle_state)
    if not lifecycle.can_transition(current, data.target):
        raise ConflictError(f"illegal hypothesis transition {current} -> {data.target}")
    content = _latest_content(session, hypothesis)
    result, findings = lifecycle.gate(
        data.target,
        content,
        H(hypothesis.epistemic_state),
        evidence.counter_evidence_complete(session, T, hypothesis.id),
    )
    gate_eval = governance.record_gate_evaluation(
        session,
        gate=QualityGateType.HYPOTHESIS,
        result=result,
        risk_level=RiskLevel(project.risk_level),
        findings=findings,
        project_id=project_id,
        subject_type="Hypothesis",
        subject_id=hypothesis.id,
    )
    if result is QualityGateResult.BLOCKED:
        raise RuleViolationError(
            "Hypothesis Gate is BLOCKED",
            gate_evaluation_id=str(gate_eval.id),
            findings=[f.model_dump(mode="json") for f in findings if f.severity is QualityGateResult.BLOCKED],
        )
    hypothesis.lifecycle_state = data.target.value
    _snapshot(session, hypothesis, content, data.reason, auth.actor)
    _audit(
        session,
        auth,
        auth.actor,
        "hypothesis.transition",
        project_id,
        "Hypothesis",
        hypothesis.id,
        previous={"lifecycle_state": current.value},
        new={"lifecycle_state": data.target.value},
        reason=data.reason,
    )
    _event(
        session,
        auth.actor,
        "HypothesisLifecycleChanged",
        project_id,
        "Hypothesis",
        hypothesis.id,
        {"from": current.value, "to": data.target.value, "gate": result.value},
    )
    return TransitionOut(hypothesis=_out(session, hypothesis), gate=gate_eval)


def assess(
    session: Session, principal: Principal, project_id: UUID, hypothesis_id: UUID, data: AssessIn
) -> HypothesisOut:
    """Human epistemic assessment. Going above what the evidence suggests is recorded as an override."""
    auth = authorized(principal, "hypothesis.assess")
    projects.require_editable_project(session, project_id)
    hypothesis = _load(session, project_id, hypothesis_id, lock=True)
    previous = hypothesis.epistemic_state
    suggested = aggregation.suggested_hypothesis_state(evidence.summarize_target(session, T, hypothesis.id))
    override = aggregation.HYPOTHESIS_RANK[data.epistemic_state] > aggregation.HYPOTHESIS_RANK[suggested]
    hypothesis.epistemic_state = data.epistemic_state.value
    _snapshot(session, hypothesis, _latest_content(session, hypothesis), data.reason, auth.actor)
    _audit(
        session,
        auth,
        auth.actor,
        "hypothesis.assess",
        project_id,
        "Hypothesis",
        hypothesis.id,
        previous={"epistemic_state": previous},
        new={
            "epistemic_state": data.epistemic_state.value,
            "suggested": suggested.value,
            "methodology_path": "OVERRIDDEN_WITH_REASON" if override else "COMPLIANT",
        },
        reason=data.reason,
    )
    _event(
        session,
        auth.actor,
        "HypothesisAssessed",
        project_id,
        "Hypothesis",
        hypothesis.id,
        {"from": previous, "to": data.epistemic_state.value, "override": override},
    )
    return _out(session, hypothesis)


def compete(
    session: Session, principal: Principal, project_id: UUID, hypothesis_id: UUID, data: CompeteIn
) -> HypothesisOut:
    auth = authorized(principal, "hypothesis.link")
    a = _load(session, project_id, hypothesis_id)
    b = _load(session, project_id, data.other_hypothesis_id)
    if a.id == b.id:
        raise RuleViolationError("a hypothesis cannot compete with itself")
    first, second = sorted([a.id, b.id], key=str)
    if session.get(HypothesisCompetition, (first, second)) is None:
        session.add(HypothesisCompetition(hypothesis_a_id=first, hypothesis_b_id=second, note=data.note))
        _audit(
            session,
            auth,
            auth.actor,
            "hypothesis.link",
            project_id,
            "Hypothesis",
            a.id,
            new={"competes_with": str(b.id)},
        )
        session.flush()
    return _out(session, a)


def link_mechanism(
    session: Session, principal: Principal, project_id: UUID, hypothesis_id: UUID, mechanism_id: UUID
) -> HypothesisOut:
    auth = authorized(principal, "hypothesis.link")
    hypothesis = _load(session, project_id, hypothesis_id)
    _mechanism(session, project_id, mechanism_id)
    if session.get(HypothesisMechanism, (hypothesis.id, mechanism_id)) is None:
        session.add(HypothesisMechanism(hypothesis_id=hypothesis.id, mechanism_id=mechanism_id))
        _audit(
            session,
            auth,
            auth.actor,
            "hypothesis.link",
            project_id,
            "Hypothesis",
            hypothesis.id,
            new={"mechanism_id": str(mechanism_id)},
        )
        session.flush()
    return _out(session, hypothesis)


def _on_evidence_changed(session: Session, project_id: UUID, hypothesis_id: UUID) -> None:
    """New knowledge can downgrade earlier confidence automatically (Core §20, FR-HYP-006)."""
    hypothesis = _load(session, project_id, hypothesis_id, lock=True)
    current = H(hypothesis.epistemic_state)
    suggested = aggregation.suggested_hypothesis_state(evidence.summarize_target(session, T, hypothesis.id))
    if not aggregation.is_downgrade(current, suggested):
        return
    authorized(system_principal("hypothesis_lab"), "hypothesis.downgrade")
    actor = system_principal("hypothesis_lab").as_actor(ActorRole.SYSTEM)
    hypothesis.epistemic_state = suggested.value
    reason = f"Accepted evidence lowers the assessment from {current.value} to {suggested.value}"
    _snapshot(session, hypothesis, _latest_content(session, hypothesis), reason, actor)
    _audit(
        session,
        None,
        actor,
        "hypothesis.downgrade",
        project_id,
        "Hypothesis",
        hypothesis.id,
        previous={"epistemic_state": current.value},
        new={"epistemic_state": suggested.value},
        reason=reason,
    )
    _event(
        session,
        actor,
        "HypothesisDowngraded",
        project_id,
        "Hypothesis",
        hypothesis.id,
        {"from": current.value, "to": suggested.value},
    )


def _hypothesis_exists(session: Session, project_id: UUID, hypothesis_id: UUID) -> bool:
    hypothesis = session.get(Hypothesis, hypothesis_id)
    return hypothesis is not None and hypothesis.project_id == project_id


# --- mechanisms (FR-MECH-001..003) ---


def _mechanism(session: Session, project_id: UUID, mechanism_id: UUID, *, lock: bool = False) -> Mechanism:
    mechanism = session.get(Mechanism, mechanism_id, with_for_update=lock)
    if mechanism is None or mechanism.project_id != project_id:
        raise NotFoundError("mechanism not found")
    return mechanism


def create_mechanism(session: Session, principal: Principal, project_id: UUID, data: MechanismIn) -> MechanismOut:
    auth = authorized(principal, "mechanism.create")
    projects.require_editable_project(session, project_id)
    mechanism = Mechanism(
        project_id=project_id,
        name=data.name,
        description=data.description,
        status=MechanismStatus.PROPOSED.value,
        provenance=_provenance(auth),
    )
    session.add(mechanism)
    session.flush()
    _audit(
        session,
        auth,
        auth.actor,
        "mechanism.create",
        project_id,
        "Mechanism",
        mechanism.id,
        new={"name": mechanism.name, "status": mechanism.status},
    )
    _event(session, auth.actor, "MechanismProposed", project_id, "Mechanism", mechanism.id, {"name": mechanism.name})
    return MechanismOut.model_validate(mechanism)


def update_mechanism(
    session: Session, principal: Principal, project_id: UUID, mechanism_id: UUID, data: MechanismUpdate
) -> MechanismOut:
    auth = authorized(principal, "mechanism.update")
    projects.require_editable_project(session, project_id)
    mechanism = _mechanism(session, project_id, mechanism_id, lock=True)
    previous = mechanism.status
    mechanism.status = data.status.value
    _audit(
        session,
        auth,
        auth.actor,
        "mechanism.update",
        project_id,
        "Mechanism",
        mechanism.id,
        previous={"status": previous},
        new={"status": mechanism.status},
        reason=data.reason,
    )
    session.flush()
    return MechanismOut.model_validate(mechanism)


def list_mechanisms(session: Session, project_id: UUID) -> list[MechanismOut]:
    rows = session.scalars(select(Mechanism).where(Mechanism.project_id == project_id).order_by(Mechanism.created_at))
    return [MechanismOut.model_validate(m) for m in rows]


def _mechanism_exists(session: Session, project_id: UUID, mechanism_id: UUID) -> bool:
    mechanism = session.get(Mechanism, mechanism_id)
    return mechanism is not None and mechanism.project_id == project_id


targets.register(EvidenceTargetType.HYPOTHESIS, _hypothesis_exists, _on_evidence_changed)
targets.register(EvidenceTargetType.MECHANISM, _mechanism_exists)
