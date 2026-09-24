# ADR-019: Project Closure Gate
Status: Accepted
Date: 2026-09-24

Context:
PRD §41 and Core §60 name nine quality gates, and the Project Closure Gate was the last one not yet implemented. Closing a project was already a dedicated human action with an append-only closure record, and reopening kept that record (Core §66-67). But nothing checked whether the project was actually ready to close.

Decision:
- `project_workflow/closure_gate.py` is a pure, risk-aware function. It checks:
  - open blocking decisions: BLOCKED;
  - other open decisions: a reservation, or NEEDS_HUMAN_DECISION on L3/L4;
  - approved or unfinished experiments: NEEDS_HUMAN_DECISION, or BLOCKED on L4;
  - evidence candidates never assessed: a reservation;
  - a closure record without limitations: a reservation, or NEEDS_HUMAN_DECISION on L3/L4;
  - unresolved matters listed with no reopen triggers: a reservation.
- `project_workflow/closure.py` gathers these inputs through the public services of governance, claims_evidence and design_experiments. It lives outside `project_workflow.service` because those modules import that service.
  - The gate is recorded as a `PROJECT_CLOSURE` evaluation.
  - BLOCKED refuses closing. NEEDS_HUMAN_DECISION requires `acknowledge_reservations` and an `override_reason`, and is recorded as OVERRIDDEN_WITH_REASON.
  - `POST /projects/{id}/closure-readiness` previews the gate.
- **Closing is an approval.** `project_closures` gains `gate_evaluation_id` and `approval_id`. The acknowledgement and override reason are stored in the approval, not in the closure record. Closures made before this change keep NULL in both columns.
- **UI.** The Desk shows a Closure card: the close form (when READY_TO_CLOSE), the reopen form with a trigger (when CLOSED), and the closure history.

Consequences:
- All nine gates now exist.
- E2E flow 10 covers close → reopen with a trigger → the closure record survives.
