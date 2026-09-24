from fastapi.testclient import TestClient

from research_api.contracts.enums import RESEARCH_CORE_VERSION
from research_api.main import create_app


def test_liveness_reports_core_version_without_services() -> None:
    response = TestClient(create_app()).get("/health/live")
    assert response.status_code == 200
    assert response.json()["research_core_version"] == RESEARCH_CORE_VERSION
