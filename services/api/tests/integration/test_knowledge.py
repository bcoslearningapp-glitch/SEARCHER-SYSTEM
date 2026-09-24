"""Learning review -> local knowledge -> gated promotion, standing, temporal validity, labelled reuse (issue #35)."""

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
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.knowledge_memory import service as knowledge
from research_api.modules.knowledge_memory.schemas import BasisIn, KnowledgeIn, PromoteIn
from research_api.platform import queue
from tests.integration.test_experiments import _dh, _experiment, _observe, _ok

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="k@1", timestamp=datetime.now(UTC))


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _project(client: TestClient, risk: str = "L1_EXPLORATORY") -> str:
    body = {"title": "Knowledge", "initial_input": "x", "input_type": "IDEA", "risk_level": risk}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _closed_experiment(client: TestClient, pid: str) -> tuple[str, str]:
    """Run an experiment to CLOSED; return its interpretation and learning review ids."""
    eid = _experiment(client, pid, _dh(client, pid, affects_people=False)["id"])
    _ok(client, pid, eid, "PROTOCOL_DEFINED", "APPROVED", "RUNNING")
    observation = _observe(client, pid, eid).json()
    _ok(client, pid, eid, "DATA_COLLECTION_COMPLETE", "ANALYSIS")
    base = f"/api/v1/projects/{pid}/experiments/{eid}"
    result = client.post(
        f"{base}/results", json={"observation_ids": [observation["id"]], "method": "rate", "summary": "90%"}
    ).json()
    interpretation = client.post(
        f"{base}/interpretations", json={"result_ids": [result["id"]], "outcome": "SUPPORTS", "statement": "Held"}
    ).json()
    _ok(client, pid, eid, "INTERPRETED")
    review = client.post(
        f"{base}/learning-reviews",
        json={"learned": "Buddies sustain attendance", "hypothesis_effect": "Supports", "limitations": ["1 site"]},
    )
    assert review.status_code == 201, review.text
    assert contract_errors("knowledge.LearningReview", _plain(review.json())) == []
    _ok(client, pid, eid, "CLOSED")
    return str(interpretation["id"]), str(review.json()["id"])


def _plain(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if v is not None}


