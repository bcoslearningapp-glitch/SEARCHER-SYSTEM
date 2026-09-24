import pytest

from research_api.contracts.enums import ProjectStatus as S
from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.project_workflow import framing_gate, lifecycle
from research_api.modules.project_workflow.schemas import ProblemFrameContent

COMPLETE = ProblemFrameContent(
    central_issue="Year-two disengagement",
    current_state="Attendance drops",
    desired_state="Sustained engagement",
    gap="Drivers unknown",
    current_explanations=["Pay plateau"],
    initial_hypotheses=["Mentoring gap"],
    context="Construction apprenticeships",
    constraints=["No budget for new staff"],
    known=["Drop starts month 14"],
    unknowns=["Role of pay"],
    research_questions=["What drives the drop?"],
    reference_review_points=["Fair treatment of apprentices"],
)


def test_every_status_has_a_transition_row() -> None:
    assert set(lifecycle.TRANSITIONS) == set(S)


def test_closed_only_reopens() -> None:
    assert lifecycle.TRANSITIONS[S.CLOSED] == frozenset({S.REOPENED})


@pytest.mark.parametrize(
    ("current", "target"), [(S.DRAFT, S.CLOSED), (S.DRAFT, S.ACTIVE_RESEARCH), (S.CLOSED, S.ACTIVE_RESEARCH)]
)
def test_illegal_transitions(current: S, target: S) -> None:
    assert not lifecycle.can_transition(current, target)


def test_backward_movement_allowed() -> None:
    assert lifecycle.can_transition(S.ACTIVE_RESEARCH, S.FRAMING)


def test_complete_frame_passes() -> None:
    assert framing_gate.evaluate(COMPLETE, RiskLevel.L1_EXPLORATORY)[0] is G.PASS


def test_missing_core_element_blocks_at_any_risk() -> None:
    content = COMPLETE.model_copy(update={"gap": ""})
    result, findings = framing_gate.evaluate(content, RiskLevel.L1_EXPLORATORY)
    assert result is G.BLOCKED
    assert any(f.code == "missing.gap" for f in findings)


def test_supporting_gaps_need_human_decision_at_low_risk_but_block_at_high_risk() -> None:
    content = COMPLETE.model_copy(update={"constraints": []})
    assert framing_gate.evaluate(content, RiskLevel.L2_APPLIED)[0] is G.NEEDS_HUMAN_DECISION
    assert framing_gate.evaluate(content, RiskLevel.L3_HIGH_IMPACT)[0] is G.BLOCKED


def test_missing_research_question_is_a_reservation() -> None:
    content = COMPLETE.model_copy(update={"research_questions": []})
    assert framing_gate.evaluate(content, RiskLevel.L4_CRITICAL)[0] is G.PASS_WITH_RESERVATIONS


def test_whitespace_does_not_count_as_content() -> None:
    content = COMPLETE.model_copy(update={"central_issue": "   "})
    assert framing_gate.evaluate(content, RiskLevel.L1_EXPLORATORY)[0] is G.BLOCKED
