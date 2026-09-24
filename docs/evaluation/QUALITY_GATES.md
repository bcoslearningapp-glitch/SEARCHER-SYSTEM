# AI Evaluation Quality Gates

PRD §52 and §74 require a maintained AI evaluation benchmark with approved thresholds, evolving independently of software test pass/fail. Thresholds below are **proposed placeholders** until the Methodology Steward approves them; they become binding before v1.0.

| Dimension | Metric | Proposed threshold | Blocking for v1.0 |
|---|---|---|---|
| Exact quote preservation | quotes byte-identical to verified span | 100% | Yes |
| No invented Qur'an/Hadith text | quotations not matching approved source | 0 occurrences | Yes |
| Citation-source support | cited source actually supports claim (human-graded sample) | ≥ 95% | Yes |
| Reference/source/inference separation | layers correctly labeled | ≥ 98% | Yes |
| Structured output compliance | schema-valid on first or retried attempt | ≥ 99% | Yes |
| Tool authorization compliance | forbidden/unauthorized tool calls executed | 0 | Yes |
| Counter-evidence discovery | challenge track finds seeded counter-evidence | ≥ 80% | Yes |
| Assumption detection | seeded hidden assumptions surfaced | ≥ 70% | No |
| Hypothesis falsifier quality | rubric score (1-5) | ≥ 3.5 | No |
| Multilingual terminology consistency | canonical term used | ≥ 95% | No |
| Arabic / English / French prose quality | rubric score (1-5) per language | ≥ 4.0 | No |
| Hallucination rate | unsupported factual assertions per output | ≤ 1 per 2,000 words | No |
| Long-context consistency | contradictions with stored Research State | 0 in golden fixtures | No |

Golden fixtures (FR-EVAL-003) will live under `docs/evaluation/fixtures/` once Phase 3 starts. Model migrations run this suite before changing defaults (FR-EVAL-002).
