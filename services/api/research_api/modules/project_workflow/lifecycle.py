"""Project lifecycle rules (Core §17, PRD §9). Pure functions, no persistence.

ProjectStatus and ResearchMode are independent dimensions (Core §16). Backward
movement is allowed where new knowledge requires it (Core §75).
"""

from __future__ import annotations

from research_api.contracts.enums import ProjectStatus as S

TRANSITIONS: dict[S, frozenset[S]] = {
    S.DRAFT: frozenset({S.FRAMING, S.ON_HOLD}),
    S.FRAMING: frozenset({S.ACTIVE_RESEARCH, S.ON_HOLD, S.DRAFT}),
    S.ACTIVE_RESEARCH: frozenset({S.FRAMING, S.ON_HOLD, S.FROZEN, S.READY_TO_CLOSE}),
    S.ON_HOLD: frozenset({S.DRAFT, S.FRAMING, S.ACTIVE_RESEARCH}),
    S.FROZEN: frozenset({S.ACTIVE_RESEARCH, S.ON_HOLD}),
    S.READY_TO_CLOSE: frozenset({S.ACTIVE_RESEARCH, S.CLOSED}),
    S.CLOSED: frozenset({S.REOPENED}),
    S.REOPENED: frozenset({S.FRAMING, S.ACTIVE_RESEARCH, S.ON_HOLD}),
}

# Transitions that need a dedicated, audited human action rather than the generic endpoint.
DEDICATED: dict[tuple[S, S], str] = {
    (S.READY_TO_CLOSE, S.CLOSED): "project.close",
    (S.CLOSED, S.REOPENED): "project.reopen",
}

# Entering ACTIVE_RESEARCH requires an approved baseline Problem Frame (Core §12, FR-FRAME-006).
REQUIRES_APPROVED_FRAME = frozenset({S.ACTIVE_RESEARCH})

# Statuses in which research content may be edited.
EDITABLE = frozenset({S.DRAFT, S.FRAMING, S.ACTIVE_RESEARCH, S.REOPENED})


def can_transition(current: S, target: S) -> bool:
    return target in TRANSITIONS[current]
