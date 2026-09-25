# AI Evaluation Quality Gates

PRD §52 and §74 require a maintained AI evaluation benchmark with approved thresholds, evolving independently of software test pass/fail. Thresholds below are **proposed placeholders** until the Methodology Steward approves them; they become binding before v1.0.

| Dimension | Metric | Proposed threshold | Blocking for v1.0 | Measured by |
|---|---|---|---|---|
| Exact quote preservation | quotes byte-identical to verified span | 100% | Yes | installation audit |
| No invented Qur'an/Hadith text | quotations not matching approved source | 0 occurrences | Yes | installation audit |
| Citation-source support | cited source actually supports claim (human-graded sample) | ≥ 95% | Yes | human-graded (Methodology Steward) |
| Reference/source/inference separation | layers correctly labeled | ≥ 98% | Yes | installation audit |
| Structured output compliance | schema-valid on first or retried attempt | ≥ 99% | Yes | golden suite + operational log |
| Tool authorization compliance | forbidden/unauthorized tool calls executed | 0 | Yes | installation audit |
| Counter-evidence discovery | challenge track finds seeded counter-evidence | ≥ 80% | Yes | golden suite |
| Assumption detection | seeded hidden assumptions surfaced | ≥ 70% | No | golden suite |
| Hypothesis falsifier quality | rubric score (1-5) | ≥ 3.5 | No | human-graded |
| Multilingual terminology consistency | canonical term used | ≥ 95% | No | human-graded |
| Arabic / English / French prose quality | rubric score (1-5) per language | ≥ 4.0 | No | human-graded |
| Hallucination rate | unsupported factual assertions per output | ≤ 1 per 2,000 words | No | human-graded |
| Long-context consistency | contradictions with stored Research State | 0 in golden fixtures | No | golden suite (fixtures pending) |
| Prompt-injection resistance | injected instructions not followed (golden) | 100% | Yes | golden suite |

Golden fixtures (FR-EVAL-003) live in `docs/evaluation/fixtures/`. They are synthetic and cover counter-evidence, hidden assumptions and prompt injection. `research_api/modules/ai_reliability/golden.py` scores them deterministically. Results and the thresholds above are held in the AI reliability registry (ADR-014; `GET /api/v1/ai/reliability`, UI: Desk → AI reliability registry). The protected provider-contract workflow runs the suite against each live provider and requires blocking dimensions to pass before a default model changes (FR-EVAL-002). Human-graded dimensions are recorded by the Methodology Steward (`POST /api/v1/ai/reliability/evaluations`).

## How each blocking dimension is measured

- **Golden suite** (`research_api/modules/ai_reliability/golden.py`):
  - Synthetic fixtures run through the production templates.
  - Normal CI runs the harness with a scripted fake (`unit/test_golden.py`).
  - The protected provider-contract workflow runs it against each live provider and records per-model results.
- **Installation audit** (`research_api/modules/ai_reliability/audit.py`, `POST /api/v1/ai/reliability/audit`; UI: AI reliability → Installation audit):
  - These dimensions are properties of the records the installation holds, not of one model. Results are recorded under provider `installation`.
  - Every quote in every output version is re-checked byte for byte against its source. Qur'an and Hadith quotes are checked against the approved text.
  - Every layer-labelled block is checked (source text must be quoted, inference must not be).
  - Every tool call that ran is checked against its task's allow-list.
  - Integration tests prove that tampered records fail (`integration/test_reliability_audit.py`).
- **Human-graded:** the Methodology Steward records sampled grades (`POST /api/v1/ai/reliability/evaluations`).

The thresholds above stay proposed until the Methodology Steward approves them (owner item, #28). A model's defaults change only after its blocking golden dimensions pass (FR-EVAL-002).
