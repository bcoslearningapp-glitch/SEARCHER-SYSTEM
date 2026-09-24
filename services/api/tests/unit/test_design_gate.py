"""Design Readiness Gate rules (Core §60, PRD §32, §41)."""

from __future__ import annotations

from uuid import uuid4

from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.design_experiments.gate import Coverage, DesignGateInput, Requirement, evaluate


def _req(priority: str = "MUST") -> Requirement:
    return Requirement(uuid4(), uuid4(), priority, f"{priority} requirement")


def _ready(**overrides: object) -> DesignGateInput:
    must = _req()
    data = DesignGateInput(
        concept_status="PROPOSED",
        risk=RiskLevel.L1_EXPLORATORY,
        requirements=[must],
        unconfirmed_requirements=0,
        coverage={must.series_id: Coverage("MEETS", must.requirement_id)},
        hypotheses_eligible={uuid4(): True},
    )
    for key, value in overrides.items():
        setattr(data, key, value)
    return data


def _codes(data: DesignGateInput) -> tuple[G, set[str]]:
    result, findings = evaluate(data)
    return result, {f.code for f in findings}


def test_fully_ready_concept_passes() -> None:
    assert _codes(_ready()) == (G.PASS, set())


def test_no_requirements_blocks_design() -> None:
    assert _codes(_ready(requirements=[], coverage={})) == (G.BLOCKED, {"requirements.missing"})


def test_priority_decides_how_missing_coverage_counts() -> None:
    must, should, could = _req("MUST"), _req("SHOULD"), _req("COULD")
    base = _ready(requirements=[must, should, could], coverage={})
    result, codes = _codes(base)
    assert result is G.BLOCKED
    assert codes == {"coverage.must_missing", "coverage.should_missing"}, "COULD gaps are not findings"


def test_conflict_and_partial_escalate_on_high_risk() -> None:
    must, should = _req("MUST"), _req("SHOULD")
    coverage = {
        must.series_id: Coverage("PARTIAL", must.requirement_id),
        should.series_id: Coverage("CONFLICTS", should.requirement_id),
    }
    low = _ready(requirements=[must, should], coverage=coverage)
    assert _codes(low) == (G.PASS_WITH_RESERVATIONS, {"coverage.must_partial", "coverage.conflict"})
    high = _ready(requirements=[must, should], coverage=coverage, risk=RiskLevel.L3_HIGH_IMPACT)
    assert _codes(high)[0] is G.NEEDS_HUMAN_DECISION
    must_conflict = _ready(coverage={}, requirements=[must])
    must_conflict.coverage = {must.series_id: Coverage("CONFLICTS", must.requirement_id)}
    assert _codes(must_conflict)[0] is G.BLOCKED


def test_stale_coverage_and_unconfirmed_requirements_are_reservations() -> None:
    must = _req()
    data = _ready(
        requirements=[must], coverage={must.series_id: Coverage("MEETS", uuid4())}, unconfirmed_requirements=2
    )
    assert _codes(data) == (G.PASS_WITH_RESERVATIONS, {"coverage.stale", "requirements.unconfirmed"})


def test_hypotheses_reference_and_operations() -> None:
    assert _codes(_ready(hypotheses_eligible={}))[1] == {"hypotheses.none"}
    assert _codes(_ready(hypotheses_eligible={uuid4(): False})) == (G.BLOCKED, {"hypotheses.not_eligible"})
    assert _codes(_ready(reference_result=G.BLOCKED)) == (G.BLOCKED, {"reference.not_cleared"})
    assert _codes(_ready(reference_result=G.NEEDS_HUMAN_DECISION))[0] is G.NEEDS_HUMAN_DECISION
    assert _codes(_ready(execution_ready=False)) == (G.PASS_WITH_RESERVATIONS, {"operational.constrained"})


def test_closed_concepts_cannot_proceed() -> None:
    for status in ("REJECTED", "WITHDRAWN"):
        assert _codes(_ready(concept_status=status)) == (G.BLOCKED, {"concept.closed"})
