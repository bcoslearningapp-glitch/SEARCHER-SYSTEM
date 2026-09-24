"""AI gateway: disclosure policy, budgets, output validation and the append-only request log (issue #21)."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import SensitivityLevel
from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_gateway import service as gateway
from research_api.modules.ai_gateway.base import (
    ProviderOutputError,
    ProviderUnavailableError,
    Section,
    StructuredRequest,
)

SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


@pytest.fixture(autouse=True)
def _mock_enabled(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    get_settings.cache_clear()
    registry.reset_cache()
    mock_adapter.register("t.summarise", lambda _r: {"summary": "grounded summary"})
    yield
    mock_adapter.STATE.mode = "ok"
    mock_adapter.STATE.responders.pop("t.summarise", None)
    get_settings.cache_clear()
    registry.reset_cache()


def _project(client: TestClient, sensitivity: str = "NORMAL") -> str:
    body = {"title": "AI", "initial_input": "Q", "input_type": "RAW_QUESTION", "sensitivity": sensitivity}
    response = client.post("/api/v1/projects", json=body)
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _ctx(pid: str, sensitivity: SensitivityLevel = SensitivityLevel.NORMAL) -> gateway.CallContext:
    return gateway.CallContext(UUID(pid), sensitivity, "local-owner", [UUID(pid)])


def _request() -> StructuredRequest:
    return StructuredRequest(
        "t.summarise", "summarise@1", "Summarise the source.", [Section("retrieved_source", "S", "text")], SCHEMA
    )


def _log(client: TestClient, pid: str) -> list[dict[str, object]]:
    response = client.get(f"/api/v1/projects/{pid}/ai-requests")
    assert response.status_code == 200
    return list(response.json())


def test_profiles_never_expose_keys(client: TestClient) -> None:
    profiles = {p["name"]: p for p in client.get("/api/v1/ai/profiles").json()}
    assert profiles["mock"]["configured"] and profiles["mock"]["local"]
    assert profiles["anthropic-default"]["default"]
    assert all("key" not in field for p in profiles.values() for field in p)


def test_successful_call_is_validated_logged_and_carries_provenance(client: TestClient, session: Session) -> None:
    pid = _project(client)
    outcome = gateway.run_structured(session, _ctx(pid), _request(), profile_name="mock")
    assert outcome.result.data == {"summary": "grounded summary"}
    assert outcome.ai_action.template_version == "summarise@1"
    assert outcome.ai_action.supplied_entity_ids == [UUID(pid)]
    [entry] = _log(client, pid)
    assert entry["status"] == "SUCCEEDED"
    assert entry["provider"] == "mock"
    assert entry["entity_ids"] == [pid]
    assert int(str(entry["outbound_chars"])) > 0
    assert entry["id"] == outcome.ai_action.task_id


def test_confidential_project_needs_consent_for_cloud_ai(client: TestClient, session: Session) -> None:
    pid = _project(client, "CONFIDENTIAL")
    ctx = _ctx(pid, SensitivityLevel.CONFIDENTIAL)
    with pytest.raises(gateway.DisclosureBlockedError):
        gateway.run_structured(session, ctx, _request(), profile_name="anthropic-default")
    [entry] = _log(client, pid)
    assert entry["status"] == "BLOCKED"
    assert entry["outbound_chars"] == 0

    consent = {"cloud_consent": True, "reason": "sponsor agreed"}
    assert client.put(f"/api/v1/projects/{pid}/ai-policy", json=consent).status_code == 200
    # Consent clears disclosure; the unconfigured provider then fails as unavailable, not as a policy block.
    with pytest.raises(ProviderUnavailableError):
        gateway.run_structured(session, ctx, _request(), profile_name="anthropic-default")
    assert _log(client, pid)[0]["status"] == "FAILED"


def test_restricted_project_never_uses_cloud_ai_even_with_consent(client: TestClient, session: Session) -> None:
    pid = _project(client, "RESTRICTED")
    client.put(f"/api/v1/projects/{pid}/ai-policy", json={"cloud_consent": True})
    with pytest.raises(gateway.DisclosureBlockedError):
        ctx = _ctx(pid, SensitivityLevel.RESTRICTED)
        gateway.run_structured(session, ctx, _request(), profile_name="openai-default")


def test_budget_exhaustion_stops_as_resource_constraint(client: TestClient, session: Session) -> None:
    pid = _project(client)
    policy = {"cloud_consent": False, "task_budget_usd": "0.0001"}
    assert client.put(f"/api/v1/projects/{pid}/ai-policy", json=policy).status_code == 200
    with pytest.raises(gateway.ResourceConstraintError):
        gateway.run_structured(session, _ctx(pid), _request(), profile_name="anthropic-default")
    [entry] = _log(client, pid)
    assert entry["error_kind"] == gateway.STOPPED_RESOURCE_CONSTRAINT


def test_invalid_structured_output_never_reaches_the_caller(client: TestClient, session: Session) -> None:
    pid = _project(client)
    mock_adapter.register("t.summarise", lambda _r: {"summary": "x", "sql": "DROP TABLE projects"})
    with pytest.raises(ProviderOutputError):
        gateway.run_structured(session, _ctx(pid), _request(), profile_name="mock")
    assert _log(client, pid)[0]["error_kind"] == "INVALID_STRUCTURED_OUTPUT"


def test_policy_allow_list_and_preferred_profile(client: TestClient, session: Session) -> None:
    pid = _project(client)
    bad = client.put(f"/api/v1/projects/{pid}/ai-policy", json={"cloud_consent": False, "allowed_profiles": ["nope"]})
    assert bad.status_code == 422
    ok = client.put(
        f"/api/v1/projects/{pid}/ai-policy",
        json={"cloud_consent": False, "allowed_profiles": ["mock"], "preferred_profile": "mock"},
    )
    assert ok.status_code == 200
    assert gateway.run_structured(session, _ctx(pid), _request()).result.provider == "mock"
    with pytest.raises(gateway.DisclosureBlockedError):
        gateway.run_structured(session, _ctx(pid), _request(), profile_name="openai-default")
    policy = client.get(f"/api/v1/projects/{pid}/ai-policy").json()
    assert Decimal(policy["spent_usd"]) == Decimal(0)
    audit = client.get("/api/v1/audit-events", params={"project_id": pid}).json()
    assert any(e["action"] == "ai_policy.update" for e in audit)


def test_request_log_is_append_only(client: TestClient, session: Session) -> None:
    pid = _project(client)
    gateway.run_structured(session, _ctx(pid), _request(), profile_name="mock")
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE ai_requests SET status = 'X' WHERE project_id = :p"), {"p": pid})


def test_provider_outage_maps_to_503(client: TestClient) -> None:
    from research_api.main import create_app  # noqa: PLC0415

    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise ProviderUnavailableError("down")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"
