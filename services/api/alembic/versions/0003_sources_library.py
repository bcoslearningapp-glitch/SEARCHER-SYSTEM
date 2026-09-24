"""Source library: SourceWork/SourceEdition/SourceAsset, excerpts, access requests, leads.

Excerpts are immutable (append-only trigger): exact quotations are protected content
(Core §29). OCR text cannot be stored as an exact quote unless verified.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-24 18:04:23.810320
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_works",
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("original_language", sa.String(length=20), nullable=True),
        sa.Column("authority_layer", sa.String(length=40), nullable=False),
        sa.Column("identifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by_id", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_works")),
    )
    op.create_index(op.f("ix_source_works_authority_layer"), "source_works", ["authority_layer"], unique=False)
    op.create_table(
        "project_sources",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("work_id", sa.Uuid(), nullable=False),
        sa.Column("added_by_id", sa.String(length=200), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_project_sources_project_id_projects")),
        sa.ForeignKeyConstraint(["work_id"], ["source_works.id"], name=op.f("fk_project_sources_work_id_source_works")),
        sa.PrimaryKeyConstraint("project_id", "work_id", name=op.f("pk_project_sources")),
    )
    op.create_table(
        "source_editions",
        sa.Column("work_id", sa.Uuid(), nullable=False),
        sa.Column("edition_label", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("translator", sa.Text(), nullable=True),
        sa.Column("publisher", sa.Text(), nullable=True),
        sa.Column("published_date", sa.String(length=40), nullable=True),
        sa.Column("identifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("verification_state", sa.String(length=40), nullable=False),
        sa.Column("license_note", sa.Text(), nullable=True),
        sa.Column("portable_asset_allowed", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["work_id"], ["source_works.id"], name=op.f("fk_source_editions_work_id_source_works")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_editions")),
    )
    op.create_index(op.f("ix_source_editions_work_id"), "source_editions", ["work_id"], unique=False)
    op.create_table(
        "source_access_requests",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("edition_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_scope", sa.Text(), nullable=False),
        sa.Column("surrounding_context", sa.Text(), nullable=True),
        sa.Column("acceptable_forms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by_kind", sa.String(length=20), nullable=False),
        sa.Column("created_by_id", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["source_editions.id"], name=op.f("fk_source_access_requests_edition_id_source_editions")
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_source_access_requests_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_access_requests")),
    )
    op.create_index(
        op.f("ix_source_access_requests_edition_id"), "source_access_requests", ["edition_id"], unique=False
    )
    op.create_index(
        op.f("ix_source_access_requests_project_id"), "source_access_requests", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_source_access_requests_status"), "source_access_requests", ["status"], unique=False)
    op.create_table(
        "source_assets",
        sa.Column("edition_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("access_mode", sa.String(length=30), nullable=False),
        sa.Column("available_in_environment", sa.Boolean(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("media_type", sa.String(length=100), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=True),
        sa.Column("storage_key", sa.String(length=100), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("text_origin", sa.String(length=30), nullable=True),
        sa.Column("holding_note", sa.Text(), nullable=True),
        sa.Column("ingestion_status", sa.String(length=20), nullable=False),
        sa.Column("ingestion_job_id", sa.Uuid(), nullable=True),
        sa.Column("access_request_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["source_editions.id"], name=op.f("fk_source_assets_edition_id_source_editions")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_assets")),
    )
    op.create_index(op.f("ix_source_assets_edition_id"), "source_assets", ["edition_id"], unique=False)
    op.create_index(op.f("ix_source_assets_sha256"), "source_assets", ["sha256"], unique=False)
    op.create_table(
        "source_excerpts",
        sa.Column("edition_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("text_origin", sa.String(length=30), nullable=False),
        sa.Column("verification_state", sa.String(length=40), nullable=False),
        sa.Column("is_exact_quote", sa.Boolean(), nullable=False),
        sa.Column("access_request_id", sa.Uuid(), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["access_request_id"],
            ["source_access_requests.id"],
            name=op.f("fk_source_excerpts_access_request_id_source_access_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["source_assets.id"], name=op.f("fk_source_excerpts_asset_id_source_assets")
        ),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["source_editions.id"], name=op.f("fk_source_excerpts_edition_id_source_editions")
        ),
        sa.CheckConstraint(
            "NOT (text_origin = 'OCR_EXTRACTED' AND is_exact_quote AND verification_state NOT IN ('MACHINE_VERIFIED', 'RESEARCHER_SUPPLIED_EXACT'))",
            name=op.f("ck_source_excerpts_ocr_not_exact_unless_verified"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_excerpts")),
    )
    op.create_index(op.f("ix_source_excerpts_edition_id"), "source_excerpts", ["edition_id"], unique=False)
    op.create_table(
        "source_leads",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("suspected_author", sa.Text(), nullable=True),
        sa.Column("suspected_work_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("verified_by_excerpt_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_id", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_source_leads_project_id_projects")),
        sa.ForeignKeyConstraint(
            ["suspected_work_id"], ["source_works.id"], name=op.f("fk_source_leads_suspected_work_id_source_works")
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_excerpt_id"],
            ["source_excerpts.id"],
            name=op.f("fk_source_leads_verified_by_excerpt_id_source_excerpts"),
        ),
        sa.CheckConstraint(
            "status <> 'VERIFIED' OR verified_by_excerpt_id IS NOT NULL",
            name=op.f("ck_source_leads_verified_has_excerpt"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_leads")),
    )
    op.create_index(op.f("ix_source_leads_project_id"), "source_leads", ["project_id"], unique=False)
    op.execute(
        "CREATE TRIGGER source_excerpts_append_only BEFORE UPDATE OR DELETE ON source_excerpts "
        "FOR EACH ROW EXECUTE FUNCTION reject_mutation_of_append_only()"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_source_leads_project_id"), table_name="source_leads")
    op.drop_table("source_leads")
    op.drop_index(op.f("ix_source_excerpts_edition_id"), table_name="source_excerpts")
    op.drop_table("source_excerpts")
    op.drop_index(op.f("ix_source_assets_sha256"), table_name="source_assets")
    op.drop_index(op.f("ix_source_assets_edition_id"), table_name="source_assets")
    op.drop_table("source_assets")
    op.drop_index(op.f("ix_source_access_requests_status"), table_name="source_access_requests")
    op.drop_index(op.f("ix_source_access_requests_project_id"), table_name="source_access_requests")
    op.drop_index(op.f("ix_source_access_requests_edition_id"), table_name="source_access_requests")
    op.drop_table("source_access_requests")
    op.drop_index(op.f("ix_source_editions_work_id"), table_name="source_editions")
    op.drop_table("source_editions")
    op.drop_table("project_sources")
    op.drop_index(op.f("ix_source_works_authority_layer"), table_name="source_works")
    op.drop_table("source_works")
