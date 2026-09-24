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

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Versions stamped onto every audit/research event (FR-PROJ-003, PRD §67).
    methodology_version: str = "1.0.0"
    constitution_version: str = "1.0.0"

    # Local single-owner mode (PRD §62): the domain stays role-aware.
    local_owner_id: str = "local-owner"

    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
