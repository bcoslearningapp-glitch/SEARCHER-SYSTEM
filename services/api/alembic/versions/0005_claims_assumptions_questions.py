"""Claims, assumptions and open questions (Core §14-19, §37).

CHECK: SYSTEM_INFERRED assumptions must carry AI_GENERATED provenance (FR-CLAIM-003).

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24 18:23:11.095378
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=30), nullable=False),
        sa.Column("statement_origin", sa.String(length=30), nullable=False),
        sa.Column("workflow_state", sa.String(length=20), nullable=False),
        sa.Column("epistemic_strength", sa.String(length=30), nullable=False),
        sa.Column("important", sa.Boolean(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_note_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_claims_project_id_projects")),
        sa.ForeignKeyConstraint(
            ["source_note_id"], ["scratch_notes.id"], name=op.f("fk_claims_source_note_id_scratch_notes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claims")),
    )
    op.create_index(op.f("ix_claims_project_id"), "claims", ["project_id"], unique=False)
    op.create_table(
        "open_questions",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("conclusion", sa.String(length=40), nullable=True),
        sa.Column("source_note_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_open_questions_project_id_projects")),
        sa.ForeignKeyConstraint(
            ["source_note_id"], ["scratch_notes.id"], name=op.f("fk_open_questions_source_note_id_scratch_notes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_open_questions")),
    )
    op.create_index(op.f("ix_open_questions_project_id"), "open_questions", ["project_id"], unique=False)
    op.create_table(
        "assumptions",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("criticality", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("source_note_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "origin <> 'SYSTEM_INFERRED' OR provenance->>'kind' = 'AI_GENERATED'",
            name=op.f("ck_assumptions_inferred_is_ai"),
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], name=op.f("fk_assumptions_claim_id_claims")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_assumptions_project_id_projects")),
        sa.ForeignKeyConstraint(
            ["source_note_id"], ["scratch_notes.id"], name=op.f("fk_assumptions_source_note_id_scratch_notes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assumptions")),
    )
    op.create_index(op.f("ix_assumptions_project_id"), "assumptions", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assumptions_project_id"), table_name="assumptions")
    op.drop_table("assumptions")
    op.drop_index(op.f("ix_open_questions_project_id"), table_name="open_questions")
    op.drop_table("open_questions")
    op.drop_index(op.f("ix_claims_project_id"), table_name="claims")
    op.drop_table("claims")
