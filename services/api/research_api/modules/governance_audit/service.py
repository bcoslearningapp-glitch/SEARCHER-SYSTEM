"""Public audit service. Every material state change goes through here (FR-EVENT-001)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import CONTRACT_SCHEMA_VERSION
from research_api.modules.governance_audit.models import AuditEventRecord, ResearchEventRecord
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    AuditEntry,
    AuditEventOut,
    ResearchEventEntry,
    VersionContext,
)


def _version_columns() -> dict[str, str]:
    settings = get_settings()
    return {
        "core_schema_version": CONTRACT_SCHEMA_VERSION,
        "methodology_version": settings.methodology_version,
        "constitution_version": settings.constitution_version,
    }


def _actor_columns(actor: Actor) -> dict[str, str | None]:
    return {
        "actor_kind": actor.kind.value,
        "actor_id": actor.id,
        "actor_role": actor.role.value if actor.role else None,
    }


def record_audit(session: Session, entry: AuditEntry) -> AuditEventRecord:
    """Append an audit event in the caller's transaction.

    The caller owns the transaction so the audit record commits or rolls back
    atomically with the state change it describes (NFR-REL-003).
    """
    record = AuditEventRecord(
        project_id=entry.project_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        action=entry.action,
        previous_state=entry.previous_state,
        new_state=entry.new_state,
        reason=entry.reason,
        ai_action=entry.ai_action.model_dump(mode="json") if entry.ai_action else None,
        **_actor_columns(entry.actor),
        **_version_columns(),
    )
    session.add(record)
    session.flush()
    return record


def record_research_event(session: Session, entry: ResearchEventEntry) -> ResearchEventRecord:
    """Append a research event in the caller's transaction (Core §56)."""
    record = ResearchEventRecord(
        project_id=entry.project_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        event_type=entry.event_type,
        payload=entry.payload,
        **_actor_columns(entry.actor),
        **_version_columns(),
    )
    session.add(record)
    session.flush()
    return record


def to_out(record: AuditEventRecord) -> AuditEventOut:
    return AuditEventOut(
        id=record.id,
        project_id=record.project_id,
        action=record.action,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        occurred_at=record.occurred_at,
        actor=Actor.model_validate(
            {"kind": record.actor_kind, "id": record.actor_id, "role": record.actor_role}
        ),
        versions=VersionContext(
            core_schema_version=record.core_schema_version,
            methodology_version=record.methodology_version,
            constitution_version=record.constitution_version,
        ),
        previous_state=record.previous_state,
        new_state=record.new_state,
        reason=record.reason,
        ai_action=AIActionRecord.model_validate(record.ai_action) if record.ai_action else None,
    )


def list_audit_events(
    session: Session, *, project_id: UUID | None = None, limit: int = 100
) -> list[AuditEventOut]:
    query = select(AuditEventRecord).order_by(AuditEventRecord.occurred_at.desc()).limit(limit)
    if project_id is not None:
        query = query.where(AuditEventRecord.project_id == project_id)
    return [to_out(r) for r in session.scalars(query)]
