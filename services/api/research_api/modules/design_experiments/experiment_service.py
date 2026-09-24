"""Design hypotheses, experiments, human-impact review, observations, results and interpretations.

PRD §33-34, Core §49-51 and §60:
- A design hypothesis states a testable claim about a design concept. Its content is versioned.
- The experiment workflow is a code-enforced state machine. Approval is a human decision behind
  the Experiment Readiness Gate, and running requires operational clearance.
- The human-impact review is kept separate from reference judgments. An external approval
  becomes an unresolved operational constraint.
- Observation, analysed result and interpretation are distinct append-only records.
- Invalidating an experiment never changes the hypothesis' epistemic state (FR-EXP-004).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    ApprovalOutcome,
    ConstraintKind,
    EvidenceTargetType,
    ExperimentState,
    HumanImpactDimension,
    HumanImpactFinding,
    HypothesisEpistemicState,
    MethodologyPathStatus,
    OperationalConstraintState,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)
from research_api.modules import targets
from research_api.modules.design_experiments import experiment_rules as rules
from research_api.modules.design_experiments import service as design
from research_api.modules.design_experiments.experiment_schemas import (
    DesignHypothesisAssess,
    DesignHypothesisContent,
    DesignHypothesisIn,
    DesignHypothesisOut,
    DesignHypothesisRevision,
    ExperimentIn,
    ExperimentOut,
    ExperimentRecordOut,
    ExperimentTransitionIn,
    ExperimentTransitionOut,
    ImpactIn,
    ImpactOut,
    InterpretationIn,
    InterpretationOut,
    LearningReviewIn,
    LearningReviewOut,
    ObservationIn,
    ObservationOut,
    ProtocolIn,
    ProtocolUpdate,
    ResultIn,
    ResultOut,
    TransitionRecord,
)
from research_api.modules.design_experiments.models import (
    DesignHypothesis,
    DesignHypothesisVersion,
    Experiment,
    ExperimentResult,
    ExperimentTransition,
    HumanImpactAssessment,
    Interpretation,
    LearningReview,
    Observation,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import Authorized, authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import Actor, AIActionRecord, GateEvaluationOut
from research_api.modules.operational_constraints import service as operational
from research_api.modules.operational_constraints.schemas import ConstraintIn
from research_api.modules.project_workflow import service as projects
from research_api.modules.reference_governance import service as reference
from research_api.platform.errors import ConflictError, NotFoundError, RuleViolationError

E = ExperimentState
DH = "DesignHypothesis"
EXPERIMENT = "Experiment"
DH_TARGET = EvidenceTargetType.DESIGN_HYPOTHESIS
# Experiments whose interpretations can inform a human assessment of the design hypothesis.
USABLE = frozenset({E.INTERPRETED.value, E.CLOSED.value})


def _actor(auth: Authorized) -> dict[str, Any]:
    return auth.actor.model_dump(mode="json", exclude_none=True)


# --- design hypotheses (FR-EXP-001) ---


def _dh(session: Session, project_id: UUID, dh_id: UUID, *, lock: bool = False) -> DesignHypothesis:
    row = session.get(DesignHypothesis, dh_id, with_for_update=lock)
    if row is None or row.project_id != project_id:
        raise NotFoundError("design hypothesis not found")
    return row


def _dh_content(session: Session, row: DesignHypothesis) -> dict[str, Any]:
    version = session.scalars(
        select(DesignHypothesisVersion).where(
            DesignHypothesisVersion.design_hypothesis_id == row.id,
            DesignHypothesisVersion.version_number == row.current_version,
        )
    ).one()
    return dict(version.content)


def _snapshot(session: Session, row: DesignHypothesis, content: dict[str, Any], reason: str, auth: Authorized) -> None:
    row.current_version += 1
    session.add(
        DesignHypothesisVersion(
            design_hypothesis_id=row.id,
            version_number=row.current_version,
            content=content,
            epistemic_state=row.epistemic_state,
            change_reason=reason,
            actor=_actor(auth),
        )
    )
    session.flush()


def _dh_out(session: Session, row: DesignHypothesis) -> DesignHypothesisOut:
    return DesignHypothesisOut(
        id=row.id,
        project_id=row.project_id,
        concept_id=row.concept_id,
        current_version=row.current_version,
        content=DesignHypothesisContent.model_validate(_dh_content(session, row)),
        affects_people=row.affects_people,
        epistemic_state=HypothesisEpistemicState(row.epistemic_state),
        provenance=row.provenance,
        created_at=row.created_at,
    )


def create_design_hypothesis(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: DesignHypothesisIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> DesignHypothesisOut:
    auth = authorized(principal, "design_hypothesis.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    concept = design.get_concept(session, project_id, data.concept_id)
    if concept.status.value in {"REJECTED", "WITHDRAWN"}:
        raise RuleViolationError(f"the design concept is {concept.status.value}; derive a new concept instead")
    row = DesignHypothesis(
        project_id=project_id,
        concept_id=concept.id,
        current_version=0,
        affects_people=data.affects_people,
        epistemic_state=HypothesisEpistemicState.UNRESOLVED.value,
        provenance=design.provenance(auth),
    )
    session.add(row)
    session.flush()
    _snapshot(session, row, data.content.model_dump(mode="json"), "Created", auth)
    design.record(
        session,
        auth,
        "design_hypothesis.create",
        "DesignHypothesisCreated",
        project_id,
        DH,
        row.id,
        {"concept_id": str(concept.id), "affects_people": row.affects_people},
    )
    return _dh_out(session, row)


def get_design_hypothesis(session: Session, project_id: UUID, dh_id: UUID) -> DesignHypothesisOut:
    return _dh_out(session, _dh(session, project_id, dh_id))


def list_design_hypotheses(session: Session, project_id: UUID) -> list[DesignHypothesisOut]:
    rows = session.scalars(
        select(DesignHypothesis).where(DesignHypothesis.project_id == project_id).order_by(DesignHypothesis.created_at)
    )
    return [_dh_out(session, r) for r in rows]


def revise_design_hypothesis(
    session: Session, principal: Principal, project_id: UUID, dh_id: UUID, data: DesignHypothesisRevision
) -> DesignHypothesisOut:
    auth = authorized(principal, "design_hypothesis.revise")
    projects.require_editable_project(session, project_id)
    row = _dh(session, project_id, dh_id, lock=True)
    previous = _dh_content(session, row)
    new = data.content.model_dump(mode="json")
    if previous == new:
        raise ConflictError("content is unchanged")
    running = session.scalars(
        select(Experiment.id).where(
            Experiment.design_hypothesis_id == row.id,
            Experiment.state.in_([E.APPROVED.value, E.RUNNING.value, E.DATA_COLLECTION_COMPLETE.value]),
        )
    ).first()
    if running is not None:
        raise ConflictError("an approved or running experiment tests this version; pause or close it before revising")
    _snapshot(session, row, new, data.change_reason, auth)
    design.record(
        session,
        auth,
        "design_hypothesis.revise",
        "DesignHypothesisRevised",
        project_id,
        DH,
        row.id,
        {"version": row.current_version},
        previous=previous,
        reason=data.change_reason,
    )
    return _dh_out(session, row)


def assess_design_hypothesis(
    session: Session, principal: Principal, project_id: UUID, dh_id: UUID, data: DesignHypothesisAssess
) -> DesignHypothesisOut:
    """Human assessment grounded in interpretations of usable experiments (never invalidated ones)."""
    auth = authorized(principal, "design_hypothesis.assess")
    projects.require_editable_project(session, project_id)
    row = _dh(session, project_id, dh_id, lock=True)
    usable = session.scalars(
        select(Interpretation.id)
        .join(Experiment, Experiment.id == Interpretation.experiment_id)
        .where(Experiment.design_hypothesis_id == row.id, Experiment.state.in_(USABLE))
    ).first()
    if usable is None and data.epistemic_state is not HypothesisEpistemicState.UNRESOLVED:
        raise RuleViolationError("assessing a design hypothesis needs an interpreted experiment")
    previous = row.epistemic_state
    row.epistemic_state = data.epistemic_state.value
    _snapshot(session, row, _dh_content(session, row), data.reason, auth)
    design.record(
        session,
        auth,
        "design_hypothesis.assess",
        "DesignHypothesisAssessed",
        project_id,
        DH,
        row.id,
        {"epistemic_state": row.epistemic_state},
        previous={"epistemic_state": previous},
        reason=data.reason,
    )
    return _dh_out(session, row)


# --- experiments (FR-EXP-002/004) ---


def _experiment(session: Session, project_id: UUID, experiment_id: UUID, *, lock: bool = False) -> Experiment:
    row = session.get(Experiment, experiment_id, with_for_update=lock)
    if row is None or row.project_id != project_id:
        raise NotFoundError("experiment not found")
    return row


def _experiment_out(session: Session, row: Experiment) -> ExperimentOut:
    transitions = session.scalars(
        select(ExperimentTransition)
        .where(ExperimentTransition.experiment_id == row.id)
        .order_by(ExperimentTransition.created_at)
    )
    return ExperimentOut(
        id=row.id,
        project_id=row.project_id,
        design_hypothesis_id=row.design_hypothesis_id,
        title=row.title,
        protocol=ProtocolIn.model_validate(row.protocol),
        state=E(row.state),
        paused_from=E(row.paused_from) if row.paused_from else None,
        affects_people=row.affects_people,
        invalidation_reason=row.invalidation_reason,
        approval_id=row.approval_id,
        provenance=row.provenance,
        transitions=[
            TransitionRecord(
                from_state=E(t.from_state),
                to_state=E(t.to_state),
                reason=t.reason,
                gate_evaluation_id=t.gate_evaluation_id,
                actor=Actor.model_validate(t.actor),
                created_at=t.created_at,
            )
            for t in transitions
        ],
        created_at=row.created_at,
    )


def create_experiment(
    session: Session,
    principal: Principal,
    project_id: UUID,
    data: ExperimentIn,
    *,
    ai_action: AIActionRecord | None = None,
) -> ExperimentOut:
    auth = authorized(principal, "experiment.create", ai_action=ai_action)
    projects.require_editable_project(session, project_id)
    dh = _dh(session, project_id, data.design_hypothesis_id)
    row = Experiment(
        project_id=project_id,
        design_hypothesis_id=dh.id,
        title=data.title,
        protocol=data.protocol.model_dump(mode="json"),
        state=E.PROPOSED.value,
        affects_people=dh.affects_people,
        provenance=design.provenance(auth),
    )
    session.add(row)
    session.flush()
    design.record(
        session,
        auth,
        "experiment.create",
        "ExperimentProposed",
        project_id,
        EXPERIMENT,
        row.id,
        {"design_hypothesis_id": str(dh.id), "affects_people": row.affects_people},
    )
    return _experiment_out(session, row)


def get_experiment(session: Session, project_id: UUID, experiment_id: UUID) -> ExperimentOut:
    return _experiment_out(session, _experiment(session, project_id, experiment_id))


def list_experiments(session: Session, project_id: UUID) -> list[ExperimentOut]:
    rows = session.scalars(
        select(Experiment).where(Experiment.project_id == project_id).order_by(Experiment.created_at)
    )
    return [_experiment_out(session, r) for r in rows]


def update_protocol(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: ProtocolUpdate
) -> ExperimentOut:
    auth = authorized(principal, "experiment.protocol")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    if row.state not in {E.PROPOSED.value, E.PROTOCOL_DEFINED.value}:
        raise ConflictError(f"the protocol is fixed once the experiment is {row.state}; move it back to review first")
    previous = dict(row.protocol)
    row.protocol = data.protocol.model_dump(mode="json")
    session.flush()
    design.record(
        session,
        auth,
        "experiment.protocol",
        "ExperimentProtocolUpdated",
        project_id,
        EXPERIMENT,
        row.id,
        row.protocol,
        previous=previous,
        reason=data.reason,
    )
    return _experiment_out(session, row)


def _latest_impact(session: Session, experiment_id: UUID) -> dict[HumanImpactDimension, HumanImpactAssessment]:
    rows = session.scalars(
        select(HumanImpactAssessment)
        .where(HumanImpactAssessment.experiment_id == experiment_id)
        .order_by(HumanImpactAssessment.assessed_at)
    )
    return {HumanImpactDimension(r.dimension): r for r in rows}


def _count(session: Session, model: Any, experiment_id: UUID) -> int:
    return len(list(session.scalars(select(model.id).where(model.experiment_id == experiment_id))))


def _readiness_input(session: Session, row: Experiment, target: E) -> rules.ReadinessInput:
    project = projects.get_project(session, row.project_id)
    dh = _dh(session, row.project_id, row.design_hypothesis_id)
    content = _dh_content(session, dh)
    concept = design.get_concept(session, row.project_id, dh.concept_id)
    ref = reference.reference_standing(session, row.project_id, EvidenceTargetType.DESIGN_CONCEPT, concept.id).result
    standings = [
        operational.operational_standing(session, row.project_id, DH_TARGET, dh.id),
        operational.operational_standing(session, row.project_id, EvidenceTargetType.DESIGN_CONCEPT, concept.id),
    ]
    reviews = list(
        session.scalars(
            select(LearningReview).where(LearningReview.experiment_id == row.id).order_by(LearningReview.created_at)
        )
    )
    pending = sum(
        1 for s in standings for c in s.blocking if c.state is OperationalConstraintState.REQUIRES_EXTERNAL_APPROVAL
    )
    return rules.ReadinessInput(
        target=target,
        risk=RiskLevel(project.risk_level),
        affects_people=row.affects_people,
        protocol=dict(row.protocol),
        failure_conditions=list(content.get("failure_conditions", [])),
        stop_conditions=list(content.get("stop_conditions", [])),
        side_effects=list(content.get("side_effects", [])),
        concept_status=concept.status.value,
        reference_result=ref,
        execution_ready=all(s.execution_ready for s in standings),
        impact={d: HumanImpactFinding(a.finding) for d, a in _latest_impact(session, row.id).items()},
        unresolved_external_approvals=pending,
        observations=_count(session, Observation, row.id),
        results=_count(session, ExperimentResult, row.id),
        interpretations=_count(session, Interpretation, row.id),
        learning_reviews=len(reviews),
        review_limitations=len(reviews[-1].limitations) if reviews else 0,
    )


def evaluate_readiness(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, target: E = E.APPROVED
) -> GateEvaluationOut:
    authorized(principal, "quality_gate.evaluate")
    row = _experiment(session, project_id, experiment_id)
    data = _readiness_input(session, row, target)
    result, findings = rules.evaluate(data)
    gate = QualityGateType.LEARNING_INTEGRITY if target is E.CLOSED else QualityGateType.EXPERIMENT_READINESS
    return governance.record_gate_evaluation(
        session,
        gate=gate,
        result=result,
        risk_level=data.risk,
        findings=findings,
        project_id=project_id,
        subject_type=EXPERIMENT,
        subject_id=row.id,
    )


def transition(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: ExperimentTransitionIn
) -> ExperimentTransitionOut:
    action = "experiment.approve" if data.target is E.APPROVED else "experiment.transition"
    auth = authorized(principal, action)
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    current = E(row.state)
    paused_from = E(row.paused_from) if row.paused_from else None
    if not rules.can_transition(current, data.target, affects_people=row.affects_people, paused_from=paused_from):
        hint = " (people are affected: go through RISK_REVIEW)" if row.affects_people else ""
        raise ConflictError(f"illegal experiment transition {current} -> {data.target}{hint}")

    gate: GateEvaluationOut | None = None
    path = MethodologyPathStatus.COMPLIANT
    if data.target not in rules.STOPS:
        gate = evaluate_readiness(session, principal, project_id, experiment_id, data.target)
        if gate.result is QualityGateResult.BLOCKED:
            raise RuleViolationError(
                "Experiment Readiness Gate is BLOCKED",
                gate_evaluation_id=str(gate.id),
                findings=[f.model_dump(mode="json") for f in gate.findings if f.severity is QualityGateResult.BLOCKED],
            )
        if gate.result is QualityGateResult.NEEDS_HUMAN_DECISION:
            if not (data.acknowledge_reservations and data.reason):
                raise RuleViolationError(
                    "Experiment Readiness Gate needs a human decision: acknowledge the reservations and give a reason",
                    gate_evaluation_id=str(gate.id),
                    findings=[f.model_dump(mode="json") for f in gate.findings],
                )
            path = MethodologyPathStatus.OVERRIDDEN_WITH_REASON

    approval = None
    if data.target is E.APPROVED:
        approval = governance.record_approval(
            session,
            project_id=project_id,
            subject_type=EXPERIMENT,
            subject_id=row.id,
            actor=auth.actor,
            outcome=ApprovalOutcome.APPROVED,
            methodology_path=path,
            reason=data.reason,
            gate_evaluation_id=gate.id if gate else None,
        )
        row.approval_id = approval.id
    if data.target is E.PAUSED:
        row.paused_from = current.value
    elif current is E.PAUSED:
        row.paused_from = None
    if data.target is E.INVALIDATED:
        # The test is unusable; the design hypothesis' epistemic state is left exactly as it was.
        row.invalidation_reason = data.reason
    row.state = data.target.value
    session.add(
        ExperimentTransition(
            experiment_id=row.id,
            from_state=current.value,
            to_state=data.target.value,
            reason=data.reason,
            gate_evaluation_id=gate.id if gate else None,
            actor=_actor(auth),
        )
    )
    session.flush()
    design.record(
        session,
        auth,
        action,
        "ExperimentStateChanged",
        project_id,
        EXPERIMENT,
        row.id,
        {"from": current.value, "to": row.state, "gate": gate.result.value if gate else None, "path": path.value},
        previous={"state": current.value},
        reason=data.reason,
    )
    return ExperimentTransitionOut(experiment=_experiment_out(session, row), gate=gate, approval=approval)


# --- human-impact review (FR-HUMAN-001..003) ---


def assess_impact(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: ImpactIn
) -> ImpactOut:
    """Record one dimension. Never touches reference judgments (FR-HUMAN-002)."""
    auth = authorized(principal, "human_impact.assess")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    if E(row.state) in rules.TERMINAL:
        raise ConflictError(f"the experiment is {row.state}")
    constraint_id = None
    if data.finding is HumanImpactFinding.REQUIRES_EXTERNAL_APPROVAL:
        constraint = operational.add_constraint(
            session,
            principal,
            project_id,
            ConstraintIn(
                target_type=DH_TARGET,
                target_id=row.design_hypothesis_id,
                kind=ConstraintKind.AUTHORIZATION,
                state=OperationalConstraintState.REQUIRES_EXTERNAL_APPROVAL,
                description=f"{data.dimension.value}: {data.note}",
                source_reference=f"Human-impact review of experiment {row.id}",
                required_change=f"Approval from {data.external_authority}",
            ),
        )
        constraint_id = constraint.id
    assessment = HumanImpactAssessment(
        experiment_id=row.id,
        dimension=data.dimension.value,
        finding=data.finding.value,
        note=data.note,
        external_authority=data.external_authority,
        operational_constraint_id=constraint_id,
        assessed_by=_actor(auth),
    )
    session.add(assessment)
    session.flush()
    design.record(
        session,
        auth,
        "human_impact.assess",
        "HumanImpactAssessed",
        project_id,
        EXPERIMENT,
        row.id,
        {"dimension": assessment.dimension, "finding": assessment.finding},
    )
    return ImpactOut.model_validate(assessment)


# --- observation, result, interpretation (FR-EXP-003) ---


def _require_state(row: Experiment, allowed: set[E], what: str) -> None:
    if E(row.state) not in allowed:
        states = ", ".join(sorted(s.value for s in allowed))
        raise ConflictError(f"{what} can be recorded only while the experiment is {states}; it is {row.state}")


def record_observation(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: ObservationIn
) -> ObservationOut:
    auth = authorized(principal, "experiment.observe")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    _require_state(row, {E.RUNNING}, "observations")
    observation = Observation(
        experiment_id=row.id,
        description=data.description,
        measurements=data.measurements,
        observed_at=data.observed_at,
        recorded_by=_actor(auth),
    )
    session.add(observation)
    session.flush()
    design.record(
        session,
        auth,
        "experiment.observe",
        "ObservationRecorded",
        project_id,
        EXPERIMENT,
        row.id,
        {"observation_id": str(observation.id)},
    )
    return ObservationOut.model_validate(observation)


def record_result(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: ResultIn
) -> ResultOut:
    auth = authorized(principal, "experiment.analyse")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    _require_state(row, {E.ANALYSIS}, "analysed results")
    known = {str(i) for i in session.scalars(select(Observation.id).where(Observation.experiment_id == row.id))}
    cited = [str(i) for i in data.observation_ids]
    if not set(cited) <= known:
        raise RuleViolationError("results must be derived from this experiment's observations")
    result = ExperimentResult(
        experiment_id=row.id,
        observation_ids=cited,
        method=data.method,
        summary=data.summary,
        values=data.values,
        recorded_by=_actor(auth),
    )
    session.add(result)
    session.flush()
    design.record(
        session,
        auth,
        "experiment.analyse",
        "ResultRecorded",
        project_id,
        EXPERIMENT,
        row.id,
        {"result_id": str(result.id), "observation_ids": cited},
    )
    return ResultOut.model_validate(result)


def record_interpretation(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: InterpretationIn
) -> InterpretationOut:
    auth = authorized(principal, "experiment.interpret")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    _require_state(row, {E.ANALYSIS}, "interpretations")
    known = {
        str(i) for i in session.scalars(select(ExperimentResult.id).where(ExperimentResult.experiment_id == row.id))
    }
    cited = [str(i) for i in data.result_ids]
    if not set(cited) <= known:
        raise RuleViolationError("interpretations must cite this experiment's analysed results")
    interpretation = Interpretation(
        experiment_id=row.id,
        result_ids=cited,
        outcome=data.outcome.value,
        statement=data.statement,
        limitations=data.limitations,
        interpreted_by=_actor(auth),
    )
    session.add(interpretation)
    session.flush()
    design.record(
        session,
        auth,
        "experiment.interpret",
        "InterpretationRecorded",
        project_id,
        EXPERIMENT,
        row.id,
        {"interpretation_id": str(interpretation.id), "outcome": interpretation.outcome},
    )
    return InterpretationOut.model_validate(interpretation)


def record_learning_review(
    session: Session, principal: Principal, project_id: UUID, experiment_id: UUID, data: LearningReviewIn
) -> LearningReviewOut:
    """Lessons are recorded for interpreted, aborted and invalidated experiments alike."""
    auth = authorized(principal, "experiment.learning_review")
    projects.require_editable_project(session, project_id)
    row = _experiment(session, project_id, experiment_id, lock=True)
    _require_state(row, {E.INTERPRETED, E.ABORTED, E.INVALIDATED}, "learning reviews")
    review = LearningReview(
        experiment_id=row.id,
        learned=data.learned,
        hypothesis_effect=data.hypothesis_effect,
        surprises=data.surprises,
        limitations=data.limitations,
        validity_threats=data.validity_threats,
        next_steps=data.next_steps,
        reviewed_by=_actor(auth),
    )
    session.add(review)
    session.flush()
    design.record(
        session,
        auth,
        "experiment.learning_review",
        "LearningReviewRecorded",
        project_id,
        EXPERIMENT,
        row.id,
        {"learning_review_id": str(review.id)},
    )
    return LearningReviewOut.model_validate(review)


def experiment_record(session: Session, project_id: UUID, experiment_id: UUID) -> ExperimentRecordOut:
    row = _experiment(session, project_id, experiment_id)

    def rows(model: Any, order: Any) -> list[Any]:
        return list(session.scalars(select(model).where(model.experiment_id == row.id).order_by(order)))

    return ExperimentRecordOut(
        human_impact=[
            ImpactOut.model_validate(a) for a in rows(HumanImpactAssessment, HumanImpactAssessment.assessed_at)
        ],
        observations=[ObservationOut.model_validate(o) for o in rows(Observation, Observation.observed_at)],
        results=[ResultOut.model_validate(r) for r in rows(ExperimentResult, ExperimentResult.created_at)],
        interpretations=[InterpretationOut.model_validate(i) for i in rows(Interpretation, Interpretation.created_at)],
        learning_reviews=[LearningReviewOut.model_validate(r) for r in rows(LearningReview, LearningReview.created_at)],
    )


def _dh_exists(session: Session, project_id: UUID, dh_id: UUID) -> bool:
    row = session.get(DesignHypothesis, dh_id)
    return row is not None and row.project_id == project_id


def record_experiment(session: Session, project_id: UUID, entity_type: str, entity_id: UUID) -> UUID | None:
    """The experiment an interpretation or learning review belongs to, if it is in this project."""
    row: Interpretation | LearningReview | None
    if entity_type == "ExperimentInterpretation":
        row = session.get(Interpretation, entity_id)
    elif entity_type == "LearningReview":
        row = session.get(LearningReview, entity_id)
    else:
        return None
    experiment = session.get(Experiment, row.experiment_id) if row is not None else None
    return experiment.id if experiment is not None and experiment.project_id == project_id else None


def record_exists(session: Session, project_id: UUID, entity_type: str, entity_id: UUID) -> bool:
    """Public check for other modules citing experiment records (e.g. knowledge evidence bases)."""
    return record_experiment(session, project_id, entity_type, entity_id) is not None


targets.register(DH_TARGET, _dh_exists)
