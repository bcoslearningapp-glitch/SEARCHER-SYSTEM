from research_api.contracts.enums import HypothesisEpistemicState as E
from research_api.contracts.enums import HypothesisLifecycleState as L
from research_api.contracts.enums import QualityGateResult as G
from research_api.modules.hypothesis_lab import lifecycle


def test_forward_one_step_backward_any() -> None:
    assert lifecycle.can_transition(L.IDEA, L.FORMULATED_HYPOTHESIS)
    assert not lifecycle.can_transition(L.IDEA, L.UNDER_RESEARCH)
    assert lifecycle.can_transition(L.ASSESSED, L.IDEA)


def test_formulation_requires_falsifiability() -> None:
    result, findings = lifecycle.gate(
        L.FORMULATED_HYPOTHESIS, {"statement": "s", "context": "c", "expected_outcome": "o"}, E.UNRESOLVED, False
    )
    assert result is G.BLOCKED
    assert any(f.code == "missing.falsification_conditions" for f in findings)


def test_design_requires_readiness_and_counter_evidence() -> None:
    content = {
        "statement": "s",
        "context": "c",
        "expected_outcome": "o",
        "falsification_conditions": ["f"],
        "proposed_mechanism": "m",
        "assumptions": ["a"],
        "boundary_conditions": ["b"],
    }
    assert lifecycle.gate(L.ELIGIBLE_FOR_DESIGN, content, E.SUPPORTED, True)[0] is G.PASS
    assert lifecycle.gate(L.ELIGIBLE_FOR_DESIGN, content, E.SUPPORTED, False)[0] is G.BLOCKED
    assert lifecycle.gate(L.ELIGIBLE_FOR_DESIGN, content, E.CONTESTED, True)[0] is G.BLOCKED
