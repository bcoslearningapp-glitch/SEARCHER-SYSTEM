# ADR-010: AI gateway — provider adapters, model profiles, disclosure log and budgets
Status: Accepted
Date: 2026-09-24

Context:
PRD §46-54 and §64 require provider-neutral AI access (Anthropic and OpenAI at minimum), configurable models, sensitivity-based disclosure rules, a disclosure record for each outbound request (FR-DATA-001), redaction/context minimisation (FR-DATA-002), usage/cost recording (FR-COST-001), and budget exhaustion ending as `STOPPED_RESOURCE_CONSTRAINT` (FR-COST-003). CLAUDE.md forbids provider SDK calls outside adapters, raw provider output mutating canonical state, and live provider calls in normal CI. Source text is prompt-injection-capable untrusted data.

Decision:
Interface and adapters
- `modules/ai_gateway/base.py` defines a provider-neutral `AIProvider` (`generate_structured`, `healthcheck`, `capabilities`), `StructuredRequest` (task, template version, instructions, labelled sections, JSON Schema), `StructuredResult` and a provider-error hierarchy (unavailable / refusal / invalid output). Only `anthropic_adapter.py` and `openai_adapter.py` import provider SDKs; the architecture test enforces this.
- Anthropic adapter: Messages API with adaptive thinking, `output_config` JSON-Schema structured output and effort. It opts in to server-side refusal fallback (`server-side-fallback-2026-07-01` beta, `fallbacks="default"`) and records whether a fallback model served the response. A refusal raises `ProviderRefusalError`; `max_tokens` truncation raises `ProviderOutputError`.
- OpenAI adapter: Chat Completions with strict `json_schema` response format and mapped reasoning effort.
- A deterministic `mock` provider exists for CI, E2E and demos. It is listed only when `AI_MOCK_ENABLED=true` and is treated as local (no external disclosure).

Prompting
- Instructions go only to the system prompt, followed by grounding rules (no quoting of Qur'an, Hadith or any source from memory) and an untrusted-data notice.
- Context is rendered as labelled sections. Retrieved sources and tool output are wrapped in `<untrusted_source>` with the content HTML-escaped so that it cannot close the wrapper or forge other sections. Secrets are redacted from all outbound text.

Profiles
- A profile is provider + model + effort + max output + prices. Model ids and prices are configuration (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `*_USD_PER_MTOK`), not product logic. Default: `anthropic-default` (`claude-opus-5`). A profile without a key is listed as unconfigured and fails as `provider_unavailable`; the product stays usable without cloud AI.

Policy, disclosure and budgets
- `project_ai_policies` (human-only action `ai_policy.update`, audited): cloud consent, allowed profiles, preferred profile, per-project and per-task budgets. No row means no consent and no budget.
- Disclosure follows PRD §54: PUBLIC/NORMAL allowed; CONFIDENTIAL needs explicit consent; RESTRICTED/CRITICAL never go to cloud providers; local providers are always allowed.
- Before a call, the worst-case cost (≈3 characters per token for input plus the full output cap) is checked against the per-task budget and against the project's remaining budget. If either is exceeded, the call is refused with `stopped_resource_constraint`.
- `ai_requests` is an append-only log (DB trigger) of every attempted call: project, task, template version, profile/provider/model, status (SUCCEEDED / FAILED / BLOCKED), error kind, disclosure reason, sensitivity, supplied entity ids, outbound characters, tokens, estimated cost, fallback flag and provider request id. It never stores prompt text. It is written in its own transaction so blocked and failed calls stay traceable when the caller rolls back. For the same reason `project_id` is indexed but is not a foreign key.
- Output is validated against the request's JSON Schema before it is returned. `run_structured` returns an `AIActionRecord` (provider, model, template version, supplied entity ids, request id) for the caller's audit entry. The gateway itself never writes domain state.

Errors
- Provider errors map to HTTP separately from domain errors: 503 `provider_unavailable`, 422 `provider_refusal`, 502 `invalid_structured_output`. Provider response text is never echoed.

Testing
- Unit and integration tests use the mock. The live suite `tests/provider_contract` (marker `provider_contract`, excluded by default) runs only in the protected `provider-contract` workflow. It is capped by `PROVIDER_CONTRACT_MAX_REQUESTS` and checks structured output and untrusted-source isolation against both providers.

Consequences:
- Adding a provider means one adapter plus profile settings; domain code and contracts do not change.
- Cost figures are estimates from configured prices, not billing data.
- The request log grows with use. Retention and export policy come with Phase 5 portability.
