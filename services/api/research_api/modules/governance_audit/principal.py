"""Who is acting. Resolved server-side; clients never assert their own roles (PRD §62, ADR-006)."""

from __future__ import annotations

from dataclasses import dataclass, field

from research_api.config import get_settings
from research_api.contracts.enums import ActorKind, ActorRole
from research_api.modules.governance_audit.schemas import Actor


@dataclass(frozen=True)
class Principal:
    kind: ActorKind
    id: str
    roles: frozenset[ActorRole] = field(default_factory=frozenset)
    display_name: str | None = None

    def as_actor(self, role: ActorRole | None = None) -> Actor:
        """The audit-facing actor, recording the role the action was performed under."""
        if role is not None and role not in self.roles:
            raise ValueError(f"principal {self.id} does not hold role {role}")
        return Actor(kind=self.kind, id=self.id, role=role)


def local_owner() -> Principal:
    settings = get_settings()
    return Principal(
        kind=ActorKind.HUMAN,
        id=settings.local_owner_id,
        roles=frozenset(ActorRole(r) for r in settings.local_owner_roles),
        display_name=settings.local_owner_display_name,
    )


def current_principal() -> Principal:
    """FastAPI dependency. v1 single-owner mode: every HTTP request acts as the local owner.

    AI principals are never created from HTTP input; the Research Orchestrator
    constructs them internally (Phase 3).
    """
    return local_owner()


def system_principal(component: str) -> Principal:
    return Principal(kind=ActorKind.SYSTEM, id=component, roles=frozenset({ActorRole.SYSTEM}))


def ai_principal(component: str) -> Principal:
    return Principal(kind=ActorKind.AI, id=component, roles=frozenset())
