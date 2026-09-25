"""Source identity, uploads, reverification, Hybrid Source Access, leads, attention (issue #5)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import Principal, ai_principal
from research_api.modules.sources_library import service
from research_api.modules.sources_library.schemas import CatalogIn
from research_api.platform import queue
from tests.contract_helpers import as_contract
from tests.pdf_fixtures import make_pdf

PHYSICAL_BOOK = {
    "work": {
        "title": "Muqaddimah",
        "authors": ["Ibn Khaldun"],
        "original_language": "ar",
        "authority_layer": "HISTORICAL_CIVILIZATIONAL",
    },
    "edition": {
        "edition_label": "Rosenthal translation",
        "language": "en",
        "identifiers": [{"scheme": "ISBN", "value": "9780691017549"}],
    },
    "holding": {"access_mode": "PHYSICAL", "note": "Shelf 3"},
}


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> list[str]:
    dispatched: list[str] = []
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: dispatched.append(task))
    return dispatched


def _project(client: TestClient) -> str:
    return str(
        client.post("/api/v1/projects", json={"title": "S", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )


def _catalog(client: TestClient, body: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    response = client.post("/api/v1/sources", json={**(body or PHYSICAL_BOOK), **extra})
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_physical_book_is_metadata_only_and_unavailable(client: TestClient) -> None:
    work = _catalog(client)
    edition = work["editions"][0]
    assert edition["verification_state"] == "METADATA_ONLY"
    assert edition["available"] is False
    [holding] = edition["assets"]
    assert holding["access_mode"] == "PHYSICAL"
    assert holding["available_in_environment"] is False
    assert (
        contract_errors("source-identity.SourceWork", as_contract(work, drop=frozenset({"editions", "created_at"})))
        == []
    )
    assert (
        contract_errors("source-identity.SourceEdition", as_contract(edition, drop=frozenset({"assets", "available"})))
        == []
    )
    asset_contract = as_contract(
        holding, drop=frozenset({"holding_note", "ingestion_status", "created_at", "original_filename"})
    )
    assert contract_errors("source-identity.SourceAsset", asset_contract) == []


def test_foundational_sources_need_constitutional_authority(client: TestClient, session: Session) -> None:
    quran = {**PHYSICAL_BOOK, "work": {"title": "Qur'an", "authority_layer": "QURAN"}}
    researcher = Principal(ActorKind.HUMAN, "r", frozenset({ActorRole.RESEARCHER}))
    with pytest.raises(PolicyViolationError):
        service.catalog(session, researcher, CatalogIn.model_validate(quran))
    with pytest.raises(PolicyViolationError):
        service.catalog(session, ai_principal("orchestrator"), CatalogIn.model_validate(quran))
    assert client.post("/api/v1/sources", json=quran).status_code == 201  # local owner holds the role


def test_upload_makes_available_but_does_not_raise_verification(client: TestClient, _no_broker: list[str]) -> None:
    edition_id = _catalog(client)["editions"][0]["id"]
    upload = client.post(
        f"/api/v1/sources/editions/{edition_id}/assets",
        files={"file": ("../../evil.pdf", make_pdf(["Asabiyya weakens over generations."]), "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    asset = upload.json()
    assert asset["kind"] == "PDF"
    assert asset["access_mode"] == "DIRECT_DIGITAL"
    assert asset["available_in_environment"] is True
    assert asset["original_filename"] == "evil.pdf"
    assert asset["ingestion_status"] == "QUEUED"
    assert _no_broker == ["sources.ingest_asset"]
    edition = client.get(f"/api/v1/sources/editions/{edition_id}").json()
    assert edition["verification_state"] == "METADATA_ONLY"
    assert edition["available"] is True


def test_upload_rejects_disguised_executables(client: TestClient) -> None:
    edition_id = _catalog(client)["editions"][0]["id"]
    response = client.post(
        f"/api/v1/sources/editions/{edition_id}/assets",
        files={"file": ("book.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")},
    )
    assert response.status_code == 415


def test_reverification_is_explicit_and_audited(client: TestClient) -> None:
    edition_id = _catalog(client)["editions"][0]["id"]
    response = client.post(
        f"/api/v1/sources/editions/{edition_id}/reverify",
        json={"verification_state": "RESEARCHER_SUPPLIED_EXACT", "method": "Checked against physical copy"},
    )
    assert response.json()["verification_state"] == "RESEARCHER_SUPPLIED_EXACT"
    actions = [e["action"] for e in client.get("/api/v1/audit-events").json()]
    assert "source.reverify" in actions


def test_hybrid_access_flow_preserves_correct_verification(client: TestClient, session: Session) -> None:
    pid = _project(client)
    edition_id = _catalog(client)["editions"][0]["id"]
    request = client.post(
        f"/api/v1/projects/{pid}/access-requests",
        json={
            "edition_id": edition_id,
            "reason": "Need the passage on asabiyya decay",
            "requested_scope": "Chapter 2, sections 10-12",
            "acceptable_forms": ["EXACT_TEXT", "RESEARCHER_SUMMARY"],
            "priority": "HIGH",
        },
    ).json()
    assert request["status"] == "OPEN"
    assert (
        contract_errors("source-identity.SourceAccessRequest", as_contract(request, drop=frozenset({"created_at"})))
        == []
    )

    attention = client.get(f"/api/v1/projects/{pid}/attention").json()
    assert any(item["kind"] == "source_access_request" for item in attention)

    not_accepted = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses",
        json={"form": "RESEARCHER_ATTESTATION", "location": "p. 1", "text": "x"},
    )
    assert not_accepted.status_code == 422

    exact = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses",
        json={"form": "EXACT_TEXT", "location": "vol. 1, p. 278", "text": "Exact words typed from the book."},
    ).json()
    assert exact["request"]["status"] == "PARTIALLY_FULFILLED"
    assert exact["excerpt"]["verification_state"] == "RESEARCHER_SUPPLIED_EXACT"
    assert exact["excerpt"]["is_exact_quote"] is True
    assert (
        contract_errors("source-identity.SourceExcerpt", as_contract(exact["excerpt"], drop=frozenset({"created_at"})))
        == []
    )

    summary = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses",
        json={
            "form": "RESEARCHER_SUMMARY",
            "location": "ch. 2 §12",
            "text": "He argues cohesion decays.",
            "fulfills_request": True,
        },
    ).json()
    assert summary["excerpt"]["verification_state"] == "RESEARCHER_REPORTED_SOURCE_CONTENT"
    assert summary["excerpt"]["is_exact_quote"] is False
    assert summary["request"]["status"] == "FULFILLED"

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(
            text("UPDATE source_excerpts SET text = 'edited' WHERE id = :id"), {"id": exact["excerpt"]["id"]}
        )


def test_page_images_create_researcher_mediated_asset(client: TestClient) -> None:
    pid = _project(client)
    edition_id = _catalog(client)["editions"][0]["id"]
    request = client.post(
        f"/api/v1/projects/{pid}/access-requests",
        json={"edition_id": edition_id, "reason": "r", "requested_scope": "p. 5", "acceptable_forms": ["PAGE_IMAGES"]},
    ).json()
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    response = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses/file",
        data={"form": "PAGE_IMAGES", "fulfills_request": "true"},
        files={"file": ("p5.png", png, "image/png")},
    )
    assert response.status_code == 200, response.text
    asset = response.json()["asset"]
    assert asset["kind"] == "SCAN"
    assert asset["access_mode"] == "RESEARCHER_MEDIATED"
    assert asset["ingestion_status"] == "NOT_APPLICABLE"


def test_source_lead_needs_an_excerpt_to_become_verified(client: TestClient, session: Session) -> None:
    pid = _project(client)
    lead = client.post(
        f"/api/v1/projects/{pid}/source-leads", json={"statement": "I remember Ibn Khaldun said cohesion decays"}
    ).json()
    assert lead["status"] == "SOURCE_LEAD"
    with pytest.raises(DBAPIError, match="verified_has_excerpt"), session.begin_nested():
        session.execute(text("UPDATE source_leads SET status = 'VERIFIED' WHERE id = :id"), {"id": lead["id"]})

    edition_id = _catalog(client)["editions"][0]["id"]
    request = client.post(
        f"/api/v1/projects/{pid}/access-requests",
        json={
            "edition_id": edition_id,
            "reason": "verify lead",
            "requested_scope": "ch. 2",
            "acceptable_forms": ["EXACT_TEXT"],
        },
    ).json()
    excerpt = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses",
        json={"form": "EXACT_TEXT", "location": "p. 9", "text": "The exact passage."},
    ).json()["excerpt"]
    verified = client.post(
        f"/api/v1/projects/{pid}/source-leads/{lead['id']}/verify", json={"excerpt_id": excerpt["id"]}
    ).json()
    assert verified["status"] == "VERIFIED"
    assert contract_errors("source-identity.SourceLead", as_contract(verified, drop=frozenset({"created_at"}))) == []


def test_closed_projects_cannot_request_sources(client: TestClient) -> None:
    pid = _project(client)
    client.post(f"/api/v1/projects/{pid}/transition", json={"target": "ON_HOLD"})
    edition_id = _catalog(client)["editions"][0]["id"]
    response = client.post(
        f"/api/v1/projects/{pid}/access-requests",
        json={"edition_id": edition_id, "reason": "r", "requested_scope": "s", "acceptable_forms": ["EXACT_TEXT"]},
    )
    assert response.status_code == 409


def test_project_library_listing(client: TestClient) -> None:
    pid = _project(client)
    _catalog(client, project_id=pid)
    _catalog(client)
    assert len(client.get("/api/v1/sources", params={"project_id": pid}).json()) == 1


def test_library_listing_pages_are_stable_and_complete(client: TestClient) -> None:
    pid = _project(client)
    created = [_catalog(client, project_id=pid)["id"] for _ in range(5)]
    everything = [w["id"] for w in client.get("/api/v1/sources", params={"project_id": pid}).json()]
    assert everything == created[::-1], "newest first, and no limit returns every work"
    pages = [
        [w["id"] for w in client.get("/api/v1/sources", params={"project_id": pid, "limit": 2, "offset": o}).json()]
        for o in (0, 2, 4)
    ]
    assert [len(p) for p in pages] == [2, 2, 1]
    assert [i for p in pages for i in p] == everything, "pages neither skip nor repeat a work"
    assert client.get("/api/v1/sources", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/sources", params={"limit": 201}).status_code == 422
