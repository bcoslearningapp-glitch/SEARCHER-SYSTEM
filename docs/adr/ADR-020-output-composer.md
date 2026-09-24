# ADR-020: Output composer, versions and protected quotes
Status: Accepted
Date: 2026-09-24

Context:
PRD §37 and Core §54-55 require the following:
- ten output types;
- READABLE, REFERENCED and AUDIT modes;
- traceability of every material claim to evidence and source (FR-OUT-004);
- exact quotes that are never mutated (FR-OUT-003);
- high-quality prose in Arabic, French and English.
CLAUDE.md adds two rules: major artifacts are versioned and never silently overwritten, and AI-generated text is not evidence.

Decision:
- **Outputs and versions.** An output (`outputs`) holds its type, title, language, mode and optional subject, where the subject is a hypothesis or an experiment. Its content lives in append-only `output_versions` of typed blocks.
  - A DB trigger keeps version content immutable. Status moves only DRAFT → APPROVED/SUPERSEDED or APPROVED → SUPERSEDED, and the approval id is stamped once.
  - Outputs cannot be deleted.
- **Block kinds**: HEADING, PARAGRAPH, CLAIM, EVIDENCE, QUOTE, LIST, NOTE.
  - Every block carries `trace` references to canonical entities.
  - A CLAIM block must have at least one trace (schema rule).
  - A QUOTE block carries a `Quote` naming its source: an EXCERPT id, a QURAN reference, or a HADITH record.
- **Deterministic composer.** The composer (`outputs_integrity/composer.py`) builds each output type from the public services of the owning modules. It does not call a model; it arranges what the project already records.
  - Evidence appears as EVIDENCE blocks.
  - A quote is added only when the excerpt is an exact, verified quote. Paraphrased or OCR text is never presented as a quotation.
  - Qur'an and Hadith quotes come from reference-review SOURCE_TEXT entries.
  - Headings are localised (en/fr/ar). Canonical content keeps its own language.
- **Changes are new drafts.** Recomposing from current state, or revising with edited blocks, appends a DRAFT and supersedes any earlier pending draft. A revision can come from a person or from the AI with provenance.
  - Every quote in a revision is re-read from its source and must match byte for byte. The block text must equal its quote.
  - Untraced claims are refused.
- **Approval is human-only.** It applies only to the latest draft and records an approval. Before approving, it re-checks the quotes and that every traced research target still exists. The previously approved version is superseded.
- **Mode** is presentation only. It decides how much label, citation and trace detail a rendering shows; the stored blocks are the same in every mode.

Consequences:
- Contracts 0.11.0 add `output.schema.json` (Output, OutputVersion, OutputBlock, Quote, Trace) and four enums.
- The eight-step integrity pipeline (#44) runs on these versions. Export (#45) renders them.
