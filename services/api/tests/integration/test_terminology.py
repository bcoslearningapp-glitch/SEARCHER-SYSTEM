"""Canonical terminology and the translation integrity check (issue #36, PRD §36)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import Principal, ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.knowledge_memory import terminology
from research_api.modules.knowledge_memory.terminology_schemas import TermDecision, TermIn

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="t@1", timestamp=datetime.now(UTC))
RESEARCHER = Principal(ActorKind.HUMAN, "researcher", frozenset({ActorRole.RESEARCHER}))


def _term(client: TestClient, **extra: Any) -> dict[str, Any]:
    domain = extra.pop("domain", f"test-{uuid4().hex[:8]}")
    body = {
        "term": "maqasid al-sharia",
        "original_language": "en",
        "domain": domain,
        "definition": "The higher objectives of the Sharia",
        "translations": {"ar": "مقاصد الشريعة", "fr": "finalités de la charia"},
        "alternatives": [{"language": "fr", "text": "objectifs de la charia"}],
        "retain_original": True,
        **extra,
    }
    response = client.post("/api/v1/terminology", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def _approve(client: TestClient, term_id: str) -> dict[str, Any]:
    response = client.post(f"/api/v1/terminology/{term_id}/approve", json={"reason": "steward review"})
    assert response.status_code == 200, response.text
    return dict(response.json())


def _check(client: TestClient, source: str, src: str, translation: str, dst: str, domain: str | None = None) -> Any:
    body = {"source_text": source, "source_language": src, "translated_text": translation, "target_language": dst}
    return client.post("/api/v1/integrity/translation-check", json=body | ({"domain": domain} if domain else {})).json()


def test_canonical_form_is_human_approved_and_versioned(client: TestClient, session: Session) -> None:
    proposed = _term(client)
    assert proposed["status"] == "PROPOSED" and proposed["translations"]["en"] == "maqasid al-sharia"
    approved = _approve(client, proposed["id"])
    assert approved["approved_by"]["kind"] == "HUMAN"
    assert contract_errors("terminology.Term", approved_contract(approved)) == []

    revised = client.post(
        f"/api/v1/terminology/{approved['id']}/revise",
        json={**proposed, "definition": "The objectives the Sharia protects", "change_reason": "Steward wording"},
    ).json()
    assert (revised["version_number"], revised["status"]) == (2, "PROPOSED")
    current = client.get("/api/v1/terminology", params={"domain": proposed["domain"], "status": "APPROVED"}).json()
    assert [t["id"] for t in current] == [approved["id"]], "the approved version stays canonical until replaced"
    _approve(client, revised["id"])
    history = client.get(f"/api/v1/terminology/{revised['id']}/history").json()
    assert [(t["version_number"], t["status"]) for t in history] == [(1, "SUPERSEDED"), (2, "APPROVED")]
    assert client.post(f"/api/v1/terminology/{revised['id']}/approve", json={}).status_code == 409

    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE terms SET definition = 'edited' WHERE id = :id"), {"id": revised["id"]})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM terms WHERE id = :id"), {"id": revised["id"]})


def approved_contract(term: dict[str, Any]) -> dict[str, Any]:
    data = {k: v for k, v in term.items() if v is not None}
    for key in ("change_reason", "approved_by", "approved_at", "created_at"):
        data.pop(key, None)
    data["translations"] = {k: v for k, v in data["translations"].items() if v is not None}
    data["alternatives"] = [{k: v for k, v in a.items() if v is not None} for a in data["alternatives"]]
    return data


def test_ai_and_researchers_propose_only_stewards_approve(session: Session) -> None:
    body = TermIn(term="retention", original_language="en", domain="hr", definition="Staying in the programme")
    proposed = terminology.propose_term(session, AI, body, ai_action=ACTION)
    assert proposed.provenance["kind"] == "AI_GENERATED"
    for principal in (AI, RESEARCHER):
        with pytest.raises(PolicyViolationError):
            terminology.approve_term(session, principal, proposed.id, TermDecision())


def test_translation_check_flags_strength_drift_and_terminology(client: TestClient) -> None:
    term = _term(client)
    _approve(client, term["id"])
    domain = term["domain"]

    clean = _check(
        client,
        "Maqasid al-sharia may be associated with policy choices.",
        "en",
        "Les finalités de la charia pourraient être associées aux choix politiques.",
        "fr",
        domain,
    )
    assert clean["passed"] is True and clean["terminology"][0]["found"] is True

    drifted = _check(
        client,
        "Maqasid al-sharia may be associated with policy choices.",
        "en",
        "Les buts de la loi entraînent les choix politiques.",
        "fr",
        domain,
    )
    assert drifted["passed"] is False
    assert {(d["axis"], d["direction"]) for d in drifted["strength_drift"]} == {
        ("relation", "STRENGTHENED"),
        ("certainty", "STRENGTHENED"),
    }
    [finding] = drifted["terminology"]
    assert finding["found"] is False and "maqasid al-sharia" in finding["expected"], "retain-original is acceptable"

    arabic = _check(client, "Mentoring is linked to retention.", "en", "الإرشاد يسبب الاستبقاء.", "ar")
    assert arabic["strength_drift"][0]["message"].startswith("The translation states a stronger relation")
