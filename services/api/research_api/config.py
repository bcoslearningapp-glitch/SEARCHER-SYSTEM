"""Application configuration.

Secrets are `SecretStr` so they never appear in reprs or logs (PRD §68 SEC-003).
Provider keys are optional: the product must stay usable without cloud AI
(PRD §3.1 goal 15, NFR-REL-001).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://research:research@localhost:5432/research"
    redis_url: str = "redis://localhost:6379/0"

    storage_root: Path = Path("./data/storage")
    contracts_dir: Path = _REPO_ROOT / "packages" / "research-core-contracts"
    evaluation_fixtures_dir: Path = _REPO_ROOT / "docs" / "evaluation" / "fixtures"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    # Host names the API answers to (DNS-rebinding protection, #55). "api" is the compose service name.
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "::1", "api"])

    # Versions stamped onto every audit/research event (FR-PROJ-003, PRD §67).
    methodology_version: str = "1.0.0"
    constitution_version: str = "1.0.0"

    # Local single-owner mode (PRD §62): the domain stays role-aware.
    local_owner_id: str = "local-owner"
    local_owner_display_name: str = "Local owner"
    # In single-owner mode the owner holds every human role (ADR-006).
    local_owner_roles: list[str] = Field(
        default_factory=lambda: [
            "RESEARCHER",
            "PROJECT_LEAD",
            "METHODOLOGY_STEWARD",
            "CONSTITUTIONAL_AUTHORITY",
        ]
    )

    # Upload/storage limits (SEC-006).
    max_upload_bytes: int = 100 * 1024 * 1024

    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Model profiles (PRD §46.2, ADR-010). Model ids and prices are configuration, not product logic.
    ai_default_profile: str = "anthropic-default"
    anthropic_model: str = "claude-opus-5"
    anthropic_effort: str = "high"
    anthropic_input_usd_per_mtok: float = 5.0
    anthropic_output_usd_per_mtok: float = 25.0
    anthropic_web_search_usd_per_request: float = 0.01
    openai_model: str = "gpt-5"
    openai_effort: str = "high"
    openai_input_usd_per_mtok: float = 1.25
    openai_output_usd_per_mtok: float = 10.0
    ai_max_output_tokens: int = 16000
    ai_request_timeout_seconds: float = 300.0
    # Deterministic mock provider for CI/E2E/demos. Never enabled implicitly.
    ai_mock_enabled: bool = False
    # Simulated behaviour of the mock provider (E2E provider-outage flow, PRD §73 flow 9).
    ai_mock_mode: Literal["ok", "unavailable", "invalid"] = "ok"

    # Selective cloud workspace (PRD §56, ADR-023). Off unless configured; the local database stays canonical.
    # "local-directory" is the reference adapter: a sandboxed directory standing in for a remote workspace.
    cloud_workspace_adapter: Literal["none", "local-directory"] = "none"
    cloud_workspace_root: Path = Path("./data/cloud-workspace")
    cloud_workspace_default_ttl_hours: int = Field(default=72, ge=1)
    cloud_workspace_max_ttl_hours: int = Field(default=720, ge=1)

    # Optional Qur'an font for PDF export, e.g. a publisher font whose licence the owner has checked (ADR-024).
    # Without it the bundled Amiri Quran font (SIL OFL) is used.
    export_quran_font_path: Path | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
