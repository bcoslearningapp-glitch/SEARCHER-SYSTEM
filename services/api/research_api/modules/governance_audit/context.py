"""Per-operation context passed to domain services: who acts, authorized for what."""

from __future__ import annotations

from dataclasses import dataclass

from research_api.modules.governance_audit.policy import PolicyDecision, authorize
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import Actor, AIActionRecord


@dataclass(frozen=True)
class Authorized:
    """Proof that `principal` passed policy for `action`. Services require one per mutation."""

    principal: Principal
    decision: PolicyDecision
    ai_action: AIActionRecord | None = None

    @property
    def actor(self) -> Actor:
        return self.principal.as_actor(self.decision.acting_role)


def authorized(principal: Principal, action: str, *, ai_action: AIActionRecord | None = None) -> Authorized:
    return Authorized(principal, authorize(principal, action), ai_action)