def _item(client: TestClient, pid: str, basis: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    body = {"statement": "Weekly buddy check-ins sustain year-two attendance", "evidence_basis": basis, **extra}
    response = client.post(f"/api/v1/projects/{pid}/knowledge", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def _promote(client: TestClient, pid: str, kid: str, target: str, **extra: Any) -> Any:
    return client.post(f"/api/v1/projects/{pid}/knowledge/{kid}/promote", json={"target": target, **extra})


def _standing(client: TestClient, pid: str, kid: str, action: str, **extra: Any) -> Any:
    return client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/standing", json={"action": action, "reason": action.lower(), **extra}
    )


def _codes(response: Any) -> set[str]:
    return {f["code"] for f in response.json()["error"]["details"]["findings"]}


def item_contract(item: dict[str, Any]) -> dict[str, Any]:
    data = _plain(item)
    for key in ("effective_status", "revalidation_due", "created_at"):
        data.pop(key)
    data["evidence_basis"] = [_plain(b) for b in data["evidence_basis"]]
    data["contrary_evidence"] = [_plain(b) for b in data["contrary_evidence"]]
    return data


def test_learning_to_operating_rule_is_gated_and_human(client: TestClient, session: Session) -> None:
    pid = _project(client)
    first_interpretation, first_review = _closed_experiment(client, pid)
    second_interpretation, _ = _closed_experiment(client, pid)
    item = _item(
        client,
        pid,
        [
            {"entity_type": "ExperimentInterpretation", "entity_id": first_interpretation, "context": "Site A"},
            {"entity_type": "LearningReview", "entity_id": first_review, "context": "Site A"},
        ],
        scope="",
        contexts=["Site A"],
    )
    assert item["stage"] == "PROJECT_FINDING", "knowledge always starts as a project finding"
    assert contract_errors("knowledge.KnowledgeItem", item_contract(item)) == []
    kid = item["id"]

    assert _promote(client, pid, kid, "REPEATED_LOCAL_RESULT").status_code == 409, "one stage at a time"
    assert _promote(client, pid, kid, "LOCAL_RESULT").json()["gate"]["gate"] == "KNOWLEDGE_PROMOTION"
    repeated = _promote(client, pid, kid, "REPEATED_LOCAL_RESULT")
    assert _codes(repeated) == {"repetition.insufficient"}, "two records of one experiment are not a repetition"

    revised = client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/revise",
        json={
            "statement": item["statement"],
            "scope": "Construction apprenticeships",
            "contexts": ["Site A", "Site B"],
            "evidence_basis": item["evidence_basis"]
            + [{"entity_type": "ExperimentInterpretation", "entity_id": second_interpretation, "context": "Site B"}],
            "confidence": "SUPPORTED",
            "reason": "Second site repeated the result",
        },
    )
    assert revised.status_code == 200, revised.text
    assert _promote(client, pid, kid, "REPEATED_LOCAL_RESULT").status_code == 200
    assert _promote(client, pid, kid, "ACCUMULATED_LOCAL_KNOWLEDGE").status_code == 200
    candidate = _promote(client, pid, kid, "CANDIDATE_OPERATING_RULE")
    assert _codes(candidate) == {"contrary.not_searched"}

    client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/revise",
        json={**revised.json(), "contrary_evidence_searched": True, "reason": "Contrary search done"},
    )
    assert _promote(client, pid, kid, "CANDIDATE_OPERATING_RULE").status_code == 200
    rule = _promote(client, pid, kid, "OPERATING_RULE", reason="Adopted for all sites")
    assert rule.status_code == 200 and rule.json()["item"]["stage"] == "OPERATING_RULE"

    versions = client.get(f"/api/v1/projects/{pid}/knowledge/{kid}/versions").json()
    assert [v["change"] for v in versions].count("PROMOTED") == 5
    with pytest.raises(PolicyViolationError):
        knowledge.promote(session, AI, UUID(pid), UUID(kid), PromoteIn(target="OPERATING_RULE"))
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("DELETE FROM knowledge_versions WHERE knowledge_item_id = :id"), {"id": kid})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM knowledge_items WHERE id = :id"), {"id": kid})


def test_standing_changes_are_versioned_and_block_promotion(client: TestClient) -> None:
    pid = _project(client)
    interpretation, _ = _closed_experiment(client, pid)
    kid = _item(client, pid, [{"entity_type": "ExperimentInterpretation", "entity_id": interpretation}])["id"]
    _promote(client, pid, kid, "LOCAL_RESULT")

    assert _standing(client, pid, kid, "CONTEST").json()["status"] == "CONTESTED"
    assert _codes(_promote(client, pid, kid, "REPEATED_LOCAL_RESULT")) >= {"status.not_active"}
    assert _standing(client, pid, kid, "REVALIDATE").status_code == 409, "reinstate contested knowledge first"
    assert _standing(client, pid, kid, "REINSTATE").json()["status"] == "ACTIVE"
    assert _standing(client, pid, kid, "DOWNGRADE", target_stage="LOCAL_RESULT").status_code == 422
    downgraded = _standing(client, pid, kid, "DOWNGRADE", target_stage="PROJECT_FINDING").json()
    assert (downgraded["stage"], downgraded["status"]) == ("PROJECT_FINDING", "DOWNGRADED")
    changes = [v["change"] for v in client.get(f"/api/v1/projects/{pid}/knowledge/{kid}/versions").json()]
    assert changes == ["CREATED", "PROMOTED", "CONTEST", "REINSTATE", "DOWNGRADE"]


