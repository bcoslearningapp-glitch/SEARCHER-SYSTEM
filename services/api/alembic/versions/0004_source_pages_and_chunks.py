"""Page-anchored extracted text and retrieval chunks with a full-text index (PRD §17, §61).

Derived data: re-ingestion may replace rows; original assets are never modified.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-24 18:05:39.247877
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_chunks",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "tsv", postgresql.TSVECTOR(), sa.Computed("to_tsvector('simple', text)", persisted=True), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["source_assets.id"], name=op.f("fk_source_chunks_asset_id_source_assets")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_chunks")),
    )
    op.create_index(op.f("ix_source_chunks_asset_id"), "source_chunks", ["asset_id"], unique=False)
    op.create_index("ix_source_chunks_tsv", "source_chunks", ["tsv"], unique=False, postgresql_using="gin")
    op.create_table(
        "source_pages",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_origin", sa.String(length=30), nullable=False),
        sa.Column("needs_ocr", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["source_assets.id"], name=op.f("fk_source_pages_asset_id_source_assets")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_pages")),
        sa.UniqueConstraint("asset_id", "page_number", name="uq_source_pages_asset_page"),
    )
    op.create_index(op.f("ix_source_pages_asset_id"), "source_pages", ["asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_source_pages_asset_id"), table_name="source_pages")
    op.drop_table("source_pages")
    op.drop_index("ix_source_chunks_tsv", table_name="source_chunks", postgresql_using="gin")
    op.drop_index(op.f("ix_source_chunks_asset_id"), table_name="source_chunks")
    op.drop_table("source_chunks")
