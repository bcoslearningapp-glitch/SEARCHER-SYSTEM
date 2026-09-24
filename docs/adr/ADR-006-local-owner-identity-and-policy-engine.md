# ADR-006: Local-owner identity and a code-registered Policy Engine
Status: Accepted
Date: 2026-09-24

Context:
PRD §62 lets v1 run in single-user mode but forbids hard-coding a single actor; every approval, decision and audit record must identify its actor and role. PRD §49 and Core §57 require action authorization (AUTONOMOUS / ACT_AND_NOTIFY / REQUEST_APPROVAL / FORBIDDEN) to live in code/configuration, not prompts. PRD §81 requires ADRs for the authentication mechanism and the policy-engine approach.

Decision:
Identity
- A `Principal` (kind HUMAN/AI/SYSTEM, id, set of roles) is resolved server-side for every request by the `current_principal` dependency. Clients never assert roles.
- v1 runs in local single-owner mode: every HTTP request acts as the configured local owner (`LOCAL_OWNER_ID`), who holds all four human roles by default (`LOCAL_OWNER_ROLES`). The API binds to 127.0.0.1 in compose.
- AI principals are constructed only by internal orchestration code, never from HTTP input. System principals identify internal components (worker, workflow automation).
- Audit records store the single role under which an action was performed (`Principal.as_actor(role)`).
- Multi-user authentication (accounts, sessions/tokens) is deferred; replacing `current_principal` is the only integration point.

Policy Engine
- `governance_audit.policy.POLICIES` registers every mutating action with: the AI authorization class, the human roles allowed, whether system components may perform it, and whether it is a human-only approval.
- Unregistered actions are denied for everyone.
- Human-only approval actions (Problem Frame approval, decision resolution, closing/reopening, reverification, foundational source adoption) are never executable by AI, regardless of class.
- `REQUEST_APPROVAL` actions are not executed for AI principals; the caller must route them to a human.
- Domain services call `authorized(principal, action)` themselves, so a router cannot forget a check.
- Methodology rules that depend on state (e.g. the Framing Gate, "ACTIVE_RESEARCH requires an approved frame") are enforced in the owning module's service and, where they protect history, by database triggers.

Alternatives considered:
- Rule engines (OPA/Cedar): powerful but adds a runtime and a policy language before the rule set is large; revisit if policies become data-driven per project.
- Trusting a role header from the web app: violates server-side enforcement (FR-AI-TOOL-004).

Consequences:
- Adding a mutation requires registering its action; tests assert AI cannot perform approval actions.
- Single-owner mode must not be exposed beyond localhost without adding real authentication.

Research Core impact: Implements Core §57-58 (AI action authority; approvals explicit and human) in code.

Migration impact: None.
