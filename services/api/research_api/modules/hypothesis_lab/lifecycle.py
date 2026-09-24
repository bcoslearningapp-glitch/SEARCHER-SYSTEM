"""Hypothesis lifecycle and Hypothesis Gate rules (Core §20-21, FR-HYP-001/003). Pure functions."""

from __future__ import annotations

from research_api.contracts.enums import HypothesisEpistemicState as E
from research_api.contracts.enums import HypothesisLifecycleState as L
from research_api.contracts.enums import QualityGateResult as G
from research_api.modules.governance_audit.schemas import GateFinding

ORDER: list[L] = [
    L.SIGNAL,
    L.IDEA,
    L.FORMULATED_HYPOTHESIS,
    L.UNDER_REFERENCE_REVIEW,
    L.UNDER_SCRUTINY,
    L.UNDER_RESEARCH,
    L.ASSESSED,
    L.ELIGIBLE_FOR_DESIGN,
    L.USED_IN_DESIGN,
    L.TESTED_IN_PRACTICE,
]
_INDEX = {state: i for i, state in enumerate(ORDER)}

REQUIRED_FOR_FORMULATED = {
    "statement": "claim",
    "context": "context",
    "expected_outcome": "expected outcome",
    "falsification_conditions": "falsification conditions",
}
RECOMMENDED_FOR_FORMULATED = {
    "proposed_mechanism": "proposed mechanism",
    "assumptions": "assumptions",
    "boundary_conditions": "boundary conditions",
}
DESIGN_READY_STATES = frozenset({E.SUPPORTED, E.PROMISING})


def can_transition(current: L, target: L) -> bool:
    """Forward one step at a time; backward to any earlier stage when knowledge changes (Core §75)."""
    return _INDEX[target] == _INDEX[current] + 1 or _INDEX[target] < _INDEX[current]


def reaches(state: L, milestone: L) -> bool:
    return _INDEX[state] >= _INDEX[milestone]


def _empty(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)


def gate(
    target: L,
    content: dict[str, object],
    epistemic: E,
    counter_evidence_complete: bool,
    reference_result: G = G.PASS,
) -> tuple[G, list[GateFinding]]:
    """Hypothesis Gate for a proposed lifecycle transition."""
    findings: list[GateFinding] = []
    if reaches(target, L.FORMULATED_HYPOTHESIS):
        for field, label in REQUIRED_FOR_FORMULATED.items():
            if _empty(content.get(field)):
                findings.append(
                    GateFinding(
                        code=f"missing.{field}", severity=G.BLOCKED, message=f"A formulated hypothesis needs {label}."
                    )
                )
        for field, label in RECOMMENDED_FOR_FORMULATED.items():
            if _empty(content.get(field)):
                findings.append(
                    GateFinding(
                        code=f"missing.{field}", severity=G.PASS_WITH_RESERVATIONS, message=f"No {label} recorded yet."
                    )
                )
    if reaches(target, L.ELIGIBLE_FOR_DESIGN):
        if epistemic not in DESIGN_READY_STATES:
            findings.append(
                GateFinding(
                    code="epistemic.not_ready",
                    severity=G.BLOCKED,
                    message=f"Hypothesis is {epistemic.value}; design needs PROMISING or SUPPORTED.",
                )
            )
        if not counter_evidence_complete:
            findings.append(
                GateFinding(
                    code="counter_evidence.missing",
                    severity=G.BLOCKED,
                    message="Challenge and alternative-explanation searches are not complete.",
                )
            )
        # Effectiveness does not override a governing reference rejection (Core §74.8).
        if reference_result in {G.BLOCKED, G.NEEDS_HUMAN_DECISION}:
            findings.append(
                GateFinding(
                    code="reference.not_cleared",
                    severity=G.BLOCKED,
                    message=f"Reference Gate is {reference_result.value}.",
                )
            )
        elif reference_result is G.PASS_WITH_RESERVATIONS:
            findings.append(
                GateFinding(
                    code="reference.reservations",
                    severity=G.PASS_WITH_RESERVATIONS,
                    message="Reference review has reservations or has not been done.",
                )
            )
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
