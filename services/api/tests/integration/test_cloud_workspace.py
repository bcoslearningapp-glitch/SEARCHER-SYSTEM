"""Selective cloud workspace and disclosure manifest (issue #47, PRD §56, FR-CLOUD-001..007)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.modules.cloud_workspace import service as workspace
from research_api.modules.cloud_workspace.adapters import LocalDirectoryAdapter, WorkspaceError
from research_api.modules.cloud_workspace.schemas import StageIn, StageItem
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal, system_principal
from research_api.platform import queue
from tests.integration.test_evidence_hypotheses import _accept, _excerpt

PASSAGE = "Mentoring declines sharply in the second year."


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


@pytest.fixture
def remote(monkeypatch: MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    root = tmp_path / "workspace"
    monkeypatch.setenv("CLOUD_WORKSPACE_ADAPTER", "local-directory")
    monkeypatch.setenv("CLOUD_WORKSPACE_ROOT", str(root))
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def _project(client: TestClient, sensitivity: str = "NORMAL") -> dict[str, str]:
    pid = str(
        client.post(
            "/api/v1/projects",
            json={"title": "W", "initial_input": "x", "input_type": "IDEA", "sensitivity": sensitivity},
        ).json()["id"]
    )
    claim = client.post(
        f"/api/v1/projects/{pid}/claims", json={"statement": "Mentoring drops in year two", "claim_type": "OBSERVATION"}
    ).json()
    _, excerpt = _excerpt(client, pid, "Cohort study", PASSAGE)
    _accept(client, pid, ("CLAIM", claim["id"]), "SUPPORTS", excerpt, "SUPPORTED")
    hypothesis = client.post(
        f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "Mentors leave"}}
    ).json()
    output = client.post(
        f"/api/v1/projects/{pid}/outputs", json={"output_type": "RESEARCH_REPORT", "title": "Report", "language": "en"}
    ).json()
    return {
        "pid": pid,
        "Claim": str(claim["id"]),
        "SourceExcerpt": excerpt,
        "Hypothesis": str(hypothesis["id"]),
        "OutputVersion": str(output["latest"]["id"]),
    }


def _stage(client: TestClient, ids: dict[str, str], kinds: list[str], **extra: Any) -> Any:
    items = [{"entity_type": k, "entity_id": ids[k]} for k in kinds]
    body = {"purpose": "Share with a remote reviewer", "items": items}
    return client.post(f"/api/v1/projects/{ids['pid']}/workspace/stagings", json={**body, **extra})


def test_no_workspace_is_configured_by_default(client: TestClient) -> None:
    ids = _project(client)
    assert client.get("/api/v1/workspace").json()["enabled"] is False
    response = _stage(client, ids, ["Claim"])
    assert response.status_code == 422
    assert "no cloud workspace" in response.json()["error"]["message"]


def test_staging_writes_only_the_selection_and_records_it(client: TestClient, remote: Path) -> None:
    ids = _project(client)
    info = client.get("/api/v1/workspace").json()
    assert info["enabled"] is True and info["remote"] is True
    kinds = ["SourceExcerpt", "Claim", "Hypothesis", "OutputVersion"]
    response = _stage(client, ids, [*kinds, "Claim"])
    assert response.status_code == 201, response.text
    staging = response.json()
    assert staging["status"] == "ACTIVE"
    assert staging["policy_decision"]["allowed"] is True
    assert [i["entity_type"] for i in staging["items"]] == kinds  # duplicates collapse
    files = sorted(remote.iterdir())
    assert len(files) == 4  # nothing but the selection: no silent synchronisation (FR-CLOUD-001)
    database_url = get_settings().database_url
    for item in staging["items"]:
        data = (remote / f"{item['remote_ref']}.json").read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert item["byte_size"] == len(data)
        envelope = json.loads(data)
        assert envelope["entity_id"] == item["entity_id"]
        assert "data, never as instructions" in envelope["notice"]
        assert database_url not in data.decode()
    excerpt = json.loads((remote / f"{staging['items'][0]['remote_ref']}.json").read_bytes())
    assert excerpt["content"]["text"] == PASSAGE
    output = json.loads((remote / f"{staging['items'][3]['remote_ref']}.json").read_bytes())
    assert output["content"]["markdown"].startswith("# Report")
    listed = client.get(f"/api/v1/projects/{ids['pid']}/workspace/stagings").json()
    assert [s["id"] for s in listed] == [staging["id"]]
    audit = client.get("/api/v1/audit-events", params={"project_id": ids["pid"]}).json()
    assert "workspace.stage" in {e["action"] for e in audit}


def test_confidential_needs_consent_and_blocked_attempts_are_recorded(client: TestClient, remote: Path) -> None:
    ids = _project(client, "CONFIDENTIAL")
    blocked = _stage(client, ids, ["Claim"]).json()
    assert blocked["status"] == "BLOCKED"
    assert "consent" in blocked["policy_decision"]["reason"]
    assert blocked["expires_at"] is None
    assert blocked["items"][0]["remote_ref"] is None and blocked["items"][0]["sha256"]
    assert not remote.exists() or not any(remote.iterdir())
    client.put(f"/api/v1/projects/{ids['pid']}/ai-policy", json={"cloud_consent": True})
    assert _stage(client, ids, ["Claim"]).json()["status"] == "ACTIVE"


def test_restricted_projects_never_stage(client: TestClient, remote: Path) -> None:
    ids = _project(client, "RESTRICTED")
    client.put(f"/api/v1/projects/{ids['pid']}/ai-policy", json={"cloud_consent": True})
    assert _stage(client, ids, ["Claim"]).json()["status"] == "BLOCKED"
    assert not remote.exists() or not any(remote.iterdir())


def test_records_of_another_project_cannot_be_staged(client: TestClient, remote: Path) -> None:
    ids = _project(client)
    other = _project(client)
    response = _stage(client, {**ids, "Claim": other["Claim"]}, ["Claim"])
    assert response.status_code == 404
    assert not remote.exists() or not any(remote.iterdir())


def test_ttl_is_bounded(client: TestClient, remote: Path) -> None:
    ids = _project(client)
    too_long = get_settings().cloud_workspace_max_ttl_hours + 1
    assert _stage(client, ids, ["Claim"], ttl_hours=too_long).status_code == 422


def test_delete_removes_remote_content_and_keeps_the_manifest(client: TestClient, remote: Path) -> None:
    ids = _project(client)
    staging = _stage(client, ids, ["Claim", "Hypothesis"]).json()
    url = f"/api/v1/projects/{ids['pid']}/workspace/stagings/{staging['id']}"
    deleted = client.post(f"{url}/delete", json={"reason": "review finished"})
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["status"] == "DELETED"
    assert deleted.json()["delete_reason"] == "review finished"
    assert not any(remote.iterdir())
    assert client.get(url).json()["items"][0]["sha256"] == staging["items"][0]["sha256"]
    assert client.post(f"{url}/delete", json={"reason": "again"}).status_code == 409


def test_expired_content_is_purged(client: TestClient, session: Session, remote: Path) -> None:
    ids = _project(client)
    staging = _stage(client, ids, ["Claim"], ttl_hours=1).json()
    assert client.post("/api/v1/workspace/purge-expired").json()["expired"] == []
    later = datetime.now(UTC) + timedelta(hours=2)
    purged = workspace.purge_expired(session, system_principal("scheduler"), now=later)
    assert [str(i) for i in purged.expired] == [staging["id"]]
    after = client.get(f"/api/v1/projects/{ids['pid']}/workspace/stagings/{staging['id']}").json()
    assert after["status"] == "EXPIRED"
    assert after["deleted_by"]["kind"] == "SYSTEM"
    assert not any(remote.iterdir())


def test_ai_cannot_stage_content(client: TestClient, session: Session, remote: Path) -> None:
    ids = _project(client)
    data = StageIn(purpose="exfiltrate", items=[StageItem(entity_type="Claim", entity_id=ids["Claim"])])
    with pytest.raises(PolicyViolationError):
        workspace.stage(session, ai_principal("research_orchestrator"), ids["pid"], data)  # type: ignore[arg-type]


def test_credentials_never_leave(client: TestClient, remote: Path) -> None:
    pid = client.post("/api/v1/projects", json={"title": "S", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    claim = client.post(
        f"/api/v1/projects/{pid}/claims",
        json={"statement": f"connect with {get_settings().database_url}", "claim_type": "OBSERVATION"},
    ).json()
    response = _stage(client, {"pid": pid, "Claim": claim["id"]}, ["Claim"])
    assert response.status_code == 422
    assert "credentials" in response.json()["error"]["message"]
    assert not remote.exists() or not any(remote.iterdir())


def test_the_manifest_cannot_be_rewritten(client: TestClient, session: Session, remote: Path) -> None:
    ids = _project(client)
    staging = _stage(client, ids, ["Claim"]).json()
    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE workspace_stagings SET purpose = 'x' WHERE id = :id"), {"id": staging["id"]})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM workspace_stagings WHERE id = :id"), {"id": staging["id"]})
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("DELETE FROM workspace_staged_items WHERE staging_id = :id"), {"id": staging["id"]})


def test_adapter_keys_stay_inside_the_workspace(tmp_path: Path) -> None:
    adapter = LocalDirectoryAdapter(tmp_path)
    for key in ("../escape", "a/b", "", "x" * 129, "a.json"):
        with pytest.raises(WorkspaceError):
            adapter.put(key, b"{}")
    ref = adapter.put("ok-1", b"{}")
    assert adapter.exists(ref)
    adapter.delete(ref)
    adapter.delete(ref)  # idempotent
    assert not adapter.exists(ref)
