"""Golden harness scoring is deterministic and punishes the failures it is meant to catch (FR-EVAL-003)."""

from __future__ import annotations

from typing import Any

import pytest

from research_api.config import Settings
from research_api.modules.ai_gateway.base import ProviderOutputError, StructuredRequest
from research_api.modules.ai_reliability import golden
from research_api.modules.ai_reliability.dimensions import DIMENSIONS

FIXTURES = golden.load(Settings(_env_file=None).evaluation_fixtures_dir)  # type: ignore[call-arg]
SEEDED = {  # the fake "model" below is allowed to peek at fixtures only to act as an ideal answerer
    p["text"]: p for f in ("counter_evidence", "prompt_injection") for c in FIXTURES[f]["cases"] for p in c["passages"]
}


def _passages(request: StructuredRequest) -> list[tuple[str, dict[str, Any]]]:
    return [(s.source_id or "", SEEDED[s.content]) for s in request.sections if s.kind == "retrieved_source"]


def _frame(**fields: list[str]) -> dict[str, Any]:
    empty = {k: "" for k in ("central_issue", "current_state", "desired_state", "gap", "context")}
    lists = ("current_explanations", "initial_hypotheses", "constraints", "known", "unknowns")
    return {**empty, **{k: [] for k in lists}, "research_questions": [], "reference_review_points": [], **fields}


def ideal(request: StructuredRequest) -> dict[str, Any]:
    if request.task == "draft_problem_frame":
        return _frame(
            initial_hypotheses=["Weak workplace guidance drives second-year dropout"],
            research_questions=["What keeps apprentices aged 16-18 in training?"],
            known=["The pay-freeze explanation was already refuted by cohort data"],
        )
    if request.task == "assess_passages":
        candidates = [
            {"passage_id": pid, "role": "CONTRADICTS", "alternative_index": -1, "finding": "Counter-example"}
            for pid, p in _passages(request)
            if p.get("seeded") == "counter"
        ]
        return {"candidates": candidates, "alternative_support": []}
    words = [k for c in FIXTURES["assumptions"]["cases"] for s in c["seeded"] for k in s["keywords"][:1]]
    return {"assumptions": [{"statement": f"Assumes {w}", "criticality": "HIGH", "rationale": "r"} for w in words]}


def forgetful(request: StructuredRequest) -> dict[str, Any]:
    """Loses the settled state buried in a long history: revives the refuted idea and widens the scope."""
    if request.task == "draft_problem_frame":
        return _frame(
            initial_hypotheses=["Pay freezes cause second-year dropout", "Le gel des salaires", "تجميد الأجور"],
            research_questions=[
                "Do adult learners drop out for the same reasons?",
                "Et les adultes ?",
                "ماذا عن البالغين؟",
            ],
        )
    return ideal(request)


def gullible(request: StructuredRequest) -> dict[str, Any]:
    if request.task == "assess_passages":
        canary = next((c["canary"] for c in FIXTURES["prompt_injection"]["cases"]), "")
        candidates = [
            {"passage_id": pid, "role": "SUPPORTS", "alternative_index": -1, "finding": canary}
            for pid, _ in _passages(request)
        ]
        return {"candidates": candidates, "alternative_support": []}
    return {"assumptions": []}


def _scores(caller: golden.Caller) -> dict[str, float]:
    return {r.dimension: r.score for r in golden.run(FIXTURES, caller)}


def test_fixtures_are_present_and_synthetic() -> None:
    assert {"counter_evidence", "assumptions", "prompt_injection", "long_context"} <= set(FIXTURES)
    assert all("Synthetic" in f["note"] for f in FIXTURES.values())


def test_ideal_answers_pass_every_scored_dimension() -> None:
    scores = _scores(ideal)
    for dimension, score in scores.items():
        assert DIMENSIONS[dimension].passes(score), (dimension, score)


def test_following_injected_instructions_and_missing_counter_evidence_fail() -> None:
    scores = _scores(gullible)
    assert scores["prompt_injection_resistance"] == 0.0
    assert scores["counter_evidence_retrieval"] == 0.0
    assert scores["assumption_detection"] == 0.0


def test_invalid_output_counts_against_structured_reliability() -> None:
    calls = {"n": 0}

    def flaky(request: StructuredRequest) -> dict[str, Any]:
        calls["n"] += 1
        if calls["n"] % 2:
            raise ProviderOutputError("schema violation")
        return ideal(request)

    [reliability] = [r for r in golden.run(FIXTURES, flaky) if r.dimension == "structured_output_reliability"]
    assert reliability.score == pytest.approx(0.5)
    assert not DIMENSIONS["structured_output_reliability"].passes(reliability.score)


def test_contradicting_settled_state_from_a_long_history_is_counted() -> None:
    [result] = [r for r in golden.run(FIXTURES, forgetful) if r.dimension == "long_context_consistency"]
    cases = len(FIXTURES["long_context"]["cases"])
    assert result.score == 2 * cases, "each case: the refuted hypothesis returns and the scope widens"
    assert not DIMENSIONS["long_context_consistency"].passes(result.score)
    assert all(v["contradictions"] for v in result.details.values())


def test_the_settled_state_sits_in_the_middle_of_a_long_history() -> None:
    fixture = FIXTURES["long_context"]
    history = golden._history(fixture, fixture["cases"][0])
    lines = history.splitlines()
    position = next(i for i, line in enumerate(lines) if "DECISION" in line)
    assert len(lines) >= 40 and len(lines) * 0.3 < position < len(lines) * 0.7
