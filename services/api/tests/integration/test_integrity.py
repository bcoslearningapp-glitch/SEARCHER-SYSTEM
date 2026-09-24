"""Eight-step output integrity pipeline (issue #44, FR-OUT-002/003)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from research_api.contracts.enums import OutputMode
from research_api.contracts.schemas import contract_errors
from research_api.modules.outputs_integrity import render
from research_api.modules.outputs_integrity.schemas import Block
from research_api.platform import queue
from tests.integration.test_evidence_hypotheses import _excerpt
from tests.integration.test_outputs import PASSAGE, _create, _plain, _project_with_evidence

STEPS = [
    "CLAIM_VERIFICATION",
    "CITATION_VERIFICATION",
    "EXACT_QUOTE_VERIFICATION",
    "REFERENCE_INTEGRITY",
    "TERMINOLOGY_CHECK",
    "TRANSLATION_SEMANTIC_CHECK",
    "LANGUAGE_EDITING",
    "FINAL_RENDERING",
]


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _run(client: TestClient, pid: str, output: dict[str, Any]) -> dict[str, Any]:
    url = f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{output['latest']['id']}/integrity"
    response = client.post(url)
    assert response.status_code == 200, response.text
    return dict(response.json())


def _revise(client: TestClient, pid: str, output: dict[str, Any], blocks: list[dict[str, Any]]) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{pid}/outputs/{output['id']}/revise", json={"blocks": blocks, "change_reason": "edit"}
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def _approve(client: TestClient, pid: str, output: dict[str, Any], **extra: Any) -> Any:
    url = f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{output['latest']['id']}/approve"
    return client.post(url, json=extra)


def _statuses(run: dict[str, Any]) -> dict[str, str]:
    return {s["step"]: s["status"] for s in run["steps"]}


def test_clean_output_is_verified_in_eight_ordered_steps(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid)
    run = _run(client, pid, output)
    assert [s["step"] for s in run["steps"]] == STEPS
    assert run["status"] == "VERIFIED"
    assert _statuses(run)["TERMINOLOGY_CHECK"] == "SKIPPED", "nothing was reworded"
    assert contract_errors("output.IntegrityRun", _plain(run)) == []
    approved = _approve(client, pid, output)
    assert approved.status_code == 200 and approved.json()["integrity"]["status"] == "VERIFIED"
    assert client.get(f"/api/v1/projects/{pid}/outputs/{output['id']}").json()["latest"]["integrity"] == "VERIFIED"


def test_candidate_evidence_cannot_be_cited_and_blocks_approval(client: TestClient) -> None:
    pid, claim_id, _ = _project_with_evidence(client)
    _, excerpt = _excerpt(client, pid, "Second study", "Another passage.")
    candidate = client.post(
        f"/api/v1/projects/{pid}/evidence",
        json={
            "target_type": "CLAIM",
            "target_id": claim_id,
            "role": "SUPPORTS",
            "finding": "unreviewed",
            "excerpt_id": excerpt,
        },
    ).json()
    output = _create(client, pid)
    blocks = output["latest"]["blocks"] + [
        {"kind": "EVIDENCE", "text": "unreviewed", "trace": [{"entity_type": "Evidence", "entity_id": candidate["id"]}]}
    ]
    output = _revise(client, pid, output, blocks)
    run = _run(client, pid, output)
    assert run["status"] == "FAILED" and _statuses(run)["CITATION_VERIFICATION"] == "FAIL"
    refused = _approve(client, pid, output, reason="ship it", acknowledge_warnings=True)
    assert refused.status_code == 422, "a FAILED version cannot be approved, even with an acknowledgement"


def test_reworded_claim_is_screened_for_strength_drift(client: TestClient) -> None:
    pid = str(
        client.post("/api/v1/projects", json={"title": "D", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )
    claim = client.post(
        f"/api/v1/projects/{pid}/claims",
        json={"statement": "Mentoring is associated with higher retention", "claim_type": "OBSERVATION"},
    ).json()
    output = _create(client, pid, output_type="EXECUTIVE_SUMMARY", language="fr")
    blocks = [
        {
            "kind": "CLAIM",
            "text": "Le mentorat entraîne une meilleure rétention",
            "trace": [{"entity_type": "Claim", "entity_id": claim["id"]}],
        }
    ]
    output = _revise(client, pid, output, blocks)
    run = _run(client, pid, output)
    steps = {s["step"]: s for s in run["steps"]}
    assert run["status"] == "VERIFIED_WITH_WARNINGS"
    assert steps["TRANSLATION_SEMANTIC_CHECK"]["findings"][0]["code"] == "strength.relation"
    assert {f["code"] for f in steps["CLAIM_VERIFICATION"]["findings"]} >= {"claim.reworded", "claim.weak"}

    assert _approve(client, pid, output).status_code == 422, "warnings need a person's decision"
    approved = _approve(client, pid, output, reason="Wording reviewed with the author", acknowledge_warnings=True)
    assert approved.status_code == 200, approved.text
    assert approved.json()["approval"]["methodology_path"] == "OVERRIDDEN_WITH_REASON"


def test_inference_is_never_shown_as_source_text(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid)
    blocks = output["latest"]["blocks"] + [
        {"kind": "PARAGRAPH", "text": "What the verse means", "label": "SOURCE_TEXT", "trace": []}
    ]
    run = _run(client, pid, _revise(client, pid, output, blocks))
    assert _statuses(run)["REFERENCE_INTEGRITY"] == "FAIL"


def test_rendering_keeps_quotes_verbatim_with_references(client: TestClient, session: Session) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid)
    blocks = [Block.model_validate(b) for b in output["latest"]["blocks"]]
    doc = render.Document("Report", "ar", OutputMode.REFERENCED, blocks, 1, "DRAFT")
    md = render.markdown(session, UUID(pid), doc)
    assert f"> {PASSAGE}" in md and "Cohort study" in md and "## المراجع" in md
    page = render.html_document(session, UUID(pid), doc)
    assert 'dir="rtl"' in page and PASSAGE in page


def test_export_markdown_and_html_carry_integrity(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid, language="ar")
    base = f"/api/v1/projects/{pid}/outputs/{output['id']}/versions/{output['latest']['id']}/export"
    draft = client.get(base, params={"format": "md"})
    assert draft.status_code == 200 and draft.headers["content-type"].startswith("text/markdown")
    assert f"> {PASSAGE}" in draft.text and "NOT_CHECKED" in draft.text, "an unchecked draft says so"
    assert 'attachment; filename="output-' in draft.headers["content-disposition"]

    _approve(client, pid, output)
    approved = client.get(base, params={"format": "html"})
    assert approved.headers["content-type"].startswith("text/html")
    assert 'dir="rtl"' in approved.text and PASSAGE in approved.text and "VERIFIED" not in approved.text
    assert client.get(base, params={"format": "exe"}).status_code == 422
