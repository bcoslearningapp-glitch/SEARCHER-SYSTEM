"""Foundational library (Qur'an text, Hadith), reference reviews and judgments, operational constraints.

Qur'an text, Hadith records, reference entries and judgments are append-only (Core §8, §29-31).

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-24 18:38:29.113022
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "foundational_sources",
        sa.Column("work_id", sa.Uuid(), nullable=False),
        sa.Column("authority_layer", sa.String(length=40), nullable=False),
        sa.Column("edition_version", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("dataset_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("staged_by_id", sa.String(length=200), nullable=False),
        sa.Column("approved_by_kind", sa.String(length=20), nullable=True),
        sa.Column("approved_by_id", sa.String(length=200), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status <> 'APPROVED' OR (approved_by_kind = 'HUMAN' AND approved_at IS NOT NULL)",
            name=op.f("ck_foundational_sources_human_approval"),
        ),
        sa.ForeignKeyConstraint(
            ["work_id"], ["source_works.id"], name=op.f("fk_foundational_sources_work_id_source_works")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_foundational_sources")),
    )
    op.create_index(op.f("ix_foundational_sources_status"), "foundational_sources", ["status"], unique=False)
    op.create_index(op.f("ix_foundational_sources_work_id"), "foundational_sources", ["work_id"], unique=False)
    op.create_index(
        "uq_foundational_sources_one_approved_quran",
        "foundational_sources",
        ["authority_layer"],
        unique=True,
        postgresql_where=sa.text("status = 'APPROVED' AND authority_layer = 'QURAN'"),
    )
    op.create_table(
        "operational_constraints",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("required_change", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_operational_constraints_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_operational_constraints")),
    )
    op.create_index(
        op.f("ix_operational_constraints_project_id"), "operational_constraints", ["project_id"], unique=False
    )
    op.create_index(
        "ix_operational_constraints_target", "operational_constraints", ["target_type", "target_id"], unique=False
    )
    op.create_table(
        "reference_reviews",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("analytical_category", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_reference_reviews_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_reviews")),
    )
    op.create_index(op.f("ix_reference_reviews_project_id"), "reference_reviews", ["project_id"], unique=False)
    op.create_index("ix_reference_reviews_target", "reference_reviews", ["target_type", "target_id"], unique=False)
    op.create_table(
        "hadith_records",
        sa.Column("foundational_source_id", sa.Uuid(), nullable=False),
        sa.Column("collection", sa.Text(), nullable=False),
        sa.Column("book", sa.Text(), nullable=True),
        sa.Column("chapter", sa.Text(), nullable=True),
        sa.Column("number", sa.String(length=40), nullable=False),
        sa.Column("numbering_scheme", sa.Text(), nullable=False),
        sa.Column("narrator", sa.Text(), nullable=True),
        sa.Column("exact_text", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("entered_by_id", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["foundational_source_id"],
            ["foundational_sources.id"],
            name=op.f("fk_hadith_records_foundational_source_id_foundational_sources"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hadith_records")),
        sa.UniqueConstraint("foundational_source_id", "numbering_scheme", "number", name="uq_hadith_records_number"),
    )
    op.create_index(
        op.f("ix_hadith_records_foundational_source_id"), "hadith_records", ["foundational_source_id"], unique=False
    )
    op.create_table(
        "quran_ayat",
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("ayah_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"], ["foundational_sources.id"], name=op.f("fk_quran_ayat_source_id_foundational_sources")
        ),
        sa.PrimaryKeyConstraint("source_id", "surah_number", "ayah_number", name=op.f("pk_quran_ayat")),
    )
    op.create_table(
        "quran_surahs",
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"], ["foundational_sources.id"], name=op.f("fk_quran_surahs_source_id_foundational_sources")
        ),
        sa.PrimaryKeyConstraint("source_id", "surah_number", name=op.f("pk_quran_surahs")),
    )
    op.create_table(
        "reference_judgments",
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("directness", sa.String(length=20), nullable=False),
        sa.Column("reservation_type", sa.String(length=30), nullable=True),
        sa.Column("divergence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("judged_by_kind", sa.String(length=20), nullable=False),
        sa.Column("judged_by_id", sa.String(length=200), nullable=False),
        sa.Column("judged_by_role", sa.String(length=40), nullable=True),
        sa.Column("decision_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "(state = 'RESERVED') = (reservation_type IS NOT NULL)",
            name=op.f("ck_reference_judgments_reservation_iff_reserved"),
        ),
        sa.CheckConstraint("judged_by_kind = 'HUMAN'", name=op.f("ck_reference_judgments_human_judge")),
        sa.ForeignKeyConstraint(
            ["review_id"], ["reference_reviews.id"], name=op.f("fk_reference_judgments_review_id_reference_reviews")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_judgments")),
    )
    op.create_index(op.f("ix_reference_judgments_review_id"), "reference_judgments", ["review_id"], unique=False)
    op.create_table(
        "reference_entries",
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("layer", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_excerpt_id", sa.Uuid(), nullable=True),
        sa.Column("quran_ref", sa.String(length=20), nullable=True),
        sa.Column("hadith_record_id", sa.Uuid(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "layer <> 'SOURCE_TEXT' OR source_excerpt_id IS NOT NULL OR quran_ref IS NOT NULL OR hadith_record_id IS NOT NULL",
            name=op.f("ck_reference_entries_source_text_is_sourced"),
        ),
        sa.CheckConstraint(
            "provenance->>'kind' <> 'AI_GENERATED' OR layer = 'SYSTEM_SYNTHESIS'",
            name=op.f("ck_reference_entries_ai_only_synthesis"),
        ),
        sa.ForeignKeyConstraint(
            ["hadith_record_id"],
            ["hadith_records.id"],
            name=op.f("fk_reference_entries_hadith_record_id_hadith_records"),
        ),
        sa.ForeignKeyConstraint(
            ["review_id"], ["reference_reviews.id"], name=op.f("fk_reference_entries_review_id_reference_reviews")
        ),
        sa.ForeignKeyConstraint(
            ["source_excerpt_id"],
            ["source_excerpts.id"],
            name=op.f("fk_reference_entries_source_excerpt_id_source_excerpts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_entries")),
    )
    op.create_index(op.f("ix_reference_entries_review_id"), "reference_entries", ["review_id"], unique=False)

    for table in ("quran_surahs", "quran_ayat", "hadith_records", "reference_entries", "reference_judgments"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_mutation_of_append_only()"
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_reference_entries_review_id"), table_name="reference_entries")
    op.drop_table("reference_entries")
    op.drop_index(op.f("ix_reference_judgments_review_id"), table_name="reference_judgments")
    op.drop_table("reference_judgments")
    op.drop_table("quran_surahs")
    op.drop_table("quran_ayat")
    op.drop_index(op.f("ix_hadith_records_foundational_source_id"), table_name="hadith_records")
    op.drop_table("hadith_records")
    op.drop_index("ix_reference_reviews_target", table_name="reference_reviews")
    op.drop_index(op.f("ix_reference_reviews_project_id"), table_name="reference_reviews")
    op.drop_table("reference_reviews")
    op.drop_index("ix_operational_constraints_target", table_name="operational_constraints")
    op.drop_index(op.f("ix_operational_constraints_project_id"), table_name="operational_constraints")
    op.drop_table("operational_constraints")
    op.drop_index(
        "uq_foundational_sources_one_approved_quran",
        table_name="foundational_sources",
        postgresql_where=sa.text("status = 'APPROVED' AND authority_layer = 'QURAN'"),
    )
    op.drop_index(op.f("ix_foundational_sources_work_id"), table_name="foundational_sources")
    op.drop_index(op.f("ix_foundational_sources_status"), table_name="foundational_sources")
    op.drop_table("foundational_sources")
