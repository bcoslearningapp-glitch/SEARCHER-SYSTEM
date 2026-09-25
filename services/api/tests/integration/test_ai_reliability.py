"""AI reliability registry and golden runs (issue #30)."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_reliability import golden
from research_api.modules.ai_reliability import service as reliability
from research_api.modules.ai_reliability.schemas import EvaluationIn
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from tests.unit.test_golden import FIXTURES, ideal


@pytest.fixture(autouse=True)
def _mock_ai(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    get_settings.cache_clear()
    registry.reset_cache()
    yield
    mock_adapter.STATE.responders.clear()
    get_settings.cache_clear()
    registry.reset_cache()


def _model() -> str:
    return f"test-model-{uuid4().hex[:8]}"


def test_steward_records_results_against_thresholds(client: TestClient) -> None:
    model = _model()
    body = {"provider": "anthropic", "model": model, "dimension": "citation_accuracy", "score": 0.9, "sample_size": 50}
    recorded = client.post("/api/v1/ai/reliability/evaluations", json=body)
    assert recorded.status_code == 201, recorded.text
    assert recorded.json()["passed"] is False and recorded.json()["threshold"] == 0.95
    unknown = client.post("/api/v1/ai/reliability/evaluations", json={**body, "dimension": "vibes"})
    assert unknown.status_code == 422
    standing = next(m for m in client.get("/api/v1/ai/reliability").json()["models"] if m["model"] == model)
    assert standing["blocking_failures"] == ["citation_accuracy"]
    assert "counter_evidence_retrieval" in standing["blocking_unevaluated"]
    # Installation-audited dimensions are measured once for the installation, not per model (#56).
    assert "exact_quote_fidelity" not in standing["blocking_unevaluated"]


def test_ai_cannot_grade_itself(session: Session) -> None:
    data = EvaluationIn(provider="mock", model=_model(), dimension="citation_accuracy", score=1.0, sample_size=1)
    with pytest.raises(PolicyViolationError):
        reliability.record_evaluation(session, ai_principal("research_orchestrator"), data)


def test_golden_run_through_the_gateway_is_logged_and_recorded(client: TestClient, session: Session) -> None:
    mock_adapter.register("assess_passages", ideal)
    mock_adapter.register("detect_assumptions", ideal)
    results = golden.run(FIXTURES, golden.gateway_caller(session, "mock"))
    model = _model()
    run_id = uuid4()
    golden.record(session, results, provider="mock", model=model, run_id=run_id)
    body = client.get("/api/v1/ai/reliability").json()
    standing = next(m for m in body["models"] if m["model"] == model)
    assert standing["latest"]["prompt_injection_resistance"]["passed"] is True
    assert standing["latest"]["counter_evidence_retrieval"]["method"] == "AUTOMATED_GOLDEN"
    assert standing["latest"]["structured_output_reliability"]["score"] == 1.0
    rows = [r for r in body["operational"] if r["provider"] == "mock" and r["task"] == "assess_passages"]
    assert rows and rows[0]["succeeded"] >= 5 and rows[0]["structured_output_reliability"] == 1.0


def test_evaluations_are_append_only(client: TestClient, session: Session) -> None:
    body = {"provider": "openai", "model": _model(), "dimension": "hallucination_rate", "score": 0.5, "sample_size": 3}
    client.post("/api/v1/ai/reliability/evaluations", json=body)
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE ai_evaluations SET passed = true WHERE model = :m"), {"m": body["model"]})
