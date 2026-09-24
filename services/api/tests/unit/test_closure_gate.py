"""Project Closure Gate rules (PRD §41, Core §60, §66)."""

from __future__ import annotations

from dataclasses import replace

from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.project_workflow.closure_gate import ClosureInput, evaluate

CLEAN = ClosureInput(
    risk=RiskLevel.L1_EXPLORATORY,
    blocking_decisions=0,
    open_decisions=0,
    evidence_candidates=0,
    experiments_in_progress=[],
    unresolved=0,
    limitations=1,
    reopen_triggers=0,
)


def _codes(data: ClosureInput) -> tuple[G, set[str]]:
    result, findings = evaluate(data)
    return result, {f.code for f in findings}


def test_clean_closure_passes() -> None:
    assert _codes(CLEAN) == (G.PASS, set())


def test_blocking_decisions_block() -> None:
    assert _codes(replace(CLEAN, blocking_decisions=1)) == (G.BLOCKED, {"decisions.blocking"})


def test_open_work_needs_attention_scaled_by_risk() -> None:
    assert _codes(replace(CLEAN, open_decisions=2))[0] is G.PASS_WITH_RESERVATIONS
    assert _codes(replace(CLEAN, open_decisions=2, risk=RiskLevel.L3_HIGH_IMPACT))[0] is G.NEEDS_HUMAN_DECISION
    running = replace(CLEAN, experiments_in_progress=["Pilot"])
    assert _codes(running) == (G.NEEDS_HUMAN_DECISION, {"experiments.in_progress"})
    assert _codes(replace(running, risk=RiskLevel.L4_CRITICAL))[0] is G.BLOCKED
    assert _codes(replace(CLEAN, evidence_candidates=3)) == (G.PASS_WITH_RESERVATIONS, {"evidence.unassessed"})


def test_closure_record_quality() -> None:
    assert _codes(replace(CLEAN, limitations=0)) == (G.PASS_WITH_RESERVATIONS, {"record.no_limitations"})
    high = replace(CLEAN, limitations=0, risk=RiskLevel.L3_HIGH_IMPACT)
    assert _codes(high) == (G.NEEDS_HUMAN_DECISION, {"record.no_limitations"})
    no_triggers = replace(CLEAN, unresolved=2)
    assert _codes(no_triggers) == (G.PASS_WITH_RESERVATIONS, {"record.no_reopen_triggers"})
    assert _codes(replace(no_triggers, reopen_triggers=1)) == (G.PASS, set())
