# Test coverage map (PRD §73)

This maps each testing requirement in PRD §73 to where it is verified. Backend paths are relative to `services/api/tests/`. E2E specs are in `tests/e2e/specs/`. Everything here runs in normal CI with mocks. Live providers run only in the protected provider-contract workflow.

## Unit tests

| Requirement | Tests |
|---|---|
| State transitions | `unit/test_lifecycle_and_gate.py`, `unit/test_hypothesis_lifecycle.py`, `unit/test_experiment_rules.py`, `unit/test_knowledge_rules.py` |
| Policy rules | `unit/test_policy.py`, `unit/test_ai_tool_registry.py`, `unit/test_architecture.py` |
| Quality gates | `unit/test_lifecycle_and_gate.py` (Framing), `unit/test_design_gate.py`, `unit/test_closure_gate.py`, `unit/test_experiment_rules.py`, `unit/test_knowledge_rules.py` |
| Source identity | `unit/test_source_rules.py`, `unit/test_storage.py` |
| Import/export, trust preservation | `integration/test_portability.py` (real round trip into a second database) |
| Reference enums/rules | `unit/test_quran_dataset.py`, `integration/test_reference.py` |
| Quotation protection | `integration/test_outputs.py`, `integration/test_integrity.py`, `integration/test_office_export.py` |

## Integration tests

| Requirement | Tests |
|---|---|
| Database persistence | every `integration/test_*.py`; append-only and protect triggers in `test_audit.py`, `test_cloud_workspace.py`, `test_ai_gateway.py` and others |
| Migrations | `integration/test_migrations.py`, plus the CI `migration-check` job (upgrade, downgrade, `alembic check`) |
| Source ingestion | `integration/test_sources.py` |
| Provider adapters with mocks | `integration/test_ai_gateway.py`, `integration/test_orchestrator.py`, `integration/test_m3_exit.py` |
| Search adapter | `integration/test_research_planning.py` |
| Background workers | `integration/test_health_and_jobs.py`, `integration/test_orchestrator.py` |
| Export/import round trips | `integration/test_portability.py` |

## Contract tests

The reusable checks are in `tests/adapter_contracts.py`. Any implementation of an interface must pass them.

| Interface | Offline (CI) | Live |
|---|---|---|
| Anthropic adapter | `unit/test_adapter_contracts.py`, `unit/test_anthropic_web_search.py` | `provider_contract/test_live_providers.py` |
| OpenAI adapter | `unit/test_adapter_contracts.py` (declares no web search; refuses as unavailable) | `provider_contract/test_live_providers.py` |
| SearchProvider (`AIProvider.web_search`, ADR-012) | `unit/test_adapter_contracts.py` (mock, Anthropic offline, OpenAI, outage) | `provider_contract/test_live_providers.py` |
| CloudWorkspaceAdapter (ADR-023) | `unit/test_adapter_contracts.py` (`local-directory`) | a concrete provider adapter must pass the same check |
| Research Core package schema | `scripts/contracts/check_contracts.py` (CI `contract-check`); `integration/test_portability.py` validates manifests | — |

## End-to-end flows

| PRD §73 flow | Spec |
|---|---|
| 1. Create project → framing → approve Problem Frame | `phase1.spec.ts` "1." |
| 2. Add digital source → extract → cite | `phase1.spec.ts` "2." |
| 3. Physical metadata-only source → Hybrid Access | `phase1.spec.ts` "3." |
| 4. Hypothesis → evidence support/challenge | `phase2.spec.ts` "4." |
| 5. Reference review → reservation → human decision | `phase2.spec.ts` "5." |
| 6. Design → experiment → learning review | `phase4.spec.ts` "6." |
| 7. Generate referenced output | `phase5.spec.ts` "7." (Markdown, HTML, DOCX, PDF) |
| 8. Export project → import → trust preserved | `phase5.spec.ts` "8." covers export and the import guard in the UI. The full import into an empty installation, which checks trust preservation, runs in `integration/test_portability.py` against a second, freshly migrated database. An E2E import would need a second installation. |
| 9. Provider outage → project remains usable | `phase3.spec.ts` "9." |
| 10. Reopen closed project | `phase4.spec.ts` "10." |

Additional E2E coverage:
- the foundational library;
- research plans and search;
- the AI reliability registry;
- design, experiments and terminology;
- outputs and the cloud workspace;
- platform smoke tests, including RTL, unknown locale and unknown project.

## Frontend states (DoD §77.3)

- **Loading:** `app/[locale]/loading.tsx` shows a localised status while any page streams.
- **Error:** `app/[locale]/error.tsx` shows a localised alert with a retry. A page's main record is loaded with `loadEntity`:
  - a missing record is a not-found page;
  - a service failure reaches the error boundary, so an outage never looks like "not found".
- **Empty:** every list card renders an explicit empty message (`Empty`).
- **Success:** action forms show the result of the action (`ActionForm`).
- Secondary data that fails to load degrades to an empty or partial view, and the desk shows `LoadError`.

## Evaluation tests

Golden research fixtures are kept separate from software tests. See `docs/evaluation/QUALITY_GATES.md` and #56.
