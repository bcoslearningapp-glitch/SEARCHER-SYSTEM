from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text

from research_api.models import Base
from tests.integration.conftest import alembic_config


def test_migrations_round_trip_and_match_models(engine: Engine) -> None:
    config = alembic_config()
    command.downgrade(config, "base")
    assert "audit_events" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")

    tables = set(inspect(engine).get_table_names())
    assert {"audit_events", "research_events", "background_jobs"} <= tables

    with engine.connect() as connection:
        assert connection.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'")).scalar()
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == [], f"models and migrations diverge: {diff}"
