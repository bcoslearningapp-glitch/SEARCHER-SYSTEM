"""Design hypotheses, experiments, human-impact review, observations/results/interpretations (issue #34)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.enums import HumanImpactDimension
from research_api.contracts.schemas import contract_errors
from research_api.modules.design_experiments import experiment_service as experiments
from research_api.modules.design_experiments.experiment_schemas import (
    DesignHypothesisContent,
    DesignHypothesisIn,
    ExperimentIn,
    ExperimentTransitionIn,
    ImpactIn,
    ObservationIn,
)
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.platform import queue

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="exp@1", timestamp=datetime.now(UTC))
PROTOCOL = {
    "method": "Pilot at two sites",
    "sample": "40 second-year apprentices",
    "duration": "8 weeks",
    "data_collected": "Weekly attendance",
    "analysis_plan": "Compare with prior cohort",
    "success_criteria": "Attendance >= 90%",
}
CONTENT = {
    "intervention": "Weekly buddy check-in",
    "target_population": "Second-year apprentices",
    "context": "Construction sites",
    "mechanism": "Peer accountability",
    "expected_outcome": "Attendance stays above 90%",
    "measurement_plan": "Weekly attendance records",
    "failure_conditions": ["Attendance below 80% after 8 weeks"],
    "side_effects": ["Buddy workload"],
    "stop_conditions": ["Any safeguarding concern"],
}


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _project(client: TestClient, risk: str = "L1_EXPLORATORY") -> str:
    body = {"title": "Experiments", "initial_input": "x", "input_type": "IDEA", "risk_level": risk}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _concept(client: TestClient, pid: str) -> str:
    response = client.post(
        f"/api/v1/projects/{pid}/design/concepts", json={"title": "Buddy rota", "description": "Pair apprentices"}
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _dh(client: TestClient, pid: str, *, affects_people: bool) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{pid}/design-hypotheses",
        json={"concept_id": _concept(client, pid), "content": CONTENT, "affects_people": affects_people},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def _experiment(client: TestClient, pid: str, dh_id: str, protocol: dict[str, str] | None = None) -> str:
    body = {"design_hypothesis_id": dh_id, "title": "Buddy pilot", "protocol": protocol or PROTOCOL}
    response = client.post(f"/api/v1/projects/{pid}/experiments", json=body)
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _move(client: TestClient, pid: str, eid: str, target: str, **extra: Any) -> Any:
    return client.post(f"/api/v1/projects/{pid}/experiments/{eid}/transition", json={"target": target, **extra})


def _ok(client: TestClient, pid: str, eid: str, *targets: str) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for target in targets:
        response = _move(client, pid, eid, target)
        assert response.status_code == 200, f"{target}: {response.text}"
        body = response.json()
    return body


def _codes(response: Any) -> set[str]:
    return {f["code"] for f in response.json()["error"]["details"]["findings"]}


def _impact(client: TestClient, pid: str, eid: str, dimension: str, finding: str, **extra: Any) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{pid}/experiments/{eid}/human-impact",
        json={"dimension": dimension, "finding": finding, "note": f"{dimension} reviewed", **extra},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def _observe(client: TestClient, pid: str, eid: str, description: str = "Week 1: 18 of 20 attended") -> Any:
    return client.post(
        f"/api/v1/projects/{pid}/experiments/{eid}/observations",
        json={"description": description, "measurements": {"attended": 18}, "observed_at": "2026-09-20T09:00:00Z"},
    )


def _contract(value: dict[str, Any], *drop: str) -> dict[str, Any]:
    return {k: v for k, v in value.items() if v is not None and k not in drop}


def _collect_analyse_interpret(client: TestClient, pid: str, eid: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Observation -> analysed result -> interpretation, each a distinct record (FR-EXP-003)."""
    observation = _observe(client, pid, eid).json()
    assert contract_errors("experiment.Observation", _contract(observation)) == []
    _ok(client, pid, eid, "DATA_COLLECTION_COMPLETE", "ANALYSIS")
    assert _observe(client, pid, eid).status_code == 409, "observation closes when data collection completes"

    results = f"/api/v1/projects/{pid}/experiments/{eid}/results"
    foreign = client.post(results, json={"observation_ids": [pid], "method": "rate", "summary": "s"})
    assert foreign.status_code == 422
    result = client.post(
        results,
        json={
            "observation_ids": [observation["id"]],
            "method": "Attendance rate",
            "summary": "90%",
            "values": {"r": 0.9},
        },
    ).json()
    assert contract_errors("experiment.ExperimentResult", _contract(result)) == []
    assert _codes(_move(client, pid, eid, "INTERPRETED")) == {"interpretation.missing"}
    interpretation = client.post(
        f"/api/v1/projects/{pid}/experiments/{eid}/interpretations",
        json={
            "result_ids": [result["id"]],
            "outcome": "SUPPORTS",
            "statement": "Attendance held",
            "limitations": "2 sites",
        },
    ).json()
    assert contract_errors("experiment.Interpretation", _contract(interpretation)) == []
    closed = _ok(client, pid, eid, "INTERPRETED", "CLOSED")["experiment"]
    assert [t["to_state"] for t in closed["transitions"]][-2:] == ["INTERPRETED", "CLOSED"]
    return observation, interpretation


