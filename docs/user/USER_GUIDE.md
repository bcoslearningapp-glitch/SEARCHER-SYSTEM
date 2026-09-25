# User guide

This guide follows a research project from the first idea to an approved, exportable output. The interface is available in English (`/en`), French (`/fr`) and Arabic (`/ar`, right to left). To install and start the product, see the README's **Run locally** section. Backups are covered in [`docs/operations/BACKUP_RESTORE.md`](../operations/BACKUP_RESTORE.md).

Three rules hold everywhere:
- **The AI proposes and you decide.** Nothing the AI produces becomes canonical until you accept or approve it. Approvals are always a person's act.
- **The project state is the memory.** Conversations are not.
- **Every change is audited.** Records you approved are versioned, never silently overwritten.

## 1. Start a project (Desk)

1. On the home page, create a project from an idea, a problem or a question.
2. The **Desk** shows:
   - the current question and project status;
   - the research mode;
   - decisions waiting for you;
   - the **attention queue** (what needs a person next);
   - notes.
3. Draft the **Problem Frame**. The Framing Gate lists what is missing. With a model configured, *Draft with AI* proposes a frame.
4. **Approve** the frame. That is an explicit approval with a reason, and it moves the project into active research.

Capture notes freely. A note becomes a claim, an assumption or a question only when you capture it as one.

## 2. Build the library (Library and project Sources)

- **Catalog** a work and its edition, then upload a file (PDF, text, EPUB or image). Uploads are checked by content, not by file name. Text is extracted page by page in the background.
- **Physical, restricted or metadata-only sources:** catalog them anyway and open a **Hybrid Source Access** request. Record the exact excerpt, a summary or a photo when you consult the source.
- **Search** covers the whole local library, with page anchors. When semantic search is enabled (ADR-025), it also finds passages by meaning, across Arabic, French and English. The results say which kind of search ran.
- **Foundational library.** Qur'an text is never bundled or generated. A Constitutional Authority imports and approves a published dataset (see the README).

## 3. Claims, evidence and hypotheses (Lab and Map)

- **Claims:** give each a statement and a type.
- **Evidence** links an exact excerpt to a claim or hypothesis, as support, contradiction, limitation or qualification. Candidate evidence stays a candidate until you assess it.
- **Exact quotes** are copied from verified page spans and cannot be edited.
- **Hypotheses** have immutable versions. New evidence can downgrade a hypothesis automatically; nothing upgrades it silently.
- **Challenge this** (AI, optional) searches for counter-evidence and alternative explanations. Results are proposals.
- The **Map** shows the central problem, hypotheses, open questions, decisions and blockers.

## 4. Research plans (Research)

A plan covers the support, challenge and alternative-explanation tracks.
- Searches run against the local library first. If a model is configured and the project's disclosure policy allows it, they can also use web search.
- Web results become **source leads**, never evidence.
- You decide sufficiency. It cannot be declared until the counter-evidence tracks have been searched.

## 5. Reference review

On a hypothesis, open a **reference review**. It keeps separate layers: source text, interpretation, inference and judgment.
- Record a human judgment. A **blocking reservation** creates a decision you must resolve.
- The Reference Gate uses these judgments before design work can proceed.

## 6. Design and experiments (Design, Experiments)

- **Design:**
  - Write requirements traced to what they come from.
  - Propose concepts.
  - Check the Design Readiness Gate, then select a concept yourself.
- **Experiments:**
  - Write a protocol, then complete the human-impact review and get approval.
  - Run the experiment and record observations, results and interpretations. These stay distinct.
- A **learning review** closes an experiment.

## 7. Local knowledge (Knowledge)

- Promote lessons one stage at a time through the Knowledge Promotion Gate.
- Time-sensitive knowledge returns to the attention queue when it needs revalidation.
- Reuse in another project is a labelled transferability judgment, never evidence.
- The **Terminology** page holds approved canonical terms, and a translation check flags claim-strength drift between languages.

## 8. Outputs (Outputs)

1. **Compose** an output (report, dossier, evidence map and others) in a language and a mode:
   - READABLE;
   - REFERENCED, with labels and references;
   - AUDIT, with a trace for every claim.
2. **Run integrity checks.** Eight steps verify claims, citations, exact quotes, reference layers, terminology, translation, edits and rendering.
   - A FAILED version cannot be approved.
   - Warnings need your acknowledgement.
3. **Approve** the version.
4. **Download** it as Markdown, HTML, DOCX or PDF. Quotes are verbatim, and each PDF carries `quotes.json` with the exact quote texts.

## 9. Share and move work

- **Export package** (project header) produces a checksummed Research Core Package.
- **Import** it on another installation from the home page. Import never raises trust: foundational texts arrive staged, and withheld files become metadata-only.
- **Workspace** (optional, when configured) stages selected records in a remote workspace. Your project's disclosure policy is checked first, and every attempt is kept in the disclosure manifest.

## 10. AI settings and reliability

- **Project AI policy** (Desk): set cloud consent, the allowed model profiles and budgets. Confidential projects need explicit consent; restricted projects never send content to cloud AI.
- **AI reliability** (Desk link): shows observed provider behaviour, evaluation standings against the approved thresholds, and the **installation audit** (exact quotes, Qur'an/Hadith integrity, layer separation, tool authorization).
- **If a provider is down:** AI tasks fail visibly and everything else keeps working. No project data depends on a provider.

## 11. Close and reopen

- **Close** a project through the Project Closure Gate. Blocking decisions, unfinished experiments, unassessed evidence and the closure record are all checked.
- **Reopen** it with a trigger. The closure record is kept.
