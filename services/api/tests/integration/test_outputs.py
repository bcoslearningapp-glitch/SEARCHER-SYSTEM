"""Output composer: traced blocks, protected quotes, immutable versions, human approval (issue #43)."""

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
from research_api.modules.outputs_integrity import service as outputs
from research_api.modules.outputs_integrity.schemas import ApproveIn, OutputIn
from research_api.platform import queue
from tests.integration.test_evidence_hypotheses import _accept, _excerpt
from tests.integration.test_reference import approved_quran  # noqa: F401 - fixture

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="out@1", timestamp=datetime.now(UTC))
PASSAGE = "Mentoring declines sharply in the second year."


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _project_with_evidence(client: TestClient) -> tuple[str, str, str]:
    pid = str(
        client.post("/api/v1/projects", json={"title": "O", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )
    claim = client.post(
        f"/api/v1/projects/{pid}/claims", json={"statement": "Mentoring drops in year two", "claim_type": "OBSERVATION"}
    ).json()
    _, excerpt = _excerpt(client, pid, "Cohort study", PASSAGE)
    _accept(client, pid, ("CLAIM", claim["id"]), "SUPPORTS", excerpt, "SUPPORTED")
    return pid, str(claim["id"]), excerpt


def _create(client: TestClient, pid: str, **extra: Any) -> dict[str, Any]:
    body = {"output_type": "RESEARCH_REPORT", "title": "Year-two report", "language": "en", **extra}
    response = client.post(f"/api/v1/projects/{pid}/outputs", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def test_composed_report_traces_claims_and_protects_quotes(client: TestClient, session: Session) -> None:
    pid, claim_id, excerpt_id = _project_with_evidence(client)
    output = _create(client, pid)
    blocks = output["latest"]["blocks"]
    claim = next(b for b in blocks if b["kind"] == "CLAIM")
    assert claim["trace"] == [{"entity_type": "Claim", "entity_id": claim_id}]
    quote = next(b for b in blocks if b["kind"] == "QUOTE")
    assert quote["quote"]["text"] == PASSAGE and quote["quote"]["excerpt_id"] == excerpt_id
    assert output["latest"]["status"] == "DRAFT"
    assert (
        contract_errors("output.Output", _plain({k: v for k, v in output.items() if k not in {"latest", "created_at"}}))
        == []
    )

    tampered = [dict(b) for b in blocks]
    index = next(i for i, b in enumerate(tampered) if b["kind"] == "QUOTE")
    tampered[index] = {
        **tampered[index],
        "text": "Mentoring collapses in year two.",
        "quote": {**tampered[index]["quote"], "text": "Mentoring collapses in year two."},
    }
    refused = client.post(
        f"/api/v1/projects/{pid}/outputs/{output['id']}/revise", json={"blocks": tampered, "change_reason": "edit"}
    )
    assert refused.status_code == 422, "exact quotes cannot be edited"
    untraced = client.post(
        f"/api/v1/projects/{pid}/outputs/{output['id']}/revise",
        json={"blocks": [{"kind": "CLAIM", "text": "Unsupported claim", "trace": []}], "change_reason": "edit"},
    )
    assert untraced.status_code == 422, "every claim traces to the evidence it rests on"

    edited = [dict(b) for b in blocks]
    edited.insert(0, {"kind": "PARAGRAPH", "text": "This report summarises the pilot.", "trace": []})
    revised = client.post(
        f"/api/v1/projects/{pid}/outputs/{output['id']}/revise", json={"blocks": edited, "change_reason": "Intro"}
    ).json()
    assert revised["current_version"] == 2

    version_id = revised["latest"]["id"]
    approved = client.post(f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{version_id}/approve", json={})
    assert approved.status_code == 200, approved.text
    assert approved.json()["approval"]["approved_by"]["kind"] == "HUMAN"
    version = approved.json()["version"]
    assert contract_errors("output.OutputVersion", _plain({k: v for k, v in version.items() if k != "integrity"})) == []
    versions = client.get(f"/api/v1/projects/{pid}/outputs/{output['id']}/versions").json()
    assert [(v["version_number"], v["status"]) for v in versions] == [(1, "SUPERSEDED"), (2, "APPROVED")]

    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE output_versions SET blocks = '[]' WHERE id = :id"), {"id": version_id})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM output_versions WHERE id = :id"), {"id": version_id})


def test_recompose_is_a_new_draft_and_old_approval_stays_until_replaced(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid, output_type="EVIDENCE_MAP", mode="AUDIT")
    first = output["latest"]["id"]
    client.post(f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{first}/approve", json={})
    client.post(f"/api/v1/projects/{pid}/claims", json={"statement": "Pay plateaus", "claim_type": "OBSERVATION"})
    refreshed = client.post(f"/api/v1/projects/{pid}/outputs/{output['id']}/recompose").json()
    assert refreshed["current_version"] == 2
    assert any(b["text"] == "Pay plateaus" for b in refreshed["latest"]["blocks"])
    statuses = [v["status"] for v in client.get(f"/api/v1/projects/{pid}/outputs/{output['id']}/versions").json()]
    assert statuses == ["APPROVED", "DRAFT"]
    stale = client.post(f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{first}/approve", json={})
    assert stale.status_code == 409


def test_subject_outputs_need_a_subject_and_every_type_composes(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    missing = client.post(f"/api/v1/projects/{pid}/outputs", json={"output_type": "HYPOTHESIS_DOSSIER", "title": "t"})
    assert missing.status_code == 422
    hid = client.post(
        f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "Mentoring matters"}}
    ).json()["id"]
    dossier = _create(client, pid, output_type="HYPOTHESIS_DOSSIER", subject_id=hid, language="ar")
    assert dossier["subject_type"] == "Hypothesis"
    assert dossier["latest"]["blocks"][0]["text"] == "الفرضيات"
    for output_type in (
        "EXECUTIVE_SUMMARY",
        "DECISION_BRIEF",
        "REFERENCE_REVIEW",
        "DESIGN_SPECIFICATION",
        "CLOSURE_REPORT",
    ):
        _create(client, pid, output_type=output_type, language="fr")


def test_ai_drafts_but_only_a_human_approves(client: TestClient, session: Session) -> None:
    pid, _, _ = _project_with_evidence(client)
    draft = outputs.create_output(
        session, AI, UUID(pid), OutputIn(output_type="RESEARCH_REPORT", title="AI draft"), ai_action=ACTION
    )
    assert draft.provenance["kind"] == "AI_GENERATED"
    with pytest.raises(PolicyViolationError):
        outputs.approve(session, AI, UUID(pid), draft.id, draft.latest.id, ApproveIn())


def test_quran_quotes_come_from_the_approved_text(client: TestClient, approved_quran: dict[str, Any]) -> None:  # noqa: F811
    pid = str(
        client.post("/api/v1/projects", json={"title": "Q", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )
    hid = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h"}}).json()["id"]
    review = client.post(
        f"/api/v1/projects/{pid}/reference-reviews",
        json={
            "target_type": "HYPOTHESIS",
            "target_id": hid,
            "question": "Q?",
            "analytical_category": "VALUES_AND_EVALUATIVE_STANDARDS",
        },
    ).json()
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{review['id']}/entries",
        json={"layer": "SOURCE_TEXT", "quran_ref": "1:2"},
    )
    output = _create(client, pid, output_type="REFERENCE_REVIEW", language="ar")
    [quote] = [b for b in output["latest"]["blocks"] if b["kind"] == "QUOTE"]
    assert {k: v for k, v in quote["quote"].items() if v is not None} == {
        "source_kind": "QURAN",
        "quran_ref": "1:2",
        "text": "PLACEHOLDER-V1-1-2",
        "language": "ar",
    }
    approved = client.post(
        f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{output['latest']['id']}/approve", json={}
    )
    assert approved.status_code == 200, approved.text