def test_time_sensitive_knowledge_must_be_revalidated(client: TestClient, session: Session) -> None:
    pid = _project(client)
    interpretation, _ = _closed_experiment(client, pid)
    basis = [{"entity_type": "ExperimentInterpretation", "entity_id": interpretation}]
    missing_policy = client.post(
        f"/api/v1/projects/{pid}/knowledge",
        json={"statement": "s", "evidence_basis": basis, "temporal_profile": "DYNAMIC"},
    )
    assert missing_policy.status_code == 422
    kid = _item(client, pid, basis, temporal_profile="DYNAMIC", revalidation_interval_days=30)["id"]
    session.execute(
        text("UPDATE knowledge_items SET last_verified_at = now() - interval '90 days' WHERE id = :id"), {"id": kid}
    )

    item = client.get(f"/api/v1/projects/{pid}/knowledge/{kid}").json()
    assert (item["status"], item["effective_status"], item["revalidation_due"]) == (
        "ACTIVE",
        "REVALIDATION_REQUIRED",
        True,
    )
    attention = client.get(f"/api/v1/projects/{pid}/attention").json()
    assert any(a["kind"] == "revalidation" and a["entity_id"] == kid for a in attention)
    assert _codes(_promote(client, pid, kid, "LOCAL_RESULT")) == {"temporal.revalidation_required"}

    high = _project(client, risk="L3_HIGH_IMPACT")
    reuse = f"/api/v1/projects/{pid}/knowledge/{kid}/reuse"
    body = {"target_project_id": high, "transferability": "DIRECTLY_RELEVANT", "rationale": "Same trade"}
    assert client.post(reuse, json=body).status_code == 422, "no high-impact reuse of expired knowledge"

    revalidated = _standing(client, pid, kid, "REVALIDATE", source_version="attendance-2026-09").json()
    assert revalidated["revalidation_due"] is False and revalidated["source_version"] == "attendance-2026-09"
    assert client.post(reuse, json=body).status_code == 201


def test_reuse_is_explicit_labelled_and_never_evidence(client: TestClient, session: Session) -> None:
    pid, other = _project(client), _project(client)
    interpretation, _ = _closed_experiment(client, pid)
    kid = _item(client, pid, [{"entity_type": "ExperimentInterpretation", "entity_id": interpretation}])["id"]
    assert client.get(f"/api/v1/projects/{other}/reused-knowledge").json() == [], "nothing is reused automatically"

    response = client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/reuse",
        json={
            "target_project_id": other,
            "transferability": "ANALOGICAL_ONLY",
            "rationale": "Nursing placements differ in shift structure",
            "differences": "Population and work pattern",
        },
    )
    assert response.status_code == 201, response.text
    [reused] = client.get(f"/api/v1/projects/{other}/reused-knowledge").json()
    assert reused["direct_evidence"] is False and "never direct evidence" in reused["label"]
    assert reused["assessed_by"]["kind"] == "HUMAN"
    contract = {k: reused[k] for k in ("id", "knowledge_item_id", "knowledge_version", "target_project_id")}
    contract |= {k: reused[k] for k in ("transferability", "rationale", "differences", "assessed_by", "created_at")}
    assert contract_errors("knowledge.KnowledgeReuse", contract) == []
    same = client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/reuse",
        json={"target_project_id": pid, "transferability": "DIRECTLY_RELEVANT", "rationale": "r"},
    )
    assert same.status_code == 422

    _standing(client, pid, kid, "SUSPEND")
    suspended = client.post(
        f"/api/v1/projects/{pid}/knowledge/{kid}/reuse",
        json={"target_project_id": other, "transferability": "DIRECTLY_RELEVANT", "rationale": "r"},
    )
    assert suspended.status_code == 422
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE knowledge_reuses SET transferability = 'DIRECTLY_RELEVANT'"))


def test_ai_records_findings_only(client: TestClient, session: Session) -> None:
    pid = _project(client)
    interpretation, _ = _closed_experiment(client, pid)
    finding = knowledge.create_item(
        session,
        AI,
        UUID(pid),
        KnowledgeIn(
            statement="Attendance may depend on buddy pairing",
            evidence_basis=[BasisIn(entity_type="ExperimentInterpretation", entity_id=UUID(interpretation))],
        ),
        ai_action=ACTION,
    )
    assert finding.stage == "PROJECT_FINDING" and finding.provenance["kind"] == "AI_GENERATED"
    foreign = client.post(
        f"/api/v1/projects/{pid}/knowledge",
        json={"statement": "s", "evidence_basis": [{"entity_type": "ExperimentInterpretation", "entity_id": pid}]},
    )
    assert foreign.status_code == 404, "an evidence basis must exist in this project"
