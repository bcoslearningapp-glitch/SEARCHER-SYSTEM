"""Portability API schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ImportOut(BaseModel):
    package_id: str
    project_id: UUID
    inserted: dict[str, int]
    kept_existing: dict[str, int]
    assets_restored: int
    metadata_only_assets: list[str]
    staged_foundational: list[str]
    trust_notes: list[str]
