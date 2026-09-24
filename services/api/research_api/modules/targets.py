"""Cross-module registry for evidence targets.

Evidence (claims_evidence) can bear on claims, hypotheses and mechanisms, which
live in different modules. Instead of importing each other's internals, owning
modules register an existence check and a listener that reacts when accepted
evidence changes (PRD §58: no bypassing another module's public contract).
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import EvidenceTargetType
from research_api.platform.errors import NotFoundError

Exists = Callable[[Session, UUID, UUID], bool]
Listener = Callable[[Session, UUID, UUID], None]

_exists: dict[EvidenceTargetType, Exists] = {}
_listeners: dict[EvidenceTargetType, list[Listener]] = {}


def register(target_type: EvidenceTargetType, exists: Exists, on_evidence_changed: Listener | None = None) -> None:
    _exists[target_type] = exists
    if on_evidence_changed is not None:
        listeners = _listeners.setdefault(target_type, [])
        if on_evidence_changed not in listeners:
            listeners.append(on_evidence_changed)


def require(session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID) -> None:
    check = _exists.get(target_type)
    if check is None or not check(session, project_id, target_id):
        raise NotFoundError(f"{target_type.value.lower()} not found in this project", target_id=str(target_id))


def evidence_changed(session: Session, project_id: UUID, target_type: EvidenceTargetType, target_id: UUID) -> None:
    for listener in _listeners.get(target_type, []):
        listener(session, project_id, target_id)