def test_people_affected_experiment_runs_the_full_governed_path(client: TestClient, session: Session) -> None:
    pid = _project(client)
    dh = _dh(client, pid, affects_people=True)
    assert dh["epistemic_state"] == "UNRESOLVED"
    assert contract_errors("experiment.DesignHypothesis", _contract(dh, "created_at")) == []

    eid = _experiment(client, pid, dh["id"], protocol={"method": "Pilot"})
    blocked = _move(client, pid, eid, "PROTOCOL_DEFINED")
    assert blocked.status_code == 422 and _codes(blocked) == {"protocol.incomplete"}
    client.put(f"/api/v1/projects/{pid}/experiments/{eid}/protocol", json={"protocol": PROTOCOL, "reason": "complete"})
    _ok(client, pid, eid, "PROTOCOL_DEFINED")
    assert _move(client, pid, eid, "APPROVED").status_code == 409, "people affected: risk review first"
    _ok(client, pid, eid, "RISK_REVIEW")
    assert "impact.incomplete" in _codes(_move(client, pid, eid, "APPROVED"))

    for dimension in HumanImpactDimension:
        if dimension is HumanImpactDimension.INSTITUTIONAL_APPROVAL:
            external = _impact(
                client, pid, eid, dimension.value, "REQUIRES_EXTERNAL_APPROVAL", external_authority="Site employer"
            )
        else:
            _impact(client, pid, eid, dimension.value, "ADDRESSED")
    assert external["operational_constraint_id"], "the external approval is an unresolved operational requirement"
    assert contract_errors("experiment.HumanImpactAssessment", _contract(external)) == []
    standing = client.get(f"/api/v1/projects/{pid}/standing/DESIGN_HYPOTHESIS/{dh['id']}").json()
    assert standing["operational"]["execution_ready"] is False
    assert standing["reference"]["result"] != "BLOCKED", "the human-impact review never writes a reference judgment"

    approved = _move(client, pid, eid, "APPROVED", reason="Protocol and impact review complete")
    assert approved.status_code == 200, approved.text
    assert approved.json()["gate"]["gate"] == "EXPERIMENT_READINESS"
    assert approved.json()["approval"]["approved_by"]["kind"] == "HUMAN"
    assert "operational.external_approval_pending" in {f["code"] for f in approved.json()["gate"]["findings"]}

    cannot_run = _move(client, pid, eid, "RUNNING")
    assert cannot_run.status_code == 422 and _codes(cannot_run) == {"operational.constrained"}
    assert _observe(client, pid, eid).status_code == 409, "no observations before the experiment runs"
    resolved = client.post(
        f"/api/v1/projects/{pid}/operational-constraints/{external['operational_constraint_id']}/resolve",
        json={"resolution": "Employer signed the pilot agreement"},
    )
    assert resolved.status_code == 200, resolved.text
    _ok(client, pid, eid, "RUNNING")

    observation, interpretation = _collect_analyse_interpret(client, pid, eid)

    record = client.get(f"/api/v1/projects/{pid}/experiments/{eid}/record").json()
    assert (len(record["observations"]), len(record["results"]), len(record["interpretations"])) == (1, 1, 1)
    assessed = client.post(
        f"/api/v1/projects/{pid}/design-hypotheses/{dh['id']}/assess",
        json={"epistemic_state": "SUPPORTED", "reason": "Pilot interpretation supports it"},
    )
    assert assessed.json()["epistemic_state"] == "SUPPORTED"

    for table, row_id in (
        ("experiment_observations", observation["id"]),
        ("experiment_interpretations", interpretation["id"]),
    ):
        with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
            session.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": row_id})  # noqa: S608
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM experiments WHERE id = :id"), {"id": eid})


