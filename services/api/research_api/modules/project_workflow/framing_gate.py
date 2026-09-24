"""Framing Gate (Core §12, §60): is the Problem Frame a Minimum Sufficient Understanding?

Pure and deterministic. Thresholds scale with risk (Core §60 "thresholds SHOULD
scale with risk"): at L3/L4 every MSU element is required; at L1/L2 only the
core situation must be present and other gaps need an explicit human decision.
"""

from __future__ import annotations

from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.governance_audit.schemas import GateFinding
from research_api.modules.project_workflow.schemas import ProblemFrameContent

# Core §12 elements: what is happening, desired, gap, current explanations,
# key hypotheses, context, constraints, known, unknown, what requires reference review.
CORE_ELEMENTS: dict[str, str] = {
    "central_issue": "central issue",
    "current_state": "what is happening (current state)",
    "desired_state": "what is desired",
    "gap": "the gap",
}
SUPPORTING_ELEMENTS: dict[str, str] = {
    "current_explanations": "current explanations",
    "initial_hypotheses": "key hypotheses",
    "context": "context",
    "constraints": "constraints",
    "known": "what is known",
    "unknowns": "what is unknown",
    "reference_review_points": "what requires reference review",
}
HIGH_RISK = frozenset({RiskLevel.L3_HIGH_IMPACT, RiskLevel.L4_CRITICAL})


def _missing(content: ProblemFrameContent, fields: dict[str, str]) -> list[tuple[str, str]]:
    missing = []
    for name, label in fields.items():
        value = getattr(content, name)
        if (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
            missing.append((name, label))
    return missing


def evaluate(content: ProblemFrameContent, risk: RiskLevel) -> tuple[G, list[GateFinding]]:
    findings = [
        GateFinding(code=f"missing.{name}", severity=G.BLOCKED, message=f"Missing {label}.")
        for name, label in _missing(content, CORE_ELEMENTS)
    ]
    supporting_severity = G.BLOCKED if risk in HIGH_RISK else G.NEEDS_HUMAN_DECISION
    findings += [
        GateFinding(code=f"missing.{name}", severity=supporting_severity, message=f"Missing {label}.")
        for name, label in _missing(content, SUPPORTING_ELEMENTS)
    ]
    if not content.research_questions:
        findings.append(
            GateFinding(
                code="missing.research_questions",
                severity=G.PASS_WITH_RESERVATIONS,
                message="No explicit research question yet; research should be organized around questions.",
            )
        )
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
