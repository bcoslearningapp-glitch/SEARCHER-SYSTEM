# ADR-013: Controlled AI tool registry
Status: Accepted
Date: 2026-09-24

Context:
PRD §47 forbids giving AI providers database credentials or filesystem access (FR-AI-TOOL-001/002). All AI interaction must go through registered tools (FR-AI-TOOL-003) that enforce project permissions and sensitivity server-side (FR-AI-TOOL-004). Changes to approved state must pass the Policy Engine and approval logic (FR-AI-TOOL-005). §53 asks for tool outputs to be recorded for reproducibility, and QUALITY_GATES requires zero executed forbidden tool calls.

Decision:
- `modules/ai_tools` holds a registry of named tools. Each tool has a kind:
  - READ: project data; source text is flagged untrusted.
  - PROPOSE: reviewable records created through domain services.
  - EXTERNAL: web search through the AI gateway.
- Each tool also has a closed JSON Schema for its input and a handler. Registration rejects open schemas and any schema with a `project_id`.
- `ToolContext` is built by the application, never by a model. It carries the project, the AI principal, the sensitivity level, the requesting human, the task's allow-list, the job, the model profile, and the `AIActionRecord` of the model step whose output is being acted on. Handlers take the project only from the context.
- `invoke` checks, in order:
  1. the tool exists;
  2. the tool is on the task's allow-list;
  3. PROPOSE tools have model provenance;
  4. the arguments match the schema;
  5. the handler runs under the Policy Engine, and domain services apply project scoping (objects from other projects are "not found") and state rules.
- Proposals land only as DRAFT (frames), PROPOSED (claims), UNCONFIRMED (assumptions), CANDIDATE (evidence, with quote text copied server-side from the page span) or SIGNAL (hypotheses). No tool approves, assesses or judges.
- Every call is written to the append-only `ai_tool_calls` log in its own transaction, refused and failed calls included. Each record holds the tool, kind, status (OK / DENIED / INVALID / ERROR), reason, arguments, output entity ids, a SHA-256 of the output, the job and the AI request id. Full source text is not stored.
- The Research Orchestrator acts only through the registry. Each task declares its allow-list:
  - `draft_problem_frame`: get_project_state, draft_problem_frame
  - `detect_assumptions`: get_project_state, propose_assumption
  - `challenge`: search_sources, read_passages, propose_evidence, propose_hypothesis
  - `web_search`: search_external_web
- Application bookkeeping stays with the application: track runs, and the context it assembles for prompts.
- Tool definitions are provider-neutral (`GET /api/v1/ai/tools`). A later model-driven tool loop will map them to each provider's tool-use format and send every requested call through `invoke`. The model's choice never bypasses these checks.

Not yet registered, because their domains don't exist yet: `get_reference_source` (beyond Qur'an/Hadith), `search_prior_projects` (Phase 4 memory), `propose_event`.

Consequences:
- A model cannot read another project, call an unlisted tool, or write anything that isn't a reviewable proposal, whatever its prompt contains.
- The tool log plus `ai_requests` reconstruct what each AI step saw and did.
