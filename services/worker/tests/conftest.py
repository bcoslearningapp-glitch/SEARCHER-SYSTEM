from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

os.environ.setdefault("ENVIRONMENT", "test")

API_ROOT = Path(__file__).resolve().parents[2] / "api"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; worker tests need PostgreSQL with pgvector")
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    command.upgrade(config, "head")
    yield
