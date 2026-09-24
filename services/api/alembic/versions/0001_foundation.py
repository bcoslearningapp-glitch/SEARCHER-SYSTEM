"""Foundation: pgvector, append-only audit/research events, durable background jobs.

Revision ID: 0001
Revises:
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APPEND_ONLY_FN = """
CREATE OR REPLACE FUNCTION reject_mutation_of_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'table % is append-only; % is not permitted', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;
"""


def _event_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_kind", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.String(length=200), nullable=False),
        sa.Column("actor_role", sa.String(length=40), nullable=True),
        sa.Column("core_schema_version", sa.String(length=20), nullable=False),
        sa.Column("methodology_version", sa.String(length=20), nullable=False),
        sa.Column("constitution_version", sa.String(length=20), nullable=False),
    ]


def _append_only(table: str) -> None:
    op.execute(
        f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
        "FOR EACH ROW EXECUTE FUNCTION reject_mutation_of_append_only()"
    )
    op.execute(
        f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} "
        "FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation_of_append_only()"
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(_APPEND_ONLY_FN)

    op.create_table(
        "audit_events",
        *_event_columns(),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("previous_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ai_action", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
        sa.CheckConstraint(
            "actor_kind <> 'AI' OR ai_action IS NOT NULL", name=op.f("ck_audit_events_ai_provenance")
        ),
    )
    op.create_index(op.f("ix_audit_events_project_id"), "audit_events", ["project_id"])
    op.create_index(op.f("ix_audit_events_occurred_at"), "audit_events", ["occurred_at"])
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"])
    _append_only("audit_events")

    op.create_table(
        "research_events",
        *_event_columns(),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_events")),
    )
    op.create_index(op.f("ix_research_events_project_id"), "research_events", ["project_id"])
    op.create_index(op.f("ix_research_events_occurred_at"), "research_events", ["occurred_at"])
    op.create_index("ix_research_events_entity", "research_events", ["entity_type", "entity_id"])
    _append_only("research_events")

    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("failure_kind", sa.String(length=40), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_jobs")),
    )
    op.create_index(op.f("ix_background_jobs_kind"), "background_jobs", ["kind"])
    op.create_index(op.f("ix_background_jobs_state"), "background_jobs", ["state"])
    op.create_index(op.f("ix_background_jobs_project_id"), "background_jobs", ["project_id"])


def downgrade() -> None:
    op.drop_table("background_jobs")
    op.drop_table("research_events")
    op.drop_table("audit_events")
    op.execute("DROP FUNCTION IF EXISTS reject_mutation_of_append_only()")
    # The vector extension is left installed: other databases objects may depend on it.
