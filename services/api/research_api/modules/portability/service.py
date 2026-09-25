"""Research Core Package export/import with policy and audit (PRD §45)."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AuditEntry, ResearchEventEntry
from research_api.modules.portability import package
from research_api.modules.portability.schemas import ImportOut
from research_api.modules.project_workflow import service as projects
from research_api.platform.errors import RuleViolationError


def export_project(session: Session, principal: Principal, project_id: UUID) -> tuple[bytes, str]:
    auth = authorized(principal, "project.export")
    projects.get_project(session, project_id)
    actor = auth.actor.model_dump(mode="json", exclude_none=True)
    data, package_id = package.export_package(session, principal, project_id, actor)
    governance.record_audit(
        session,
        AuditEntry(
            project_id=project_id,
            action="project.export",
            entity_type="Project",
            entity_id=project_id,
            actor=auth.actor,
            new_state={"package_id": package_id, "bytes": len(data)},
        ),
    )
    return data, package_id


def import_project(session: Session, principal: Principal, data: bytes) -> ImportOut:
    auth = authorized(principal, "project.import")
    try:
        with session.begin_nested():
            report = package.import_package(session, data)
    except DBAPIError as exc:
        raise RuleViolationError("the package does not fit this installation's schema; nothing was imported") from exc
    out = ImportOut.model_validate(asdict(report))
    governance.record_audit(
        session,
        AuditEntry(
            project_id=out.project_id,
            action="project.import",
            entity_type="Project",
            entity_id=out.project_id,
            actor=auth.actor,
            new_state={
                "package_id": out.package_id,
                "inserted": out.inserted,
                "metadata_only": len(out.metadata_only_assets),
            },
        ),
    )
    governance.record_research_event(
        session,
        ResearchEventEntry(
            project_id=out.project_id,
            event_type="ProjectImported",
            entity_type="Project",
            entity_id=out.project_id,
            actor=auth.actor,
            payload={"package_id": out.package_id, "trust_notes": out.trust_notes},
        ),
    )
    return out
