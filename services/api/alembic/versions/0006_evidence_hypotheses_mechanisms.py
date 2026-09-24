"""Evidence, lineage, research tracks, hypotheses (immutable versions) and mechanisms.

hypothesis_versions is append-only; assessed evidence is immutable (Core §20, §32, FR-HYP-004).

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-24 18:30:39.556442
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_EVIDENCE_FN = """
CREATE OR REPLACE FUNCTION protect_assessed_evidence() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'evidence is never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF OLD.status <> 'CANDIDATE' THEN
        RAISE EXCEPTION 'assessed evidence is immutable; record new evidence instead' USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.create_table(
        "hypotheses",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=30), nullable=False),
        sa.Column("epistemic_state", sa.String(length=20), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_hypotheses_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hypotheses")),
    )
    op.create_index(op.f("ix_hypotheses_project_id"), "hypotheses", ["project_id"], unique=False)
    op.create_table(
        "mechanisms",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_mechanisms_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mechanisms")),
    )
    op.create_index(op.f("ix_mechanisms_project_id"), "mechanisms", ["project_id"], unique=False)
    op.create_table(
        "research_track_runs",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("track", sa.String(length=30), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("queries", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("performed_by_id", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_research_track_runs_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_track_runs")),
    )
    op.create_index(op.f("ix_research_track_runs_project_id"), "research_track_runs", ["project_id"], unique=False)
    op.create_index("ix_research_track_runs_target", "research_track_runs", ["target_type", "target_id"], unique=False)
    op.create_table(
        "source_lineage",
        sa.Column("from_work_id", sa.Uuid(), nullable=False),
        sa.Column("relation", sa.String(length=20), nullable=False),
        sa.Column("to_work_id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("from_work_id <> to_work_id", name=op.f("ck_source_lineage_no_self_lineage")),
        sa.ForeignKeyConstraint(
            ["from_work_id"], ["source_works.id"], name=op.f("fk_source_lineage_from_work_id_source_works")
        ),
        sa.ForeignKeyConstraint(
            ["to_work_id"], ["source_works.id"], name=op.f("fk_source_lineage_to_work_id_source_works")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_lineage")),
        sa.UniqueConstraint("from_work_id", "relation", "to_work_id", name="uq_source_lineage_edge"),
    )
    op.create_index(op.f("ix_source_lineage_from_work_id"), "source_lineage", ["from_work_id"], unique=False)
    op.create_index(op.f("ix_source_lineage_to_work_id"), "source_lineage", ["to_work_id"], unique=False)
    op.create_table(
        "hypothesis_competitions",
        sa.Column("hypothesis_a_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis_b_id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["hypothesis_a_id"], ["hypotheses.id"], name=op.f("fk_hypothesis_competitions_hypothesis_a_id_hypotheses")
        ),
        sa.ForeignKeyConstraint(
            ["hypothesis_b_id"], ["hypotheses.id"], name=op.f("fk_hypothesis_competitions_hypothesis_b_id_hypotheses")
        ),
        sa.PrimaryKeyConstraint("hypothesis_a_id", "hypothesis_b_id", name=op.f("pk_hypothesis_competitions")),
    )
    op.create_table(
        "hypothesis_mechanisms",
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("mechanism_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"], ["hypotheses.id"], name=op.f("fk_hypothesis_mechanisms_hypothesis_id_hypotheses")
        ),
        sa.ForeignKeyConstraint(
            ["mechanism_id"], ["mechanisms.id"], name=op.f("fk_hypothesis_mechanisms_mechanism_id_mechanisms")
        ),
        sa.PrimaryKeyConstraint("hypothesis_id", "mechanism_id", name=op.f("pk_hypothesis_mechanisms")),
    )
    op.create_table(
        "hypothesis_versions",
        sa.Column("hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=30), nullable=False),
        sa.Column("epistemic_state", sa.String(length=20), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("actor_kind", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.String(length=200), nullable=False),
        sa.Column("actor_role", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"], ["hypotheses.id"], name=op.f("fk_hypothesis_versions_hypothesis_id_hypotheses")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hypothesis_versions")),
        sa.UniqueConstraint("hypothesis_id", "version_number", name="uq_hypothesis_versions_number"),
    )
    op.create_index(
        op.f("ix_hypothesis_versions_hypothesis_id"), "hypothesis_versions", ["hypothesis_id"], unique=False
    )
    op.create_table(
        "evidence",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("finding", sa.Text(), nullable=False),
        sa.Column("excerpt_id", sa.Uuid(), nullable=False),
        sa.Column("track", sa.String(length=30), nullable=True),
        sa.Column("assessment", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("assessed_by_id", sa.String(length=200), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status <> 'ACCEPTED' OR assessment IS NOT NULL", name=op.f("ck_evidence_accepted_has_assessment")
        ),
        sa.ForeignKeyConstraint(
            ["excerpt_id"], ["source_excerpts.id"], name=op.f("fk_evidence_excerpt_id_source_excerpts")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_evidence_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence")),
    )
    op.create_index(op.f("ix_evidence_project_id"), "evidence", ["project_id"], unique=False)
    op.create_index(op.f("ix_evidence_status"), "evidence", ["status"], unique=False)
    op.create_index("ix_evidence_target", "evidence", ["target_type", "target_id"], unique=False)

    op.execute(
        "CREATE TRIGGER hypothesis_versions_append_only BEFORE UPDATE OR DELETE ON hypothesis_versions "
        "FOR EACH ROW EXECUTE FUNCTION reject_mutation_of_append_only()"
    )
    op.execute(_EVIDENCE_FN)
    op.execute(
        "CREATE TRIGGER evidence_immutable_once_assessed BEFORE UPDATE OR DELETE ON evidence "
        "FOR EACH ROW EXECUTE FUNCTION protect_assessed_evidence()"
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_target", table_name="evidence")
    op.drop_index(op.f("ix_evidence_status"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_project_id"), table_name="evidence")
    op.drop_table("evidence")
    op.drop_index(op.f("ix_hypothesis_versions_hypothesis_id"), table_name="hypothesis_versions")
    op.drop_table("hypothesis_versions")
    op.drop_table("hypothesis_mechanisms")
    op.drop_table("hypothesis_competitions")
    op.drop_index(op.f("ix_source_lineage_to_work_id"), table_name="source_lineage")
    op.drop_index(op.f("ix_source_lineage_from_work_id"), table_name="source_lineage")
    op.drop_table("source_lineage")
    op.drop_index("ix_research_track_runs_target", table_name="research_track_runs")
    op.drop_index(op.f("ix_research_track_runs_project_id"), table_name="research_track_runs")
    op.drop_table("research_track_runs")
    op.drop_index(op.f("ix_mechanisms_project_id"), table_name="mechanisms")
    op.drop_table("mechanisms")
    op.drop_index(op.f("ix_hypotheses_project_id"), table_name="hypotheses")
    op.drop_table("hypotheses")
    op.execute("DROP FUNCTION IF EXISTS protect_assessed_evidence()")
