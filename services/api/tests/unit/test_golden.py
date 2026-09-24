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


def ideal(request: StructuredRequest) -> dict[str, Any]:
    if request.task == "assess_passages":
        candidates = [
            {"passage_id": pid, "role": "CONTRADICTS", "alternative_index": -1, "finding": "Counter-example"}
            for pid, p in _passages(request)
            if p.get("seeded") == "counter"
        ]
        return {"candidates": candidates, "alternative_support": []}
    words = [k for c in FIXTURES["assumptions"]["cases"] for s in c["seeded"] for k in s["keywords"][:1]]
    return {"assumptions": [{"statement": f"Assumes {w}", "criticality": "HIGH", "rationale": "r"} for w in words]}


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
    assert {"counter_evidence", "assumptions", "prompt_injection"} <= set(FIXTURES)
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
