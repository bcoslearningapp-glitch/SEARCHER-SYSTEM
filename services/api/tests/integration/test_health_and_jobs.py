from uuid import uuid4

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from research_api.platform import queue


def test_readiness_with_database(client: TestClient) -> None:
    response = client.get("/health/ready")
    body = response.json()
    assert body["database"] == "ok"
    # Queue may or may not be running locally; missing cloud AI must never fail readiness.
    assert response.status_code == 200
    assert body["status"] in {"ready", "degraded"}


def test_ping_job_dispatch_failure_is_recorded_not_lost(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    def broken_dispatch(task_name: str, job_id: object) -> None:
        raise ConnectionError("broker down")

    monkeypatch.setattr(queue, "dispatch", broken_dispatch)
    response = client.post("/api/v1/system/jobs/ping")
    assert response.status_code == 503
    job_id = response.json()["detail"]["job_id"]

    job = client.get(f"/api/v1/system/jobs/{job_id}").json()
    assert job["state"] == "FAILED"
    assert job["failure_kind"] == "DISPATCH_FAILURE"


def test_ping_job_is_queued_and_cancellable(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    dispatched: list[str] = []
    monkeypatch.setattr(queue, "dispatch", lambda task_name, job_id: dispatched.append(task_name))
    created = client.post("/api/v1/system/jobs/ping")
    assert created.status_code == 202
    job = created.json()
    assert job["state"] == "QUEUED"
    assert dispatched == ["system.ping"]

    cancelled = client.post(f"/api/v1/system/jobs/{job['id']}/cancel").json()
    assert cancelled["state"] == "CANCELLED"
    assert client.get(f"/api/v1/system/jobs/{job['id']}").json()["state"] == "CANCELLED"


def test_unknown_job_is_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/system/jobs/{uuid4()}").status_code == 404