def test_invalidated_experiment_is_not_a_failed_test(client: TestClient) -> None:
    pid = _project(client)
    dh = _dh(client, pid, affects_people=False)
    eid = _experiment(client, pid, dh["id"])
    _ok(client, pid, eid, "PROTOCOL_DEFINED", "APPROVED", "RUNNING")
    _observe(client, pid, eid)
    assert _move(client, pid, eid, "INVALIDATED").status_code == 422, "invalidation needs a reason"
    response = _move(client, pid, eid, "INVALIDATED", reason="Attendance system outage corrupted the data")
    assert response.status_code == 200
    invalidated = response.json()["experiment"]
    assert invalidated["invalidation_reason"]
    assert contract_errors("experiment.Experiment", invalidated_contract(invalidated)) == []

    after = client.get(f"/api/v1/projects/{pid}/design-hypotheses/{dh['id']}").json()
    assert after["epistemic_state"] == "UNRESOLVED", "an invalid experiment says nothing about the hypothesis"
    assess = client.post(
        f"/api/v1/projects/{pid}/design-hypotheses/{dh['id']}/assess",
        json={"epistemic_state": "REFUTED", "reason": "the pilot failed"},
    )
    assert assess.status_code == 422, "an invalidated experiment cannot ground an assessment"
    assert _move(client, pid, eid, "RUNNING").status_code == 409, "INVALIDATED is final"


def invalidated_contract(experiment: dict[str, Any]) -> dict[str, Any]:
    data = _contract(experiment, "paused_from", "approval_id", "transitions", "created_at")
    data["protocol"] = {k: v for k, v in data["protocol"].items() if v}
    return data


def test_pause_resumes_where_it_left_off(client: TestClient) -> None:
    pid = _project(client)
    eid = _experiment(client, pid, _dh(client, pid, affects_people=False)["id"])
    _ok(client, pid, eid, "PROTOCOL_DEFINED", "APPROVED", "RUNNING")
    paused = _move(client, pid, eid, "PAUSED", reason="Site closed for a week").json()["experiment"]
    assert paused["paused_from"] == "RUNNING"
    assert _move(client, pid, eid, "ANALYSIS").status_code == 409
    assert _ok(client, pid, eid, "RUNNING")["experiment"]["paused_from"] is None


def test_open_concerns_need_an_explicit_override(client: TestClient) -> None:
    pid = _project(client)
    eid = _experiment(client, pid, _dh(client, pid, affects_people=True)["id"])
    _ok(client, pid, eid, "PROTOCOL_DEFINED", "RISK_REVIEW")
    for dimension in HumanImpactDimension:
        _impact(
            client, pid, eid, dimension.value, "CONCERN" if dimension is HumanImpactDimension.CONSENT else "ADDRESSED"
        )
    needs = _move(client, pid, eid, "APPROVED", reason="go")
    assert needs.status_code == 422 and "impact.concern" in _codes(needs)
    overridden = _move(client, pid, eid, "APPROVED", reason="Opt-out consent agreed", acknowledge_reservations=True)
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["approval"]["methodology_path"] == "OVERRIDDEN_WITH_REASON"


def test_ai_can_propose_but_never_runs_research_on_people(client: TestClient, session: Session) -> None:
    pid = UUID(_project(client))
    concept = UUID(_concept(client, str(pid)))
    dh = experiments.create_design_hypothesis(
        session,
        AI,
        pid,
        DesignHypothesisIn(concept_id=concept, content=DesignHypothesisContent(**CONTENT), affects_people=True),
        ai_action=ACTION,
    )
    assert dh.provenance["kind"] == "AI_GENERATED"
    experiment = experiments.create_experiment(
        session, AI, pid, ExperimentIn(design_hypothesis_id=dh.id, title="AI-proposed pilot"), ai_action=ACTION
    )
    assert experiment.state == "PROPOSED"
    for attempt in (
        lambda: experiments.transition(
            session, AI, pid, experiment.id, ExperimentTransitionIn(target="PROTOCOL_DEFINED")
        ),
        lambda: experiments.transition(session, AI, pid, experiment.id, ExperimentTransitionIn(target="APPROVED")),
        lambda: experiments.assess_impact(
            session, AI, pid, experiment.id, ImpactIn(dimension="HARM", finding="ADDRESSED", note="n")
        ),
        lambda: experiments.record_observation(
            session, AI, pid, experiment.id, ObservationIn(description="d", observed_at=datetime.now(UTC))
        ),
    ):
        with pytest.raises(PolicyViolationError):
            attempt()
