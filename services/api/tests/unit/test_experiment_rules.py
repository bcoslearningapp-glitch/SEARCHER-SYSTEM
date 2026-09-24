"""Experiment workflow and Experiment Readiness Gate rules (Core §50-51, §60; PRD §33-34)."""

from __future__ import annotations

from itertools import pairwise
from typing import Any

from research_api.contracts.enums import ExperimentState as E
from research_api.contracts.enums import HumanImpactDimension as D
from research_api.contracts.enums import HumanImpactFinding as F
from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.design_experiments.experiment_rules import (
    PROTOCOL_FIELDS,
    ReadinessInput,
    can_transition,
    evaluate,
)

PROTOCOL = {f: "defined" for f in PROTOCOL_FIELDS}
ALL_ADDRESSED = {d: F.ADDRESSED for d in D}


def _input(target: E = E.APPROVED, **overrides: Any) -> ReadinessInput:
    data = ReadinessInput(
        target=target,
        risk=RiskLevel.L1_EXPLORATORY,
        affects_people=False,
        protocol=dict(PROTOCOL),
        failure_conditions=["f"],
        stop_conditions=["s"],
        side_effects=["e"],
        concept_status="SELECTED",
    )
    for key, value in overrides.items():
        setattr(data, key, value)
    return data


def _codes(data: ReadinessInput) -> tuple[G, set[str]]:
    result, findings = evaluate(data)
    return result, {f.code for f in findings}


def test_forward_path_and_people_need_risk_review() -> None:
    path = [E.PROPOSED, E.PROTOCOL_DEFINED, E.APPROVED, E.RUNNING, E.DATA_COLLECTION_COMPLETE, E.ANALYSIS]
    path += [E.INTERPRETED, E.CLOSED]
    for current, target in pairwise(path):
        assert can_transition(current, target, affects_people=False)
    assert not can_transition(E.PROTOCOL_DEFINED, E.APPROVED, affects_people=True)
    assert can_transition(E.PROTOCOL_DEFINED, E.RISK_REVIEW, affects_people=True)
    assert can_transition(E.RISK_REVIEW, E.APPROVED, affects_people=True)
    assert not can_transition(E.PROPOSED, E.RUNNING, affects_people=False), "no skipping approval"


def test_pause_resumes_only_where_it_left_off_and_terminal_states_are_final() -> None:
    assert can_transition(E.RUNNING, E.PAUSED, affects_people=False)
    assert can_transition(E.PAUSED, E.RUNNING, affects_people=False, paused_from=E.RUNNING)
    assert not can_transition(E.PAUSED, E.ANALYSIS, affects_people=False, paused_from=E.RUNNING)
    assert can_transition(E.PAUSED, E.INVALIDATED, affects_people=False, paused_from=E.RUNNING)
    for terminal in (E.CLOSED, E.ABORTED, E.INVALIDATED):
        assert not can_transition(terminal, E.RUNNING, affects_people=False)
        assert not can_transition(terminal, E.PAUSED, affects_people=False)


def test_approval_needs_protocol_and_failure_and_stop_conditions() -> None:
    assert _codes(_input()) == (G.PASS, set())
    result, codes = _codes(_input(protocol={}, failure_conditions=[], stop_conditions=[], side_effects=[]))
    assert result is G.BLOCKED
    assert codes == {
        "protocol.incomplete",
        "hypothesis.no_failure_conditions",
        "hypothesis.no_stop_conditions",
        "hypothesis.no_side_effects",
    }


def test_people_affected_requires_complete_impact_review() -> None:
    assert _codes(_input(affects_people=True)) == (G.BLOCKED, {"impact.incomplete"})
    assert _codes(_input(affects_people=True, impact=ALL_ADDRESSED)) == (G.PASS, set())
    concern = {**ALL_ADDRESSED, D.CONSENT: F.CONCERN}
    assert _codes(_input(affects_people=True, impact=concern)) == (G.NEEDS_HUMAN_DECISION, {"impact.concern"})
    critical = _input(affects_people=True, impact=concern, risk=RiskLevel.L4_CRITICAL)
    assert _codes(critical)[0] is G.BLOCKED


def test_external_approval_can_be_approved_but_not_run() -> None:
    pending = {**ALL_ADDRESSED, D.INSTITUTIONAL_APPROVAL: F.REQUIRES_EXTERNAL_APPROVAL}
    approval = _input(affects_people=True, impact=pending, unresolved_external_approvals=1)
    assert _codes(approval) == (G.PASS_WITH_RESERVATIONS, {"operational.external_approval_pending"})
    assert _codes(_input(E.RUNNING, execution_ready=False)) == (G.BLOCKED, {"operational.constrained"})
    assert _codes(_input(E.RUNNING)) == (G.PASS, set())


def test_concept_and_reference_standing() -> None:
    assert _codes(_input(concept_status="REJECTED"))[0] is G.BLOCKED
    assert _codes(_input(concept_status="PROPOSED")) == (G.PASS_WITH_RESERVATIONS, {"concept.not_selected"})
    assert _codes(_input(reference_result=G.NEEDS_HUMAN_DECISION))[0] is G.NEEDS_HUMAN_DECISION
    assert _codes(_input(E.RUNNING, reference_result=G.BLOCKED))[0] is G.BLOCKED


def test_data_and_interpretation_prerequisites() -> None:
    assert _codes(_input(E.DATA_COLLECTION_COMPLETE)) == (G.BLOCKED, {"observations.none"})
    assert _codes(_input(E.DATA_COLLECTION_COMPLETE, observations=3))[0] is G.PASS
    assert _codes(_input(E.INTERPRETED, results=1)) == (G.BLOCKED, {"interpretation.missing"})
    assert _codes(_input(E.INTERPRETED, results=1, interpretations=1))[0] is G.PASS


def test_learning_integrity_gate_closes_only_with_a_review() -> None:
    assert _codes(_input(E.CLOSED)) == (G.BLOCKED, {"learning.missing"})
    reviewed = _input(E.CLOSED, learning_reviews=1)
    assert _codes(reviewed) == (G.PASS_WITH_RESERVATIONS, {"learning.no_limitations"})
    assert _codes(_input(E.CLOSED, learning_reviews=1, risk=RiskLevel.L3_HIGH_IMPACT))[0] is G.NEEDS_HUMAN_DECISION
    assert _codes(_input(E.CLOSED, learning_reviews=1, review_limitations=2)) == (G.PASS, set())
