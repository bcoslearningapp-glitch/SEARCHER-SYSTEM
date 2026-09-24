"""Design requirements, design concepts and the Design Readiness Gate (issue #33, PRD §32)."""

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

from research_api.contracts.schemas import contract_errors
from research_api.modules.design_experiments import service as design
from research_api.modules.design_experiments.schemas import ConceptIn, RequirementIn, SelectIn, TraceIn
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.platform import queue
from tests.contract_helpers import as_contract
from tests.integration.test_reference import _make_design_ready

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="design@1", timestamp=datetime.now(UTC))


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _project(client: TestClient, risk: str = "L1_EXPLORATORY") -> str:
    body = {"title": "Design", "initial_input": "x", "input_type": "IDEA", "risk_level": risk}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _requirement(client: TestClient, pid: str, statement: str, priority: str = "MUST") -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{pid}/design/requirements",
        json={"statement": statement, "priority": priority, "traces": [{"basis": "PURPOSE", "note": "frame"}]},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def _concept(client: TestClient, pid: str, **extra: Any) -> dict[str, Any]:
    body = {"title": "Buddy rota", "description": "Pair apprentices with a buddy.", **extra}
    response = client.post(f"/api/v1/projects/{pid}/design/concepts", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def _cover(client: TestClient, pid: str, cid: str, rid: str, coverage: str) -> dict[str, Any]:
    response = client.put(
        f"/api/v1/projects/{pid}/design/concepts/{cid}/coverage", json={"requirement_id": rid, "coverage": coverage}
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def _codes(response: Any) -> set[str]:
    return {f["code"] for f in response.json()["error"]["details"]["findings"]}


def concept_contract(concept: dict[str, Any]) -> dict[str, Any]:
    data = as_contract(concept)
    data.pop("selection", None)
    data.pop("created_at")
    data["coverage"] = [{k: c[k] for k in ("requirement_id", "coverage", "note") if k in c} for c in data["coverage"]]
    if "rejection" in data:
        data["rejection"].pop("approval_id", None)
    return dict(data)


def test_requirements_come_before_selection_and_selection_is_human(client: TestClient) -> None:
    pid = _project(client)
    hid = str(client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h"}}).json()["id"])
    concept = _concept(client, pid, hypothesis_ids=[hid])
    other = _concept(client, pid, title="Evening classes")
    assert concept["origin"] == "RESEARCHER" and concept["status"] == "PROPOSED"

    select = f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/select"
    blocked = client.post(select, json={})
    assert blocked.status_code == 422
    assert {"requirements.missing", "hypotheses.not_eligible"} <= _codes(blocked)

    requirement = _requirement(client, pid, "Must fit within existing shift patterns")
    assert requirement["status"] == "ACTIVE", "a researcher's requirement is active immediately"
    assert contract_errors("design.DesignRequirement", as_contract(requirement, drop=frozenset({"created_at"}))) == []
    assert "coverage.must_missing" in _codes(client.post(select, json={}))

    _cover(client, pid, concept["id"], requirement["id"], "MEETS")
    _make_design_ready(client, pid, hid)
    eligible = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/transition", json={"target": "ELIGIBLE_FOR_DESIGN", "reason": "ok"}
    )
    assert eligible.status_code == 200, eligible.text

    selected = client.post(select, json={"reason": "Best fit for the shift constraint"})
    assert selected.status_code == 200, selected.text
    body = selected.json()
    assert body["concept"]["status"] == "SELECTED"
    assert body["gate"]["gate"] == "DESIGN_READINESS"
    assert body["gate"]["result"] == "PASS_WITH_RESERVATIONS", "no reference review of the concept yet"
    assert body["approval"]["approved_by"]["kind"] == "HUMAN"
    assert body["concept"]["selection"]["approval_id"] == body["approval"]["id"]
    assert contract_errors("design.DesignConcept", concept_contract(body["concept"])) == []
    assert client.get(f"/api/v1/projects/{pid}/design/concepts/{other['id']}").json()["status"] == "PROPOSED", (
        "selection does not rank or reject the other concepts"
    )


def test_requirement_revision_supersedes_and_marks_coverage_stale(client: TestClient, session: Session) -> None:
    pid = _project(client)
    first = _requirement(client, pid, "Cost under 5k")
    concept = _concept(client, pid)
    _cover(client, pid, concept["id"], first["id"], "MEETS")

    revised = client.post(
        f"/api/v1/projects/{pid}/design/requirements/{first['id']}/revise",
        json={
            "statement": "Cost under 3k",
            "priority": "MUST",
            "traces": [{"basis": "OPERATIONAL_CONSTRAINT"}],
            "change_reason": "Budget cut",
        },
    ).json()
    assert revised["series_id"] == first["series_id"] and revised["version_number"] == 2
    assert revised["supersedes_id"] == first["id"]
    history = client.get(f"/api/v1/projects/{pid}/design/requirements/{revised['id']}/history").json()
    assert [(r["version_number"], r["status"]) for r in history] == [(1, "SUPERSEDED"), (2, "ACTIVE")]
    assert [r["id"] for r in client.get(f"/api/v1/projects/{pid}/design/requirements").json()] == [revised["id"]]

    [coverage] = client.get(f"/api/v1/projects/{pid}/design/concepts/{concept['id']}").json()["coverage"]
    assert coverage["stale"] is True
    gate = client.post(f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/readiness").json()
    assert "coverage.stale" in {f["code"] for f in gate["findings"]}
    stale_revise = client.post(
        f"/api/v1/projects/{pid}/design/requirements/{first['id']}/revise",
        json={"statement": "x", "traces": [{"basis": "PURPOSE"}], "change_reason": "again"},
    )
    assert stale_revise.status_code == 409

    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE design_requirements SET statement = 'edited' WHERE id = :id"), {"id": first["id"]})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM design_concepts WHERE id = :id"), {"id": concept["id"]})


def test_ai_proposals_need_human_confirmation_and_keep_ai_origin(client: TestClient, session: Session) -> None:
    pid = UUID(_project(client))
    proposed = design.create_requirement(
        session,
        AI,
        pid,
        RequirementIn(statement="Must not add paperwork", traces=[TraceIn(basis="RISK")]),
        ai_action=ACTION,
    )
    assert proposed.status == "PROPOSED"
    assert proposed.provenance["kind"] == "AI_GENERATED"
    concept = design.create_concept(
        session,
        AI,
        pid,
        ConceptIn(title="Digital log", description="Replace paper logs", origin="RESEARCHER"),
        ai_action=ACTION,
    )
    assert concept.origin == "AI", "an AI idea is never recorded as the researcher's"
    assert contract_errors("design.DesignConcept", concept.to_contract()) == []

    for attempt in (
        lambda: design.confirm_requirement(session, AI, pid, proposed.id),
        lambda: design.select_concept(session, AI, pid, concept.id, SelectIn()),
    ):
        with pytest.raises(PolicyViolationError):
            attempt()

    gate = client.post(f"/api/v1/projects/{pid}/design/concepts/{concept.id}/readiness").json()
    assert {"requirements.missing", "requirements.unconfirmed"} <= {f["code"] for f in gate["findings"]}
    confirmed = client.post(f"/api/v1/projects/{pid}/design/requirements/{proposed.id}/confirm", json={})
    assert confirmed.json()["status"] == "ACTIVE"

    human_claims_ai = client.post(
        f"/api/v1/projects/{pid}/design/concepts", json={"title": "t", "description": "d", "origin": "AI"}
    )
    assert human_claims_ai.status_code == 422


def test_rejected_design_stays_in_history_with_reusable_mechanisms(client: TestClient) -> None:
    pid = _project(client)
    mechanism = client.post(
        f"/api/v1/projects/{pid}/mechanisms", json={"name": "Peer accountability", "description": "Reusable"}
    ).json()
    concept = _concept(client, pid, mechanism_ids=[mechanism["id"]])
    reject = f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/reject"
    foreign = client.post(reject, json={"ground": "REFERENCE", "reason": "r", "reusable_mechanism_ids": [pid]})
    assert foreign.status_code == 422

    rejected = client.post(
        reject,
        json={
            "ground": "REFERENCE",
            "reason": "Blocking reservation in the reference review",
            "reusable_mechanism_ids": [mechanism["id"]],
        },
    ).json()
    assert rejected["status"] == "REJECTED"
    assert rejected["rejection"]["reusable_mechanism_ids"] == [mechanism["id"]]
    assert contract_errors("design.DesignConcept", concept_contract(rejected)) == []
    assert [c["id"] for c in client.get(f"/api/v1/projects/{pid}/design/concepts").json()] == [concept["id"]]

    gate = client.post(f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/readiness").json()
    assert gate["result"] == "BLOCKED" and "concept.closed" in {f["code"] for f in gate["findings"]}

    recombined = _concept(
        client,
        pid,
        title="Peer check-ins",
        origin="JOINT_SYNTHESIS",
        mechanism_ids=[mechanism["id"]],
        derived_from_concept_ids=[concept["id"]],
    )
    assert recombined["derived_from_concept_ids"] == [concept["id"]]


def test_high_risk_partial_must_needs_an_explicit_override(client: TestClient) -> None:
    pid = _project(client, risk="L3_HIGH_IMPACT")
    requirement = _requirement(client, pid, "Must protect apprentice wages")
    concept = _concept(client, pid)
    _cover(client, pid, concept["id"], requirement["id"], "PARTIAL")

    review = client.post(
        f"/api/v1/projects/{pid}/reference-reviews",
        json={
            "target_type": "DESIGN_CONCEPT",
            "target_id": concept["id"],
            "question": "Is the design acceptable?",
            "analytical_category": "VALUES_AND_EVALUATIVE_STANDARDS",
        },
    )
    assert review.status_code == 201, review.text
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{review.json()['id']}/judgments",
        json={"state": "NOT_IN_CONFLICT", "directness": "INFERENTIAL", "rationale": "No conflict found"},
    )

    select = f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/select"
    needs = client.post(select, json={"reason": "go"})
    assert needs.status_code == 422
    assert "coverage.must_partial" in _codes(needs)
    overridden = client.post(select, json={"reason": "Wage top-up agreed separately", "acknowledge_reservations": True})
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["gate"]["result"] == "NEEDS_HUMAN_DECISION"
    assert overridden.json()["approval"]["methodology_path"] == "OVERRIDDEN_WITH_REASON"


def test_latest_readiness_is_readable(client: TestClient) -> None:
    pid = _project(client)
    concept = _concept(client, pid)
    url = f"/api/v1/projects/{pid}/design/concepts/{concept['id']}/readiness"
    assert client.get(url).json() is None
    recorded = client.post(url).json()
    assert client.get(url).json()["id"] == recorded["id"]
