"""Projects, Research State, notes, Problem Frames, approvals, decisions, quality gates.

Approvals and gate evaluations are append-only. Approved/superseded Problem Frame
versions and resolved decisions are immutable, enforced by triggers (FR-FRAME-007,
FR-DEC-002, PRD §60).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-24 17:56:44.774077
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_FRAME_FN = """
CREATE OR REPLACE FUNCTION protect_problem_frame_versions() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'problem frame versions are never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF OLD.status = 'DRAFT' THEN
        RETURN NEW;
    END IF;
    IF NEW.content IS DISTINCT FROM OLD.content
       OR NEW.provenance IS DISTINCT FROM OLD.provenance
       OR NEW.version_number IS DISTINCT FROM OLD.version_number
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.approval_id IS DISTINCT FROM OLD.approval_id
       OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
       OR NOT (OLD.status = NEW.status OR (OLD.status = 'APPROVED' AND NEW.status = 'SUPERSEDED')) THEN
        RAISE EXCEPTION 'approved problem frame versions are immutable (only APPROVED -> SUPERSEDED)'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_DECISION_FN = """
CREATE OR REPLACE FUNCTION protect_resolved_decisions() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'decisions are never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF OLD.status <> 'OPEN' THEN
        RAISE EXCEPTION 'resolved or withdrawn decisions are immutable' USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.create_table(
        "approvals",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("approver_kind", sa.String(length=20), nullable=False),
        sa.Column("approver_id", sa.String(length=200), nullable=False),
        sa.Column("approver_role", sa.String(length=40), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("methodology_path", sa.String(length=40), nullable=False),
        sa.Column("gate_evaluation_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("approver_kind = 'HUMAN'", name=op.f("ck_approvals_human_approver")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approvals")),
    )
    op.create_index(op.f("ix_approvals_project_id"), "approvals", ["project_id"], unique=False)
    op.create_index("ix_approvals_subject", "approvals", ["subject_type", "subject_id"], unique=False)
    op.create_table(
        "decisions",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ai_recommendation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("required_role", sa.String(length=40), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=True),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("final_decision", sa.Text(), nullable=True),
        sa.Column("human_justification", sa.Text(), nullable=True),
        sa.Column("methodology_path", sa.String(length=40), nullable=True),
        sa.Column("decided_by_kind", sa.String(length=20), nullable=True),
        sa.Column("decided_by_id", sa.String(length=200), nullable=True),
        sa.Column("decided_by_role", sa.String(length=40), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_kind", sa.String(length=20), nullable=False),
        sa.Column("created_by_id", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "status <> 'DECIDED' OR (decided_by_kind = 'HUMAN' AND final_decision IS NOT NULL AND human_justification IS NOT NULL)",
            name=op.f("ck_decisions_human_decides"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decisions")),
    )
    op.create_index(op.f("ix_decisions_project_id"), "decisions", ["project_id"], unique=False)
    op.create_index(op.f("ix_decisions_status"), "decisions", ["status"], unique=False)
    op.create_table(
        "projects",
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("initial_input", sa.Text(), nullable=False),
        sa.Column("input_type", sa.String(length=40), nullable=False),
        sa.Column("sensitivity", sa.String(length=20), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("research_mode", sa.String(length=30), nullable=False),
        sa.Column("primary_language", sa.String(length=5), nullable=False),
        sa.Column("forked_from_project_id", sa.Uuid(), nullable=True),
        sa.Column("core_schema_version", sa.String(length=20), nullable=False),
        sa.Column("methodology_version", sa.String(length=20), nullable=False),
        sa.Column("constitution_version", sa.String(length=20), nullable=False),
        sa.Column("owner_kind", sa.String(length=20), nullable=False),
        sa.Column("owner_id", sa.String(length=200), nullable=False),
        sa.Column("owner_role", sa.String(length=40), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["forked_from_project_id"], ["projects.id"], name=op.f("fk_projects_forked_from_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)
    op.create_table(
        "quality_gate_evaluations",
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("gate", sa.String(length=40), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=True),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("findings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("methodology_version", sa.String(length=20), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_gate_evaluations")),
    )
    op.create_index(
        op.f("ix_quality_gate_evaluations_project_id"), "quality_gate_evaluations", ["project_id"], unique=False
    )
    op.create_index(
        "ix_quality_gate_evaluations_subject", "quality_gate_evaluations", ["subject_type", "subject_id"], unique=False
    )
    op.create_table(
        "problem_frame_versions",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("supersedes_version_id", sa.Uuid(), nullable=True),
        sa.Column("approval_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_problem_frame_versions_project_id_projects")
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_version_id"],
            ["problem_frame_versions.id"],
            name=op.f("fk_problem_frame_versions_supersedes_version_id_problem_frame_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_problem_frame_versions")),
        sa.UniqueConstraint("project_id", "version_number", name="uq_problem_frame_versions_project_version"),
    )
    op.create_index(
        op.f("ix_problem_frame_versions_project_id"), "problem_frame_versions", ["project_id"], unique=False
    )
    op.create_index(
        "uq_problem_frame_versions_one_approved",
        "problem_frame_versions",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("status = 'APPROVED'"),
    )
    op.create_index(
        "uq_problem_frame_versions_one_draft",
        "problem_frame_versions",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("status = 'DRAFT'"),
    )
    op.create_table(
        "project_closures",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("closure_type", sa.String(length=40), nullable=False),
        sa.Column("record", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("closed_by_id", sa.String(length=200), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopen_trigger", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_project_closures_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_closures")),
    )
    op.create_index(op.f("ix_project_closures_project_id"), "project_closures", ["project_id"], unique=False)
    op.create_table(
        "research_states",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("current_question", sa.Text(), nullable=True),
        sa.Column("established_findings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("unresolved_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active_hypothesis_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reservations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("next_action_reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_research_states_project_id_projects")),
        sa.PrimaryKeyConstraint("project_id", name=op.f("pk_research_states")),
    )
    op.create_table(
        "scratch_notes",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", sa.String(length=200), nullable=False),
        sa.Column("captured_as", sa.String(length=60), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_scratch_notes_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scratch_notes")),
    )
    op.create_index(op.f("ix_scratch_notes_project_id"), "scratch_notes", ["project_id"], unique=False)

    # --- immutability rules enforced in the database ---
    for table in ("approvals", "quality_gate_evaluations"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_mutation_of_append_only()"
        )
    op.execute(_FRAME_FN)
    op.execute(
        "CREATE TRIGGER problem_frame_versions_immutable BEFORE UPDATE OR DELETE ON problem_frame_versions "
        "FOR EACH ROW EXECUTE FUNCTION protect_problem_frame_versions()"
    )
    op.execute(_DECISION_FN)
    op.execute(
        "CREATE TRIGGER decisions_immutable_once_resolved BEFORE UPDATE OR DELETE ON decisions "
        "FOR EACH ROW EXECUTE FUNCTION protect_resolved_decisions()"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_scratch_notes_project_id"), table_name="scratch_notes")
    op.drop_table("scratch_notes")
    op.drop_table("research_states")
    op.drop_index(op.f("ix_project_closures_project_id"), table_name="project_closures")
    op.drop_table("project_closures")
    op.drop_index(
        "uq_problem_frame_versions_one_draft",
        table_name="problem_frame_versions",
        postgresql_where=sa.text("status = 'DRAFT'"),
    )
    op.drop_index(
        "uq_problem_frame_versions_one_approved",
        table_name="problem_frame_versions",
        postgresql_where=sa.text("status = 'APPROVED'"),
    )
    op.drop_index(op.f("ix_problem_frame_versions_project_id"), table_name="problem_frame_versions")
    op.drop_table("problem_frame_versions")
    op.drop_index("ix_quality_gate_evaluations_subject", table_name="quality_gate_evaluations")
    op.drop_index(op.f("ix_quality_gate_evaluations_project_id"), table_name="quality_gate_evaluations")
    op.drop_table("quality_gate_evaluations")
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_decisions_status"), table_name="decisions")
    op.drop_index(op.f("ix_decisions_project_id"), table_name="decisions")
    op.drop_table("decisions")
    op.drop_index("ix_approvals_subject", table_name="approvals")
    op.drop_index(op.f("ix_approvals_project_id"), table_name="approvals")
    op.drop_table("approvals")
    op.execute("DROP FUNCTION IF EXISTS protect_problem_frame_versions()")
    op.execute("DROP FUNCTION IF EXISTS protect_resolved_decisions()")
