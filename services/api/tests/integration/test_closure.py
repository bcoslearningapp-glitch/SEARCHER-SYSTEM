"""Project Closure Gate, closure approval and reopening (issue #41, PRD §41, Core §66-67)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from research_api.platform import queue
from tests.integration.test_experiments import _dh, _experiment, _ok
from tests.integration.test_projects import COMPLETE_FRAME, _draft

RECORD = {
    "closure_type": "JUSTIFIED_STOP",
    "resolved": ["Scoped the question"],
    "confidence_scope": "Low; pilot only",
    "limitations": ["One site"],
}


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _ready_project(client: TestClient, risk: str = "L1_EXPLORATORY") -> str:
    body = {"title": "Closing", "initial_input": "x", "input_type": "IDEA", "risk_level": risk}
    pid = str(client.post("/api/v1/projects", json=body).json()["id"])
    frame = _draft(client, pid, COMPLETE_FRAME)
    approved = client.post(
        f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve",
        json={"acknowledge_reservations": True, "reason": "baseline"},
    )
    assert approved.status_code == 200, approved.text
    return pid


def _to_ready(client: TestClient, pid: str) -> None:
    response = client.post(f"/api/v1/projects/{pid}/transition", json={"target": "READY_TO_CLOSE"})
    assert response.status_code == 200, response.text


def _close(client: TestClient, pid: str, **extra: Any) -> Any:
    return client.post(f"/api/v1/projects/{pid}/close", json={**RECORD, **extra})


def _codes(response: Any) -> set[str]:
    return {f["code"] for f in response.json()["error"]["details"]["findings"]}


def test_blocking_decision_prevents_closing(client: TestClient) -> None:
    pid = _ready_project(client)
    decision = client.post(
        f"/api/v1/projects/{pid}/decisions",
        json={"question": "Which site?", "options": ["A", "B"], "blocking": True},
    )
    assert decision.status_code == 201, decision.text
    _to_ready(client, pid)
    blocked = _close(client, pid)
    assert blocked.status_code == 422 and _codes(blocked) == {"decisions.blocking"}
    assert client.get(f"/api/v1/projects/{pid}").json()["status"] == "READY_TO_CLOSE"


def test_running_experiment_needs_an_explicit_override_and_closure_is_an_approval(client: TestClient) -> None:
    pid = _ready_project(client)
    eid = _experiment(client, pid, _dh(client, pid, affects_people=False)["id"])
    _ok(client, pid, eid, "PROTOCOL_DEFINED", "APPROVED", "RUNNING")
    _to_ready(client, pid)

    preview = client.post(f"/api/v1/projects/{pid}/closure-readiness", json=RECORD).json()
    assert preview["gate"] == "PROJECT_CLOSURE" and preview["result"] == "NEEDS_HUMAN_DECISION"
    assert "experiments.in_progress" in _codes(_close(client, pid))
    closed = _close(client, pid, acknowledge_reservations=True, override_reason="Pilot continues under a new project")
    assert closed.status_code == 200, closed.text
    body = closed.json()
    assert body["gate_evaluation_id"] and body["approval_id"]
    assert "acknowledge_reservations" not in body["record"], "the override is not part of the closure record"

    reopened = client.post(f"/api/v1/projects/{pid}/reopen", json={"trigger": "New cohort data"})
    assert reopened.json()["status"] == "REOPENED"
    [closure] = client.get(f"/api/v1/projects/{pid}/closures").json()
    assert closure["reopen_trigger"] == "New cohort data" and closure["approval_id"] == body["approval_id"]


def test_high_risk_closure_without_limitations_needs_a_decision(client: TestClient) -> None:
    pid = _ready_project(client, risk="L3_HIGH_IMPACT")
    _to_ready(client, pid)
    response = _close(client, pid, limitations=[])
    assert response.status_code == 422 and _codes(response) == {"record.no_limitations"}
