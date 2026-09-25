"""HTTP boundary protections (#55, PRD §68): host allow-list, cross-site refusal, security headers."""

from __future__ import annotations

from fastapi.testclient import TestClient

from research_api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_unknown_host_is_refused_to_defeat_dns_rebinding() -> None:
    response = _client().get("/health/live", headers={"Host": "attacker.example"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "host_not_allowed"


def test_known_hosts_with_ports_are_served() -> None:
    for host in ("localhost:8000", "127.0.0.1:8000", "testserver"):
        assert _client().get("/health/live", headers={"Host": host}).status_code == 200, host


def test_cross_site_writes_are_refused_even_without_a_preflight() -> None:
    client = _client()
    # A multipart form post is a "simple" request: browsers send it cross-site without asking first.
    forged = client.post(
        "/api/v1/packages/import",
        files={"file": ("p.zip", b"PK", "application/zip")},
        headers={"Origin": "https://attacker.example"},
    )
    assert forged.status_code == 403
    assert forged.json()["error"]["code"] == "cross_site_request"
    no_origin = client.post("/api/v1/workspace/purge-expired", headers={"Sec-Fetch-Site": "cross-site"})
    assert no_origin.status_code == 403


def test_reads_and_same_site_writes_are_not_affected() -> None:
    client = _client()
    assert client.get("/health/live", headers={"Origin": "https://attacker.example"}).status_code == 200
    allowed = client.post("/api/v1/projects", json={}, headers={"Origin": "http://localhost:3000"})
    assert allowed.status_code == 422, "reaches validation: the web app's origin is trusted"


def test_security_headers_are_set_on_every_response() -> None:
    response = _client().get("/health/live")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    refused = _client().get("/health/live", headers={"Host": "attacker.example"})
    assert refused.headers["X-Frame-Options"] == "DENY"
